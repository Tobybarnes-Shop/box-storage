#!/bin/bash
# Box Storage - Start Script

cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt

# Get local IP for network access
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')

echo ""
echo "==================================="
echo "  Box Storage is running!"
echo "==================================="
echo ""
echo "  Local:   http://localhost:5000"
if [ -n "$LOCAL_IP" ]; then
echo "  Network: http://$LOCAL_IP:5000"
fi
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# Run the app
python app.py
