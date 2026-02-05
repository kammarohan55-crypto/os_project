#!/bin/bash
# setup.sh - Automated environment setup for OS Sandbox project

set -e  # Exit on error

echo "==========================================="
echo "OS Sandbox - Environment Setup"
echo "==========================================="
echo

# Check if running on Linux/WSL
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script requires Linux or WSL"
    echo "   Please run in WSL (Windows Subsystem for Linux) or native Linux"
    exit 1
fi

echo "📦 Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y \
    gcc \
    make \
    libseccomp-dev \
    python3 \
    python3-pip \
    python3-venv

echo
echo "🐍 Installing Python dependencies..."
pip3 install -q flask pandas numpy scikit-learn

echo
echo "🔨 Building runner/launcher..."
make clean
make

# Ensure launcher is executable
chmod +x runner/launcher
echo "✅ runner/launcher is now executable"

echo
echo "🧪 Building test programs..."
cd test_programs
make clean 2>/dev/null || true
make
chmod +x *
cd ..

echo
echo "📁 Creating logs directory..."
mkdir -p logs

echo
echo "==========================================="
echo "✅ Setup Complete!"
echo "==========================================="
echo
echo "Next steps:"
echo "1. Run tests: python3 run_all_tests.py"
echo "2. Start dashboard: python3 dashboard/app.py"
echo "3. Open browser: http://localhost:5000"
echo
