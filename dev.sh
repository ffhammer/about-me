#!/bin/sh
# Dev daemon in a `screen` session named "aboutme".
#   ./dev.sh start    start in background (rebuild on save + live reload on :8000)
#   ./dev.sh attach   look at the log (detach again with Ctrl-a d)
#   ./dev.sh stop     stop it
#   ./dev.sh status   is it running?
cd "$(dirname "$0")" || exit 1
NAME=aboutme

running() { screen -ls | grep -q "\.$NAME[[:space:]]"; }

case "${1:-start}" in
  start)
    if running; then echo "already running  ->  ./dev.sh attach"; exit 0; fi
    screen -dmS "$NAME" python3 dev.py
    sleep 1
    running && echo "started  ->  http://localhost:8000/   (log: ./dev.sh attach)" || echo "failed to start, try: python3 dev.py"
    ;;
  attach) screen -r "$NAME" ;;
  stop)   screen -S "$NAME" -X quit; pkill -f "[Pp]ython3* dev.py"; echo "stopped" ;;
  status) running && echo "running" || echo "not running" ;;
  *) echo "usage: ./dev.sh start|attach|stop|status"; exit 1 ;;
esac
