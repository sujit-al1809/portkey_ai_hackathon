#!/bin/bash
# 🚀 Quick Start Script for Linux/Mac

echo "🎯 Cost-Quality Optimization System - Quick Start"
echo "================================================"
echo ""

# Check Python
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ $PYTHON_VERSION"
else
    echo "   ❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo ""
    echo "✅ Virtual environment already exists"
fi

# Activate venv
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed"

# Check .env
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "   Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "   📝 Please edit .env and add your PORTKEY_API_KEY"
    echo "   Get your key from: https://app.portkey.ai"
    echo ""
    read -p "   Open .env in editor? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo ""
    echo "✅ .env file exists"
fi

# Test configuration
echo ""
echo "🧪 Testing Portkey configuration..."
if python tests/test_config.py > /dev/null 2>&1; then
    echo "   ✅ Configuration valid!"
else
    echo "   ⚠️  Configuration test failed"
    echo "   Please check your PORTKEY_API_KEY in .env"
fi

echo ""
echo "================================================"
echo "🎉 Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. 🧪 Run tests: python tests/simple_test.py"
echo "  2. 🚀 Run demo: python main.py"
echo "  3. ♾️  Run continuous: python continuous_mode.py"
echo ""
echo "Happy optimizing! 🎯"
echo ""
