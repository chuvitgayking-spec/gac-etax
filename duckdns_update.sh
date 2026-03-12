#!/bin/bash
# DuckDNS DDNS Update Script

# Configuration
DOMAIN="gac-etax"  # Your subdomain (without .duckdns.org)
TOKEN="YOUR_DUCKDNS_TOKEN"  # Get from https://duckdns.org

# Get current public IP
IP=$(curl -s ifconfig.me)

# Update DuckDNS
curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${IP}"

echo "Updated: $DOMAIN.duckdns.org -> $IP"
