#!/bin/bash
# Cloudflare Tunnel Setup for GAC E-Tax

echo "=== Cloudflare Tunnel Setup ==="

# 1. Install cloudflared
echo "1. Installing cloudflared..."
brew install cloudflared

# 2. Login to Cloudflare
echo "2. Login to Cloudflare:"
echo "   Run: cloudflared tunnel login"

# 3. Create tunnel
echo "3. Create tunnel:"
echo "   Run: cloudflared tunnel create gac-etax"

# 4. Add DNS
echo "4. Add DNS (replace TUNNEL_ID):"
echo "   cloudflared tunnel route dns gac-etax gac-etax.yourdomain.com"

# 5. Run tunnel
echo "5. Run tunnel (temporary):"
echo "   cloudflared tunnel --url http://localhost:8501"

echo ""
echo "=== OR use simplest method (ngrok): ==="
echo "   brew install ngrok"
echo "   ngrok http 8501"
