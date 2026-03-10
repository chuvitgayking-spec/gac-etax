#!/bin/bash
# Setup script for e-Tax Invoice System

echo "====================================="
echo "GAC e-Tax Invoice System Setup"
echo "====================================="

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create data directories
echo "📁 Creating directories..."
mkdir -p data/temp
mkdir -p data/output

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "from database import init_database; init_database()"

echo ""
echo "====================================="
echo "✅ Setup complete!"
echo "====================================="
echo ""
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py"
echo ""
echo "To access from other computers on network:"
echo "  streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
echo ""
