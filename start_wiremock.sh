#!/usr/bin/env bash
set -euo pipefail
WORKDIR="$(pwd)"

# Prefer Docker container for Wiremock
if command -v docker >/dev/null 2>&1; then
  # Remove existing container if present (clean start)
  docker rm -f jenkins-wiremock >/dev/null 2>&1 || true
  docker run -d -p 9090:9090 -v "${WORKDIR}/test/wiremock":/home/wiremock --name jenkins-wiremock wiremock/wiremock:2.27.2 || true
  echo "Wiremock started in Docker (container: jenkins-wiremock)."
  exit 0
fi

# Fallback: standalone jar (requires wiremock-standalone.jar in repo)
if [ -f "${WORKDIR}/wiremock-standalone.jar" ]; then
  nohup java -jar "${WORKDIR}/wiremock-standalone.jar" --port 9090 --root-dir "${WORKDIR}/test/wiremock" >/dev/null 2>&1 &
  echo $! > "${WORKDIR}/wiremock.pid"
  echo "Wiremock started (jar) pid $(cat "${WORKDIR}/wiremock.pid")."
  exit 0
fi

echo "ERROR: Docker not found and wiremock-standalone.jar missing. Install Docker or add the jar."
exit 1