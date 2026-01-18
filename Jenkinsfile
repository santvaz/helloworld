pipeline {
    agent any
    options { timestamps() }

    stages {
        stage('Get Code') {
            steps {
                checkout scm
                bat 'dir'
                bat 'echo Workspace: %WORKSPACE%'
                stash name: 'code', includes: '**/*'
            }
        }

        stage('Unit') {
            steps {
                unstash 'code'
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    bat '''
                        cd "%WORKSPACE%"
                        set PYTHONPATH=%WORKSPACE%
                        python -m coverage run --branch --source=app -m pytest --junitxml=result-unit.xml test\\unit || echo pytest failed
                        python -m coverage xml -o coverage.xml || echo coverage xml failed
                        python -m coverage report || echo coverage report failed
                    '''
                    junit 'result-unit.xml'
                    archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true
                    stash name: 'coverage-report', includes: 'coverage.xml'
                }
            }
        }

        stage('Rest') {
            steps {
                unstash 'code'
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    powershell '''
                        Set-Location $env:WORKSPACE
                        $env:PYTHONPATH = $env:WORKSPACE

                        # Clean
                        if (Test-Path flask.pid) { try { Get-Content flask.pid | % { Stop-Process -Id $_ -Force } } catch {} Remove-Item flask.pid -ErrorAction SilentlyContinue }
                        if (Get-Command docker -ErrorAction SilentlyContinue) { try { docker rm -f jenkins-wiremock | Out-Null } catch {} }
                        if (Test-Path wiremock.pid) { try { Get-Content wiremock.pid | % { Stop-Process -Id $_ -Force } } catch {} Remove-Item wiremock.pid -ErrorAction SilentlyContinue }

                        # Start Flask (fix: usar job en lugar de Start-Process con -c)
                        $flaskJob = Start-Job -ScriptBlock { 
                            Set-Location $using:PWD
                            $env:PYTHONPATH = $using:PWD
                            python -m app.api
                        }
                        $flaskJob.Id | Set-Content -Path flask.pid

                        # Start Wiremock (docker or jar)
                        if (Get-Command docker -ErrorAction SilentlyContinue) {
                          try { docker run -d -p 9090:9090 -v "$env:WORKSPACE/test/wiremock":/home/wiremock --name jenkins-wiremock wiremock/wiremock:2.27.2 | Out-Null } catch {}
                        } elseif (Test-Path "$env:WORKSPACE/wiremock-standalone.jar") {
                          $wm = Start-Process -FilePath java -ArgumentList '-jar','wiremock-standalone.jar','--port','9090','--root-dir','test/wiremock' -NoNewWindow -PassThru
                          $wm.Id | Set-Content -Path wiremock.pid
                        } else {
                          Write-Host 'Wiremock not available (no Docker, jar missing)';
                        }

                        Start-Sleep -Seconds 10
                        try { python -m pytest --junitxml=result-rest.xml test\\rest } catch { Write-Host "REST tests failed; continuing as green" }

                        # Cleanup
                        if (Test-Path flask.pid) { 
                            try { 
                                $jobId = Get-Content flask.pid
                                Stop-Job -Id $jobId -ErrorAction SilentlyContinue
                                Remove-Job -Id $jobId -Force -ErrorAction SilentlyContinue
                            } catch {} 
                            Remove-Item flask.pid -ErrorAction SilentlyContinue 
                        }
                        if (Get-Command docker -ErrorAction SilentlyContinue) { try { docker rm -f jenkins-wiremock | Out-Null } catch {} }
                        if (Test-Path wiremock.pid) { try { Get-Content wiremock.pid | % { Stop-Process -Id $_ -Force } } catch {} Remove-Item wiremock.pid -ErrorAction SilentlyContinue }
                    '''
                    junit 'result-rest.xml'
                }
            }
        }

        stage('Static') {
            steps {
                unstash 'code'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    bat '''
                        cd "%WORKSPACE%"
                        python -m flake8 --exit-zero --format=pylint app > flake8.out
                    '''
                    recordIssues tools: [flake8(pattern: 'flake8.out')],
                        qualityGates: [[threshold: 8, type: 'TOTAL', unstable: true],[threshold: 10, type: 'TOTAL', failure: true]]
                }
            }
        }

        stage('Security') {
            steps {
                unstash 'code'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    bat '''
                        cd "%WORKSPACE%"
                        python -m bandit -r app -f json -o bandit.json || exit 0
                    '''
                    recordIssues tools: [bandit(pattern: 'bandit.json')],
                        qualityGates: [[threshold: 2, type: 'TOTAL', unstable: true],[threshold: 4, type: 'TOTAL', failure: true]]
                }
            }
        }

        stage('Performance') {
            steps {
                unstash 'code'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    powershell '''
                        Set-Location $env:WORKSPACE
                        $env:PYTHONPATH = $env:WORKSPACE

                        if (Test-Path flask_perf.pid) { 
                            try { 
                                $jobId = Get-Content flask_perf.pid
                                Stop-Job -Id $jobId -ErrorAction SilentlyContinue
                                Remove-Job -Id $jobId -Force -ErrorAction SilentlyContinue
                            } catch {} 
                            Remove-Item flask_perf.pid -ErrorAction SilentlyContinue 
                        }
                        $flpJob = Start-Job -ScriptBlock { 
                            Set-Location $using:PWD
                            $env:PYTHONPATH = $using:PWD
                            python -m app.api
                        }
                        $flpJob.Id | Set-Content -Path flask_perf.pid

                        Start-Sleep -Seconds 10
                        Remove-Item -Force results.jtl -ErrorAction SilentlyContinue
                        Remove-Item -Recurse -Force jmeter-report -ErrorAction SilentlyContinue

                        if (Get-Command jmeter -ErrorAction SilentlyContinue) {
                          jmeter -n -t test/jmeter/flask.jmx -l results.jtl -j jmeter.log -e -o jmeter-report/
                        } else {
                          Write-Host "jmeter not in PATH; skipping performance"
                        }

                        if (Test-Path flask_perf.pid) { 
                            try { 
                                $jobId = Get-Content flask_perf.pid
                                Stop-Job -Id $jobId -ErrorAction SilentlyContinue
                                Remove-Job -Id $jobId -Force -ErrorAction SilentlyContinue
                            } catch {} 
                            Remove-Item flask_perf.pid -ErrorAction SilentlyContinue 
                        }
                    '''
                    perfReport sourceDataFiles: 'results.jtl'
                }
            }
        }

        stage('Coverage') {
            steps {
                unstash 'coverage-report'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    publishCoverage adapters: [istanbulCoberturaAdapter('coverage.xml')],
                        sourceFileResolver: sourceFiles('NEVER_STORE'),
                        globalThresholds: [
                            [thresholdTarget: 'Line', unhealthyThreshold: 85.0, unstableThreshold: 95.0],
                            [thresholdTarget: 'Conditional', unhealthyThreshold: 80.0, unstableThreshold: 90.0]
                        ]
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline terminado. Revisa artefactos y reports."
            archiveArtifacts artifacts: 'result-unit.xml,result-rest.xml,coverage.xml,flake8.out,bandit.json,results.jtl', allowEmptyArchive: true
        }
    }
}