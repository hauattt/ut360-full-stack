#!/bin/bash

# Setup script for Phase 1 environment
# This script installs necessary Python packages

echo "================================"
echo "Setting up Phase 1 environment"
echo "================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Installing system packages..."
    apt-get update
    apt-get install -y python3-pip python3-dev
else
    echo "Note: Running without root privileges"
    echo "If pip is not available, run with sudo: sudo bash setup_environment.sh"
fi

# Install Python packages
echo ""
echo "Installing Python packages..."

if command -v pip3 &> /dev/null; then
    pip3 install --user pandas numpy pyarrow matplotlib seaborn scipy
    echo "✓ Python packages installed successfully"
else
    echo "ERROR: pip3 is not available"
    echo "Please install pip first:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install python3-pip"
    exit 1
fi

echo ""
echo "================================"
echo "Setup completed!"
echo "================================"
echo ""
echo "You can now run:"
echo "  python3 01_data_loading.py"
echo "  python3 02_eda_analysis.py"
