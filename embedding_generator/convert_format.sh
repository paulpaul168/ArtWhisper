#!/bin/bash
# Check if Python virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

tensorflowjs_converter --input_format keras art_feature_extractor.h5 tfjs_model