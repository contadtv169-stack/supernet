#!/bin/bash
# SuperNet - Setup Script
# Stack: contadtv169-stack
# Servidor: 162.120.186.147
# Uso: ssh root@162.120.186.147 'bash -s' < setup.sh

set -e

echo "========================================"
echo " SuperNet 6.0.0 — Setup automatizado"
echo " Stack: contadtv169-stack"
echo "========================================"

echo "[1/8] Atualizando sistema..."
apt update && apt upgrade -y

echo "[2/8] Instalando dependencias..."
apt install -y curl wget git python3 python3-pip python3-venv nodejs npm nginx wireguard ufw iptables-persistent
pip3 install pyOpenSSL python-dotenv requests flask flask-cors gunicorn

echo "[3/8] Criando estrutura de diretorios..."
mkdir -p /opt/supernet/{bot,api,dpi,scripts,clientes}
mkdir -p /var/www/supernet

echo "[4/8] Clonando repositorio..."
if [ -d /opt/supernet/.git ]; then
    cd /opt/supernet && git pull origin main
else
    git clone https://github.com/KURONUZX/supernet.git /opt/supernet
fi

echo "[5/8] Configurando variaveis de ambiente..."
cat > /opt/supernet/bot/.env << 'ENVEOF'
DISCORD_TOKEN=MTUxNDI3NTU4Mjc0NDE5OTM4OA.GwmhpG.c4NXR-Y-98BY1Ez2bWBsyQCpQ0wkpSlFOqs-3g
GUILD_ID=1514275582744199388
KRYPT_CI=krypt_ci_49e0355123ad4d54fa
KRYPT_CS=krypt_cs_952dfe7561989e86e889204c1f1ab313
KRYPT_PIX=https://kryptgateway.netlify.app/api/gateway/pix-create
KRYPT_CRYPTO=https://kryptgateway.netlify.app/api/gateway/crypto-create
KRYPT_CASHOUT=https://kryptgateway.netlify.app/api/merchant/cashout
SERVER_IP=162.120.186.147
PROXY_PORT=8080
WG_PORT=51820
DNS_1=1.1.1.1
DNS_2=8.8.8.8
ENVEOF

echo "[6/8] Instalando servicos systemd..."
cat > /etc/systemd/system/supernet-dpi.service << 'SERVICEEOF'
[Unit]
Description=SuperNet DPI Bypass Proxy
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/supernet/dpi/dpi_bypass_proxy.py
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
SERVICEEOF

cat > /etc/systemd/system/supernet-api.service << 'SERVICEEOF'
[Unit]
Description=SuperNet API Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 api.server:app --chdir /opt/supernet
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
SERVICEEOF

cat > /etc/systemd/system/supernet-bot.service << 'SERVICEEOF'
[Unit]
Description=SuperNet Discord Bot
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/supernet/bot/bot.py
Restart=always
RestartSec=5
User=root
WorkingDirectory=/opt/supernet/bot

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "[7/8] Configurando firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow from 162.120.186.147/32 to any port 22
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw allow 51820/udp
ufw --force enable

echo "[8/8] Iniciando servicos..."
systemctl daemon-reload
systemctl enable --now supernet-dpi
systemctl enable --now supernet-api
systemctl enable --now supernet-bot

echo "========================================"
echo " SuperNet 6.0.0 — Setup concluido!"
echo " IP: 162.120.186.147"
echo " IPv6: 2001:4860:7:f03::97"
echo " Proxy DPI: :8080"
echo " WireGuard: :51820"
echo "========================================"
systemctl status supernet-dpi --no-pager
systemctl status supernet-api --no-pager
systemctl status supernet-bot --no-pager
