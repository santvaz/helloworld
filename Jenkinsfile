pipeline {
    agent any
    options { timestamps() }

    stages {
        stage('Get Code') {
            steps {
                // Checkout repo where this Jenkinsfile lives (Jenkins will automatically checkout the pipeline too)
                checkout scm
                sh 'ls -la'
                sh 'echo "Workspace: ${WORKSPACE}"'
                // stash source for other stages if needed
                stash name: 'code', includes: '**/*'
            }
        }

        stage('Unit') {
            steps {
                unstash 'code'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        cd "${WORKSPACE}"
                        export PYTHONPATH="${WORKSPACE}"
                        # Ejecuta las pruebas unitarias UNA vez y genera coverage.xml
                        python3 -m coverage run --branch --source=app -m pytest --junitxml=result-unit.xml test/unit || true
                        python3 -m coverage xml -o coverage.xml || true
                        python3 -m coverage report || true
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
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        cd "${WORKSPACE}"
                        export PYTHONPATH="${WORKSPACE}"

                        # Ensure old processes are stopped
                        ./stop_wiremock.sh || true
                        ./stop_flask.sh || true

                        # Start Flask in background (app/api.py)
                        python -u -c "from app.api import api_application; api_application.run(host='0.0.0.0', port=5000)" &
                        echo $! > flask.pid

                        # Start Wiremock via Docker if available, else fall back to script
                        if command -v docker >/dev/null 2>&1; then
                          docker run -d -p 9090:9090 -v "${WORKSPACE}/test/wiremock":/home/wiremock --name jenkins-wiremock wiremock/wiremock:2.27.2 || true
                        else
                          ./start_wiremock.sh || true
                        fi

                        # Delay to avoid race conditions (ensure services ready)
                        sleep 10

                        # Run REST integration tests
                        python3 -m pytest --junitxml=result-rest.xml test/rest || true

                        # Cleanup
                        if [ -f flask.pid ]; then kill $(cat flask.pid) || true; rm -f flask.pid; fi
                        docker rm -f jenkins-wiremock || true
                        ./stop_wiremock.sh || true
                    '''
                    junit 'result-rest.xml'
                }
            }
        }

        stage('Static') {
            steps {
                unstash 'code'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        cd "${WORKSPACE}"
                        python3 -m flake8 --exit-zero --format=pylint app > flake8.out || true
                    '''
                    recordIssues tools: [flake8(pattern: 'flake8.out')],
                        qualityGates: [
                            [threshold: 8, type: 'TOTAL', unstable: true],
                            [threshold: 10, type: 'TOTAL', failure: true]
                        ]
                }
            }
        }

        stage('Security') {
            steps {
                unstash 'code'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        cd "${WORKSPACE}"
                        python3 -m bandit -r app -f json -o bandit.json || true
                    '''
                    recordIssues tools: [bandit(pattern: 'bandit.json')],
                        qualityGates: [
                            [threshold: 2, type: 'TOTAL', unstable: true],
                            [threshold: 4, type: 'TOTAL', failure: true]
                        ]
                }
            }
        }

        stage('Performance') {
            steps {
                unstash 'code'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        cd "${WORKSPACE}"
                        export PYTHONPATH="${WORKSPACE}"

                        # Ensure clean start
                        ./stop_flask.sh || true

                        # Start Flask for performance tests
                        python -u -c "from app.api import api_application; api_application.run(host='0.0.0.0', port=5000)" &
                        echo $! > flask_perf.pid

                        # Delay to avoid race
                        sleep 10

                        # Clean previous JMeter results
                        rm -f results.jtl || true
                        rm -rf jmeter-report || true

                        # Run JMeter (assume jmeter in PATH)
                        if command -v jmeter >/dev/null 2>&1; then
                          jmeter -n -t test/jmeter/flask.jmx -l results.jtl -j jmeter.log -e -o jmeter-report/ || true
                        else
                          echo "jmeter not found; skipping performance stage"
                        fi

                        # Cleanup Flask started for perf
                        if [ -f flask_perf.pid ]; then kill $(cat flask_perf.pid) || true; rm -f flask_perf.pid; fi
                    '''
                    perfReport sourceDataFiles: 'results.jtl'
                }
            }
        }

        stage('Coverage') {
            steps {
                unstash 'coverage-report'
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        cd "${WORKSPACE}"
                        if [ -f coverage.xml ]; then
                            python3 - <<PY
import xml.etree.ElementTree as ET
try:
    r = ET.parse('coverage.xml').getroot()
    lines = float(r.get('line-rate',0)) * 100
    branches = float(r.get('branch-rate',0)) * 100
    print(f"LINE_COVERAGE={lines:.2f}")
    print(f"BRANCH_COVERAGE={branches:.2f}")
except Exception:
    print("LINE_COVERAGE=0")
    print("BRANCH_COVERAGE=0")
PY
                        else
                            echo "coverage.xml not found"
                        fi
                    '''
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                        sourceFileResolver: sourceFiles('NEVER_STORE'),
                        globalThresholds: [
                            [thresholdTarget: 'Line', unhealthyThreshold: 85.0, unstableThreshold: 95.0],
                            [thresholdTarget: 'Conditional', unhealthyThreshold: 80.0, unstableThreshold: 90.0]
                        ]
                }
            }
        }
    } // stages

    post {
        always {
            echo "Pipeline terminado. Revisa artefactos y reports."
            archiveArtifacts artifacts: 'result-unit.xml,result-rest.xml,coverage.xml,flake8.out,bandit.json,results.jtl', allowEmptyArchive: true
        }
    }
}