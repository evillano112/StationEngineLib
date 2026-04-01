#!/usr/bin/env bash
set -e

APP_DIR="$(pwd)"
LOG_DIR="$APP_DIR/logs"

mkdir -p "$LOG_DIR"

echo "Using app dir: $APP_DIR"

echo "Activating venv..."
source "$APP_DIR/venv/bin/activate"

echo "Building queue (72 hours)..."
python -c "from queue_eng.queue_builder import build_queue; build_queue(hours=72)"

echo "Starting Liquidsoap..."
nohup liquidsoap "$APP_DIR/radio_with_telnet.liq" \
  > "$LOG_DIR/liquidsoap.log" 2>&1 &

echo $! > "$LOG_DIR/liquidsoap.pid"

sleep 3

echo "Starting dispatcher..."
nohup python -m queue_eng.dispatcher \
  > "$LOG_DIR/dispatcher.log" 2>&1 &

echo $! > "$LOG_DIR/dispatcher.pid"

echo "===================================="
echo "Station started successfully"
echo "Liquidsoap PID: $(cat "$LOG_DIR/liquidsoap.pid")"
echo "Dispatcher PID: $(cat "$LOG_DIR/dispatcher.pid")"
echo "Logs:"
echo "  $LOG_DIR/liquidsoap.log"
echo "  $LOG_DIR/dispatcher.log"
echo "===================================="
