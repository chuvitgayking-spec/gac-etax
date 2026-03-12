#!/bin/bash
# Cloudflare Tunnel Setup for gac-dom.duckdns.org

echo "=== Cloudflare Tunnel Setup ==="

# 1. Install cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "Installing cloudflared..."
    brew install cloudflared
fi

# 2. Login (first time only)
echo "Login to Cloudflare (first time):"
echo "   cloudflared tunnel login"

# 3. Create tunnel
echo "Creating tunnel..."
cloudflared tunnel create gac-etax 2>/dev/null || echo "Tunnel may already exist"

# 4. Create config
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << 'CONFIG'
tunnel: gac-etax
credentials-file: ~/.cloudflared/gac-etax.json

ingress:
  - hostname: gac-dom.duckdns.org
    service: http://localhost:8501
  - service: http_status:404
CONFIG

# 5. Add DNS
echo "Adding DNS..."
cloudflared tunnel route dns gac-etax gac-dom.duckdns.org

# 6. Run tunnel
echo "Starting tunnel..."
cloudflared tunnel run gac-etax
