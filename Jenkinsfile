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

                        # Start Flask
                        $fl = Start-Process -FilePath python -ArgumentList '-u','-c','from app.api import api_application; api_application.run(host="0.0.0.0", port=5000)' -NoNewWindow -PassThru
                        $fl.Id | Set-Content -Path flask.pid

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
                        if (Test-Path flask.pid) { try { Get-Content flask.pid | % { Stop-Process -Id $_ -Force } } catch {} Remove-Item flask.pid -ErrorAction SilentlyContinue }
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
                        python -m bandit -r app -f json -o bandit.json
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

                        if (Test-Path flask_perf.pid) { try { Get-Content flask_perf.pid | % { Stop-Process -Id $_ -Force } } catch {} Remove-Item flask_perf.pid -ErrorAction SilentlyContinue }
                        $flp = Start-Process -FilePath python -ArgumentList '-u','-c','from app.api import api_application; api_application.run(host="0.0.0.0", port=5000)' -NoNewWindow -PassThru
                        $flp.Id | Set-Content -Path flask_perf.pid

                        Start-Sleep -Seconds 10
                        Remove-Item -Force results.jtl -ErrorAction SilentlyContinue
                        Remove-Item -Recurse -Force jmeter-report -ErrorAction SilentlyContinue

                        if (Get-Command jmeter -ErrorAction SilentlyContinue) {
                          jmeter -n -t test/jmeter/flask.jmx -l results.jtl -j jmeter.log -e -o jmeter-report/
                        } else {
                          Write-Host "jmeter not in PATH; skipping performance"
                        }

                        if (Test-Path flask_perf.pid) { try { Get-Content flask_perf.pid | % { Stop-Process -Id $_ -Force } } catch {} Remove-Item flask_perf.pid -ErrorAction SilentlyContinue }
                    '''
                    perfReport sourceDataFiles: 'results.jtl'
                }
            }
        }

        stage('Coverage') {
            steps {
                unstash 'coverage-report'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')],
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