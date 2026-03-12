#!/bin/bash
# GAC E-Tax Server Startup Script

cd "$(dirname "$0")"

# Check if virtualenv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install requirements
pip install -q streamlit pandas pillow fpdf2

# Kill existing streamlit
pkill -f "streamlit run" 2>/dev/null

# Start with nohup (runs in background)
nohup streamlit run app.py --server.port 8501 --server.headless true > streamlit.log 2>&1 &

echo "✅ GAC E-Tax started!"
echo "Local: http://localhost:8501"
echo ""
echo "To stop: pkill -f streamlit"
