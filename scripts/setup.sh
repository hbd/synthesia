#!/bin/bash

echo "Setting up Synthesia audio-visual system..."

# Check Python version
python3 --version

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# macOS-specific setup
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS - checking for portaudio..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install from https://brew.sh"
        exit 1
    fi
    
    if ! brew list portaudio &> /dev/null; then
        echo "Installing portaudio..."
        brew install portaudio
    fi
fi

echo "Setup complete! To run:"
echo "1. source venv/bin/activate"
echo "2. python audio_visual_prototype.py"