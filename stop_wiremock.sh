#!/usr/bin/env bash
set +e
WORKDIR="$(pwd)"

# Try to remove Docker container if exists
if command -v docker >/dev/null 2>&1; then
  docker rm -f jenkins-wiremock >/dev/null 2>&1 || true
  echo "Attempted to remove Docker container jenkins-wiremock."
fi

# If started via jar, stop process by PID file
if [ -f "${WORKDIR}/wiremock.pid" ]; then
  kill "$(cat "${WORKDIR}/wiremock.pid")" >/dev/null 2>&1 || true
  rm -f "${WORKDIR}/wiremock.pid"
  echo "Stopped Wiremock (jar) process."
fi

echo "stop_wiremock completed."