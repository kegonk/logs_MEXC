#!/bin/bash

# MEXC Scalper Logger Startup Script
echo "🎯 Starting MEXC Scalper Logger..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install websocket-client requests
else
    echo "✅ Virtual environment found"
    source venv/bin/activate
fi

# Check config file
if [ ! -f "config.json" ]; then
    echo "❌ config.json not found!"
    echo "Please create config.json with your MEXC API credentials"
    exit 1
fi

echo "✅ Configuration found"
echo "🚀 Starting logger..."
echo "👨‍💻 Open MetaScalp and start trading"
echo "🛑 Press Ctrl+C to stop logging"
echo ""

# Start the logger
python mexc_working_logger.py