#!/bin/bash
# Local setup script for GAC E-Tax with Thai support

echo "Setting up GAC E-Tax locally..."

# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install requirements
pip install streamlit pandas pillow reportlab fpdf2 weasyprint

# Check Thai font
if [ ! -f "assets/fonts/NotoSansThai-Regular.ttf" ]; then
    echo "Downloading Thai font..."
    mkdir -p assets/fonts
    curl -L -o assets/fonts/NotoSansThai-Regular.ttf \
        "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Thai/NotoSansThai-Regular.ttf" \
        2>/dev/null || echo "Font download may have failed"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run:"
echo "  source .venv/bin/activate"
echo "  streamlit run app.py"
echo ""
echo "Then open: http://localhost:8501"
