#!/bin/bash
# SuperNet - Gerenciador WireGuard
# Uso: ./wg/gerar_config.sh list|add|remove|show <user>

WG_CONF="/etc/wireguard/wg0.conf"
WG_DIR="/opt/supernet/wg"
DATA_DIR="/opt/supernet/clientes"
SERVER_PUB=$(cat /opt/supernet/api/server.key 2>/dev/null | cut -d= -f2 | tr -d ' ')
SERVER_ENDPOINT="162.120.186.147:51820"
DNS="1.1.1.1, 8.8.8.8"

mkdir -p "$WG_DIR" "$DATA_DIR"

case "${1:-list}" in
    list)
        echo "=== Usuarios WireGuard ==="
        if [ -f "$WG_CONF" ]; then
            grep -E "^# Cliente|^# User" "$WG_CONF" 2>/dev/null || echo "Nenhum cliente configurado"
        else
            echo "WireGuard nao configurado"
        fi
        ;;
    add)
        USER="${2:-cliente$(date +%s)}"
        PRIV=$(wg genkey)
        PUB=$(echo "$PRIV" | wg pubkey)
        IPS=$(cat "$WG_CONF" 2>/dev/null | grep AllowedIPs | awk '{print $3}' | cut -d/ -f1 | cut -d. -f4 | sort -n | tail -1)
        IPS=${IPS:-1}
        NEXT=$((IPS + 1))
        CLIENT_IP="10.0.0.$NEXT"
        cat >> "$WG_CONF" << EOF

# Cliente: $USER
[Peer]
PublicKey = $PUB
AllowedIPs = $CLIENT_IP/32
EOF
        CONFIG="[Interface]
PrivateKey = $PRIV
Address = $CLIENT_IP/24
DNS = $DNS

[Peer]
PublicKey = $SERVER_PUB
Endpoint = $SERVER_ENDPOINT
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"
        echo "$CONFIG" > "$WG_DIR/${USER}.conf"
        echo "$CONFIG"
        echo ""
        echo "Config salva em: $WG_DIR/${USER}.conf"
        echo "IP: $CLIENT_IP"
        wg addconf wg0 <(wg-quick strip wg0 2>/dev/null) 2>/dev/null || true
        ;;
    remove)
        USER="${2}"
        if [ -z "$USER" ]; then echo "Uso: $0 remove <usuario>"; exit 1; fi
        sed -i "/# Cliente: $USER/,+3d" "$WG_CONF" 2>/dev/null
        rm -f "$WG_DIR/${USER}.conf"
        echo "Usuario $USER removido"
        wg addconf wg0 <(wg-quick strip wg0 2>/dev/null) 2>/dev/null || true
        ;;
    show)
        USER="${2}"
        if [ -z "$USER" ]; then echo "Uso: $0 show <usuario>"; exit 1; fi
        if [ -f "$WG_DIR/${USER}.conf" ]; then
            cat "$WG_DIR/${USER}.conf"
        else
            echo "Config nao encontrada para $USER"
        fi
        ;;
    *)
        echo "Uso: $0 {list|add|remove|show} [usuario]"
        ;;
esac
