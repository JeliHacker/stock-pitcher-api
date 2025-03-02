#!/bin/bash

PYTHON_SCRIPT="/Users/eligooch/Desktop/git/stock_pitcher_api/scraper/main.py"

LOGFILE="/Users/eligooch/Desktop/git/stock_pitcher_api/scraper/main.log"

echo "Running main.py at $(date)" >> "$LOGFILE"
python3 "$PYTHON_SCRIPT" >> "$LOGFILE" 2>&1
echo "Finished running main.py at $(date)" >> "$LOGFILE"
