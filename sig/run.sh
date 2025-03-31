#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "./venv" ]; then
    python3 -m venv venv
    source ./venv/bin/activate
    pip install -r requirements.txt
else
    source ./venv/bin/activate
fi

# Run the Makefile to process images
make