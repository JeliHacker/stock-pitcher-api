#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_SCRIPT="${STOCK_PITCHER_SCRAPER:-$SCRIPT_DIR}/main.py"
LOGFILE="${STOCK_PITCHER_SCRAPER:-$SCRIPT_DIR}/logs/main.log"

echo "Running main.py at $(date)" >> "$LOGFILE"
cd ..
echo "Running main.py from $(pwd)"
echo $(pwd)/scraper/main.py
python3 -m scraper.main >> "$LOGFILE" 2>&1
echo "Finished running main.py at $(date)" >> "$LOGFILE"
