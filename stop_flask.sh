#!/usr/bin/env bash
set +e
WORKDIR="$(pwd)"

# Stop Flask processes started by pipeline via PID files
for pidfile in "${WORKDIR}/flask.pid" "${WORKDIR}/flask_perf.pid"; do
  if [ -f "${pidfile}" ]; then
    pid="$(cat "${pidfile}" 2>/dev/null || true)"
    if [ -n "${pid}" ]; then
      kill "${pid}" >/dev/null 2>&1 || true
      echo "Killed PID ${pid} from ${pidfile}."
    fi
    rm -f "${pidfile}"
  fi
done

# Fallback: kill any running flask/app.api processes (careful on shared agents)
pkill -f "app.api" >/dev/null 2>&1 || true
pkill -f "flask" >/dev/null 2>&1 || true

echo "stop_flask completed."