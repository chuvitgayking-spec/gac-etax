#!/bin/bash
# Cloudflare Tunnel Permanent Setup

echo "=== Cloudflare Tunnel Setup ==="

# 1. Install cloudflared
echo "1. Installing cloudflared..."
brew install cloudflared

# 2. Login to Cloudflare
echo "2. Login to Cloudflare:"
echo "   cloudflared tunnel login"

# 3. Create tunnel
echo "3. Create tunnel:"
echo "   cloudflared tunnel create gac-etax"

# 4. Get tunnel ID and create config
echo "4. Create config file at ~/.cloudflared/config.yml:"
cat > ~/.cloudflared/config.yml << 'CONFIG'
tunnel: gac-etax
credentials-file: ~/.cloudflared/gac-etax.json

ingress:
  - hostname: gac-etax.yourdomain.com
    service: http://localhost:8501
  - service: http_status:404
CONFIG

# 5. Add DNS
echo "5. Add DNS:"
echo "   cloudflared tunnel route dns gac-etax gac-etax.yourdomain.com"

# 6. Run as service
echo "6. Install as service:"
echo "   sudo cloudflared service install"

echo ""
echo "=== Alternative: Use ngrok (simpler) ==="
echo "   brew install ngrok"
echo "   ngrok http 8501"
