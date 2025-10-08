#!/bin/bash

# Serial Communication Performance Tester Run Script

echo "Starting Serial Communication Performance Tester..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py
