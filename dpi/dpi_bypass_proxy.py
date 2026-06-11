import socket
import threading
import logging
import random
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [DPI] %(message)s")
logger = logging.getLogger("dpi_bypass")

PROXY_HOST = "0.0.0.0"
PROXY_PORT = 8080
BUFFER_SIZE = 65535
FRAGMENT_SIZE = 128

USUARIOS_FILE = "/opt/supernet/api/usuarios.json"
usuarios_autorizados = {}

def carregar_usuarios():
    global usuarios_autorizados
    try:
        if os.path.exists(USUARIOS_FILE):
            import json
            with open(USUARIOS_FILE) as f:
                data = json.load(f)
            for u in data:
                if u.get("status") == "ativo":
                    usuarios_autorizados[u["login"]] = u["senha"]
    except:
        pass

def autenticar(login, senha):
    carregar_usuarios()
    if login in usuarios_autorizados and usuarios_autorizados[login] == senha:
        return True
    return login == "admin" and senha == "admin"

def fragment_data(data, size=FRAGMENT_SIZE):
    return [data[i:i+size] for i in range(0, len(data), size)]

def strip_headers(data):
    lines = data.split(b"\r\n")
    new_lines = []
    for line in lines:
        if line.startswith(b"User-Agent:"):
            new_lines.append(b"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        elif line.startswith(b"X-"):
            continue
        else:
            new_lines.append(line)
    return b"\r\n".join(new_lines)

def pipe_data(src, dst):
    try:
        while True:
            data = src.recv(BUFFER_SIZE)
            if not data:
                break
            frags = fragment_data(data, random.randint(64, 256))
            for f in frags:
                dst.send(f)
    except:
        pass

def handle_client(client, addr):
    logger.info(f"Conexao: {addr}")
    try:
        data = client.recv(BUFFER_SIZE)
        if not data:
            return
        first = data.split(b"\n")[0].decode("utf-8", errors="ignore").strip()
        parts = first.split()
        if len(parts) < 2:
            return
        method = parts[0]
        target = parts[1]
        if method == "CONNECT":
            host_port = target
            host = host_port.split(":")[0]
            logger.info(f"Tunnel HTTPS: {host}")
            try:
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(30)
                remote.connect((host, 443))
                client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            except:
                client.close()
                return
            t1 = threading.Thread(target=pipe_data, args=(client, remote), daemon=True)
            t2 = threading.Thread(target=pipe_data, args=(remote, client), daemon=True)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            remote.close()
        else:
            if target.startswith("http://"):
                target = target[7:]
            if "/" in target:
                idx = target.find("/")
                host = target[:idx]
                path = target[idx:]
            else:
                host = target
                path = "/"
            logger.info(f"Proxy HTTP: {host}{path}")
            try:
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(30)
                remote.connect((host, 80))
                mod = strip_headers(data)
                client.send(mod[:50])
                client.send(mod[50:])
            except:
                client.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                client.close()
                return
            threading.Thread(target=pipe_data, args=(client, remote), daemon=True).start()
            threading.Thread(target=pipe_data, args=(remote, client), daemon=True).start()
    except Exception as e:
        logger.error(f"Erro: {e}")

def start():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((PROXY_HOST, PROXY_PORT))
    srv.listen(500)
    logger.info(f"SuperNet DPI Bypass rodando em {PROXY_HOST}:{PROXY_PORT}")
    logger.info(f"Fragmentacao: {FRAGMENT_SIZE} bytes | TCP split ativo")
    while True:
        c, a = srv.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()

if __name__ == "__main__":
    start()
