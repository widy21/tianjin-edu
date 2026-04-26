#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "Killing processes containing app.py..."
pids=$(pgrep -f "python.*app.py" || true)
for pid in $pids; do
    echo "Killing process $pid"
    kill "$pid"
done

if [ -x "$APP_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$APP_DIR/.venv/bin/python"
else
    PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

echo "Starting app.py in the background with ${PYTHON_BIN}..."
nohup "$PYTHON_BIN" app.py >> out.log 2>&1 &

echo "Script completed. Check out.log for output."
