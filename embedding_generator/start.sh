#!/bin/bash
# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    echo "No arguments provided"
    echo "Usage: $0 <python_file>"
    exit 1
fi

# Check if Python virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

python $1