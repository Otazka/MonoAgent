#!/bin/bash

# Activate virtual environment and run the split repo agent
source venv/bin/activate

# Check if --dry-run flag is provided
if [[ "$*" == *"--dry-run"* ]]; then
    echo "Running in DRY RUN mode..."
    python split_repo_agent.py --dry-run
else
    echo "Running in LIVE mode..."
    python split_repo_agent.py "$@"
fi
