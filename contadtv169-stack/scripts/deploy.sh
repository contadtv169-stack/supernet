#!/bin/bash
# SuperNet - Deploy rapido
# Uso: ./deploy.sh

VPS_IP="162.120.186.147"
VPS_USER="root"
REPO="https://github.com/KURONUZX/supernet.git"

echo "Fazendo deploy para $VPS_IP..."
ssh "$VPS_USER@$VPS_IP" << 'EOF'
    cd /opt/supernet
    git pull origin main
    pip3 install -r api/requirements.txt 2>/dev/null || true
    systemctl restart supernet-api
    systemctl restart supernet-dpi
    systemctl restart supernet-bot
    echo "Deploy concluido em $(date)"
EOF
