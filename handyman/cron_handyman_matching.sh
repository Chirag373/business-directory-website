#!/bin/bash

# Path to your project directory
PROJECT_DIR="/Users/oza/Desktop/Data/Tyson/business-directory-website"
VENV_DIR="$PROJECT_DIR/venv"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Go to project directory
cd "$PROJECT_DIR"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Log start time
echo "Starting handyman matching at $(date)" >> "$PROJECT_DIR/logs/cron.log"

# Run the matching command with Celery (async mode)
python manage.py match_handyman_services --async > "$PROJECT_DIR/logs/handyman_matching_$(date +%Y-%m-%d).log" 2>&1

# Log completion
echo "Handyman matching scheduled at $(date)" >> "$PROJECT_DIR/logs/cron.log"

# Deactivate virtual environment
deactivate 