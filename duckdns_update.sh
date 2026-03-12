#!/bin/bash
# DuckDNS DDNS Update Script

DOMAIN="gac-dom"
TOKEN="5ee2399c-39a1-4428-ab32-b81240513291"

# Get current IP
IP=$(curl -s ifconfig.me)

# Update DuckDNS
curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${IP}"

echo ""
echo "✅ Updated: gac-dom.duckdns.org -> $IP"
