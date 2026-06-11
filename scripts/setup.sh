#!/bin/bash
# SuperNet 6.0.0 - Setup completo VPS
# Uso: curl -sL https://bit.ly/supernet-setup | bash
# Ou: ssh root@162.120.186.147 'bash -s' < scripts/setup.sh

set -e

GREEN='\033[0;32m'; BLUE='\033[0;34m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "${BLUE}[SuperNet]${NC} $1"; }
ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
err() { echo -e "${RED}[ERRO]${NC} $1"; }

log "Iniciando setup SuperNet 6.0.0"

log "[1/9] Atualizando sistema..."
apt update && apt upgrade -y && ok "Sistema atualizado"

log "[2/9] Instalando dependencias..."
apt install -y curl wget git python3 python3-pip python3-venv nodejs npm nginx wireguard ufw iptables-persistent net-tools
pip3 install flask flask-cors gunicorn requests python-dotenv pyOpenSSL
ok "Dependencias instaladas"

log "[3/9] Criando estrutura..."
mkdir -p /opt/supernet/{bot,api,dpi,scripts,clientes,wg}
mkdir -p /var/www/supernet
ok "Estrutura criada"

log "[4/9] Clonando repositorio..."
if [ -d /opt/supernet/.git ]; then
    cd /opt/supernet && git pull origin master
else
    git clone https://github.com/contadtv169-stack/supernet.git /opt/supernet 2>/dev/null || \
    git clone https://github.com/KURONUZX/supernet.git /opt/supernet 2>/dev/null || true
fi
ok "Repositorio clonado"

log "[5/9] Configurando WireGuard..."
wg_priv=$(wg genkey)
wg_pub=$(echo "$wg_priv" | wg pubkey)
cat > /etc/wireguard/wg0.conf << WGEOF
[Interface]
PrivateKey = $wg_priv
Address = 10.0.0.1/24
ListenPort = 51820
DNS = 1.1.1.1, 8.8.8.8
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
WGEOF
echo "SERVER_PUBLIC_KEY=$wg_pub" > /opt/supernet/api/server.key
systemctl enable --now wg-quick@wg0 2>/dev/null || true
ok "WireGuard configurado (PubKey: $wg_pub)"

log "[6/9] Instalando servicos systemd..."
for svc in dpi api bot; do
    cat > /etc/systemd/system/supernet-${svc}.service << UNIT
[Unit]
Description=SuperNet $svc Service
After=network.target

[Service]
Type=simple
ExecStart=$( [ "$svc" = "api" ] && echo "/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 api.server:app --chdir /opt/supernet" || echo "/usr/bin/python3 /opt/supernet/$svc/${svc}_bypass_proxy.py" )
WorkingDirectory=/opt/supernet/$svc
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
UNIT
done
systemctl daemon-reload
systemctl enable --now supernet-dpi supernet-api supernet-bot 2>/dev/null || true
ok "Servicos instalados"

log "[7/9] Configurando Nginx..."
cat > /etc/nginx/sites-available/supernet << NGINX
server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}
server {
    listen 443 ssl http2;
    server_name api.contadtv169-stack.com;
    ssl_certificate /etc/ssl/certs/self-signed.crt;
    ssl_certificate_key /etc/ssl/private/self-signed.key;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
NGINX
mkdir -p /etc/nginx/sites-enabled
ln -sf /etc/nginx/sites-available/supernet /etc/nginx/sites-enabled/
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/self-signed.key -out /etc/ssl/certs/self-signed.crt -subj "/CN=supernet" 2>/dev/null
systemctl enable --now nginx && systemctl reload nginx 2>/dev/null || true
ok "Nginx configurado"

log "[8/9] Configurando firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow from 162.120.186.147/32 to any port 22
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw allow 51820/udp
ufw --force enable
ok "Firewall configurado"

log "[9/9] Configurando IPv6..."
cat >> /etc/sysctl.conf << SYSCTL
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
SYSCTL
sysctl -p 2>/dev/null || true
ok "IPv4/IPv6 forwarding ativado"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} SuperNet 6.0.0 - Setup concluido!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Servidor: 162.120.186.147"
echo "WireGuard Public Key: $(wg pubkey < /etc/wireguard/privatekey 2>/dev/null || echo 'N/A')"
echo "Proxy DPI: :8080"
echo "WireGuard: :51820"
echo "API: :5000"
echo ""
echo "Comandos uteis:"
echo "  systemctl status supernet-api"
echo "  systemctl status supernet-bot"
echo "  systemctl status supernet-dpi"
echo "  wg show"
echo ""
echo "Logs:"
echo "  journalctl -u supernet-api -f"
echo "  journalctl -u supernet-bot -f"
