#!/bin/bash
LOG="/var/log/snapatask-scrapers.log"
DATE=$(date '+%Y-%m-%d %H:%M')
echo "[$DATE] Starting daily scrapers..." >> $LOG

# Environment Agency (re-run to catch new registrations)
python3 /opt/snapatask/env-agency-scraper.py >> $LOG 2>&1
echo "[$DATE] EA scraper done" >> $LOG

# Checkatrade
python3 /opt/snapatask/checkatrade-scraper.py >> $LOG 2>&1
echo "[$DATE] Checkatrade scraper done" >> $LOG

# Gumtree contractors
python3 /opt/snapatask/lead-scraper.py >> $LOG 2>&1
echo "[$DATE] Gumtree scraper done" >> $LOG

# Run data cleaner
python3 /opt/snapatask/data-cleaner.py >> $LOG 2>&1
echo "[$DATE] Data cleaner done" >> $LOG
echo "[$DATE] All scrapers complete" >> $LOG
