import json
import os
import uuid
import hashlib
import subprocess
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = "/opt/supernet/api/usuarios.json"
WG_CONF = "/etc/wireguard/wg0.conf"
WG_INTERFACE = "wg0"
SERVER_PUBLIC_KEY = None
SERVER_ENDPOINT = "162.120.186.147:51820"
DNS_SERVERS = "1.1.1.1, 8.8.8.8"
ALLOWED_IPS = "0.0.0.0/0, ::/0"

def carregar_usuarios():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return []

def salvar_usuarios(usuarios):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(usuarios, f, indent=2)

def gerar_wg_keypair():
    try:
        priv = subprocess.check_output(["wg", "genkey"]).decode().strip()
        pub = subprocess.check_output(["wg", "pubkey"], input=priv.encode()).decode().strip()
        return priv, pub
    except:
        return None, None

def gerar_wg_config(server_pub, client_priv, client_pub, client_ip):
    return f"""[Interface]
PrivateKey = {client_priv}
Address = {client_ip}/24
DNS = {DNS_SERVERS}

[Peer]
PublicKey = {server_pub}
Endpoint = {SERVER_ENDPOINT}
AllowedIPs = {ALLOWED_IPS}
PersistentKeepalive = 25
"""

@app.route("/")
def home():
    return jsonify({"service": "SuperNet API", "status": "online", "version": "6.0.0"})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

@app.route("/api/dashboard")
def dashboard():
    usuarios = carregar_usuarios()
    ativos = len([u for u in usuarios if u.get("status") == "ativo"])
    return jsonify({
        "clientes_ativos": ativos,
        "total_usuarios": len(usuarios),
        "vendas_hoje": 0,
        "faturamento_mensal": sum(39.9 if u.get("plano") == "premium" else 19.9 for u in usuarios),
        "saldo_krypt": 0,
    })

@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    return jsonify(carregar_usuarios())

@app.route("/api/usuarios", methods=["POST"])
def criar_usuario():
    data = request.json
    usuarios = carregar_usuarios()
    priv, pub = gerar_wg_keypair()
    if not priv:
        return jsonify({"error": "Falha ao gerar chaves WireGuard"}), 500
    
    next_ip = 2
    used_ips = set()
    for u in usuarios:
        ip = u.get("wg_ip", "")
        if ip:
            parts = ip.split(".")
            if len(parts) == 4 and parts[3].isdigit():
                used_ips.add(int(parts[3]))
    for i in range(2, 255):
        if i not in used_ips:
            next_ip = i
            break
    
    client_ip = f"10.0.0.{next_ip}"
    login = "SN" + uuid.uuid4().hex[:6].upper()
    senha = uuid.uuid4().hex[:16]
    dias = int(data.get("dias", 30))
    expira = (datetime.utcnow() + timedelta(days=dias)).strftime("%Y-%m-%d")
    
    usuario = {
        "id": str(len(usuarios) + 1).zfill(4),
        "nome": data.get("nome", "Cliente"),
        "discord": data.get("discord", ""),
        "login": login,
        "senha": senha,
        "plano": data.get("plano", "basico"),
        "status": "ativo",
        "expira": expira,
        "wg_private": priv,
        "wg_public": pub,
        "wg_ip": client_ip,
        "criado": datetime.utcnow().isoformat(),
    }
    usuarios.append(usuario)
    salvar_usuarios(usuarios)
    return jsonify({"id": usuario["id"], "login": login, "senha": senha, "wg_ip": client_ip, "expira": expira}), 201

@app.route("/api/usuarios/<id>", methods=["GET"])
def get_usuario(id):
    usuarios = carregar_usuarios()
    u = next((x for x in usuarios if x["id"] == id), None)
    if not u:
        return jsonify({"error": "Nao encontrado"}), 404
    safe = {k: v for k, v in u.items() if k not in ("wg_private",)}
    return jsonify(safe)

@app.route("/api/usuarios/<id>/credenciais", methods=["GET"])
def get_credenciais(id):
    usuarios = carregar_usuarios()
    u = next((x for x in usuarios if x["id"] == id), None)
    if not u:
        return jsonify({"error": "Nao encontrado"}), 404
    config = gerar_wg_config(SERVER_PUBLIC_KEY or "SERVER_PUB_KEY", u.get("wg_private", ""), u.get("wg_public", ""), u.get("wg_ip", "10.0.0.2"))
    return jsonify({
        "login": u["login"],
        "senha": u["senha"],
        "servidor": "162.120.186.147",
        "wg_porta": 51820,
        "proxy_porta": 8080,
        "wg_config": config,
    })

@app.route("/api/usuarios/<id>/bloquear", methods=["POST"])
def bloquear(id):
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u["id"] == id:
            u["status"] = "bloqueado"
            salvar_usuarios(usuarios)
            return jsonify({"status": "bloqueado"})
    return jsonify({"error": "Nao encontrado"}), 404

@app.route("/api/usuarios/<id>/desbloquear", methods=["POST"])
def desbloquear(id):
    usuarios = carregar_usuarios()
    for u in usuarios:
        if u["id"] == id:
            u["status"] = "ativo"
            salvar_usuarios(usuarios)
            return jsonify({"status": "ativo"})
    return jsonify({"error": "Nao encontrado"}), 404

@app.route("/api/usuarios/<id>", methods=["DELETE"])
def excluir(id):
    usuarios = carregar_usuarios()
    usuarios = [u for u in usuarios if u["id"] != id]
    salvar_usuarios(usuarios)
    return jsonify({"status": "excluido"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
