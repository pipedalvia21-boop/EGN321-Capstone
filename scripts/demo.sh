#!/usr/bin/env bash
# Runs the five required live demos in order. Usage: bash scripts/demo.sh
# (Windows: run the same python commands one by one in PowerShell.)
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
step(){ echo; echo "================ $1 ================"; }

step "DEMO 1 - Normal operation (valid input -> calculation -> result)"
$PY -m growvest_economics report --save

step "DEMO 2 - Original workbook verification"
$PY -m pytest -q tests/test_workbook_verification.py

step "DEMO 3 - Invalid input is refused"
$PY -m growvest_economics report --data samples/invalid_churn_percent.json; echo "exit code: $?"
$PY -m growvest_economics report --data samples/malformed.json; echo "exit code: $?"

step "DEMO 4 - Evidence: tests, history, status, log"
$PY -m pytest -q
$PY -m growvest_economics history --tier pro
$PY -m growvest_economics status
$PY -m growvest_economics log --last 5

step "DEMO 5 - Failure and recovery (database outage)"
$PY scripts/simulate_db_outage.py --seconds 6 &
sleep 1
echo "--- failure: save while the database is locked"
$PY -m growvest_economics report --save --tier pro
echo "--- detection"
$PY -m growvest_economics status
sleep 6
echo "--- recovery"
$PY -m growvest_economics recover
echo "--- verification"
$PY -m growvest_economics status
$PY -m growvest_economics history --tier pro --limit 3
$PY -m growvest_economics log --last 6
