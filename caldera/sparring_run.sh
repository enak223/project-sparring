#!/usr/bin/env bash
# sparring_run.sh - Project Sparring v0.6
# One scheduled campaign, end to end: launch -> poll -> pull -> correlate -> report.
# Sources secrets from sparring.env (gitignored). Designed to be cron-driven.
set -euo pipefail

CALDERA_DIR="/home/ubuntuai/caldera"
RUNS_DIR="$CALDERA_DIR/runs"
LOG="$CALDERA_DIR/sparring.log"
PY="$CALDERA_DIR/.venv/bin/python"
ADVERSARY="0f4c3c67-845e-49a0-927e-90ed33c044e0"   # Discovery
PLANNER="aaa7c857-37a0-4c4a-85f7-4e9f7f30e31a"     # atomic
SOURCE="ed32b9c3-9593-4c33-b0db-e2007315096b"      # basic
AGENT="ubuntu-webserver"
PLATFORM="linux"
POLL_SECS=30
MAX_POLLS=20                                        # ~10 min ceiling

source "$CALDERA_DIR/sparring.env"
mkdir -p "$RUNS_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN="$RUNS_DIR/$STAMP"
mkdir -p "$RUN"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

log "=== Sparring run $STAMP START ==="

# 1. launch operation
OP_JSON="$(curl -s -X POST -H "KEY: $CALDERA_API_KEY" -H "Content-Type: application/json" \
  "$CALDERA_URL/api/v2/operations" \
  -d "{\"name\":\"sparring-$STAMP\",\"adversary\":{\"adversary_id\":\"$ADVERSARY\"},\"planner\":{\"id\":\"$PLANNER\"},\"source\":{\"id\":\"$SOURCE\"},\"group\":\"red\",\"auto_close\":true,\"obfuscator\":\"plain-text\",\"state\":\"running\"}")"
OP_ID="$(echo "$OP_JSON" | $PY -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')"

if [ -z "$OP_ID" ]; then
  log "ERROR: no operation id returned. Response: $OP_JSON"
  exit 1
fi
log "launched operation $OP_ID"

# 2. poll until finished
STATE="running"
for i in $(seq 1 "$MAX_POLLS"); do
  sleep "$POLL_SECS"
  STATE="$(curl -s -H "KEY: $CALDERA_API_KEY" "$CALDERA_URL/api/v2/operations/$OP_ID" \
    | $PY -c 'import sys,json; print(json.load(sys.stdin).get("state",""))')"
  log "poll $i/$MAX_POLLS: state=$STATE"
  [ "$STATE" = "finished" ] && break
done

# 3. pull executed + detected
cd "$CALDERA_DIR"
$PY pull_executed.py "$OP_ID" --json "$RUN/executed.json"                    >>"$LOG" 2>&1
$PY pull_detected.py "$OP_ID" --agent "$AGENT" --json "$RUN/detected.json"   >>"$LOG" 2>&1

# 4. correlate
$PY correlate.py "$RUN/executed.json" "$RUN/detected.json" --json "$RUN/coverage.json" >>"$LOG" 2>&1

# 5. gap report (API mode)
$PY gap_report.py "$RUN/coverage.json" --api --platform "$PLATFORM" --out "$RUN/gap-report.json" >>"$LOG" 2>&1 || \
  log "WARN: gap report step failed (continuing)"

# 6. one-line summary
COV="$($PY -c 'import json;d=json.load(open("'"$RUN/coverage.json"'"));print(f"{d.get(chr(99)+chr(111)+chr(118)+chr(101)+chr(114)+chr(97)+chr(103)+chr(101),0):.0%}",len(d.get("executed",[])),len(d.get("detected",[])))' 2>/dev/null || echo "?? ? ?")"
read -r PCT NEX NDET <<< "$COV"
log "SUMMARY $STAMP: coverage=$PCT executed=$NEX detected=$NDET  -> $RUN"
log "=== Sparring run $STAMP END ==="
