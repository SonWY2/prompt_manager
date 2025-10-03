#!/bin/bash
# Linux/macOS shell script to run Prompt Manager GUI

echo "===================================================="
echo "           Prompt Manager GUI Launcher"
echo "===================================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Change to script directory
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ -f "venv/bin/activate" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Warning: No virtual environment found"
    echo "Running with system Python..."
fi

# Install GUI requirements if needed
echo "📦 Checking GUI requirements..."
pip install -q -r requirements-gui.txt
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Failed to install some GUI requirements"
fi

# Run the GUI
echo "🚀 Starting Prompt Manager GUI..."
echo
python3 run_gui.py

# Deactivate virtual environment if it was activated
if [ -f "venv/bin/activate" ]; then
    deactivate
fi

echo
echo "👋 GUI session ended."

