import socket
import select
import threading
import struct
import ssl
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [DPI] %(message)s")
logger = logging.getLogger("dpi_bypass")

PROXY_HOST = "0.0.0.0"
PROXY_PORT = 8080
BUFFER_SIZE = 65535
FRAGMENT_SIZE = 128

ALVO_DOMAINS = [
    "youtube.com", "googlevideo.com", "ytimg.com",
    "whatsapp.com", "whatsapp.net",
    "netflix.com", "nflxvideo.net",
    "spotify.com", "twitch.tv",
    "instagram.com", "tiktok.com", "facebook.com",
]

DNS_SERVERS = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
current_dns = 0

def fragment_data(data, size=FRAGMENT_SIZE):
    fragments = []
    for i in range(0, len(data), size):
        fragments.append(data[i:i+size])
    return fragments

def send_fragmented(client_socket, data):
    fragments = fragment_data(data)
    for frag in fragments:
        try:
            client_socket.send(frag)
        except:
            break

def strip_http_headers(data):
    lines = data.split(b"\r\n")
    new_lines = []
    for line in lines:
        if line.startswith(b"User-Agent:"):
            new_lines.append(b"User-Agent: Mozilla/5.0")
        elif line.startswith(b"Host:"):
            new_lines.append(line)
        else:
            new_lines.append(line)
    return b"\r\n".join(new_lines)

def modify_tls_hello(data):
    if len(data) < 5:
        return data
    if data[0] == 0x16 and data[1] == 0x03:
        logger.info("Fragmentando TLS ClientHello")
        return data[:50] + b"\x00" * 50 + data[50:]
    return data

def handle_https_tunnel(client, remote):
    try:
        remote.connect(("8.8.8.8", 443))
    except:
        return
    threading.Thread(target=lambda: pipe_data(client, remote), daemon=True).start()
    threading.Thread(target=lambda: pipe_data(remote, client), daemon=True).start()

def pipe_data(src, dst):
    try:
        while True:
            data = src.recv(BUFFER_SIZE)
            if not data:
                break
            chunks = fragment_data(data, random.randint(64, 256))
            for chunk in chunks:
                dst.send(chunk)
    except:
        pass

def handle_client(client_socket, addr):
    logger.info(f"Conexao de {addr}")
    try:
        data = client_socket.recv(BUFFER_SIZE)
        if not data:
            return
        first_line = data.split(b"\n")[0].decode("utf-8", errors="ignore").strip()
        parts = first_line.split()
        if len(parts) < 2:
            return
        method = parts[0]
        target = parts[1]
        if method == "CONNECT":
            host_port = target
            host = host_port.split(":")[0]
            logger.info(f"Tunnel HTTPS para {host_port}")
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(30)
            try:
                remote.connect((host, 443))
                client_socket.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                send_fragmented(client_socket, b"\r\n\r\n")
            except:
                client_socket.close()
                return
            threading.Thread(target=pipe_data, args=(client_socket, remote), daemon=True).start()
            threading.Thread(target=pipe_data, args=(remote, client_socket), daemon=True).start()
        else:
            if target.startswith("http://"):
                target = target[7:]
            path = "/"
            if "/" in target:
                idx = target.find("/")
                host = target[:idx]
                path = target[idx:]
            else:
                host = target
            logger.info(f"Proxy HTTP para {host}{path}")
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(30)
            try:
                remote.connect((host, 80))
            except:
                client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                return
            modified_data = strip_http_headers(data)
            modified_data = modify_tls_hello(modified_data)
            send_fragmented(client_socket, modified_data[:50])
            send_fragmented(client_socket, modified_data[50:])
            threading.Thread(target=pipe_data, args=(client_socket, remote), daemon=True).start()
            threading.Thread(target=pipe_data, args=(remote, client_socket), daemon=True).start()
    except Exception as e:
        logger.error(f"Erro: {e}")
    finally:
        pass

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((PROXY_HOST, PROXY_PORT))
    server.listen(200)
    logger.info(f"DPI Bypass Proxy rodando em {PROXY_HOST}:{PROXY_PORT}")
    logger.info(f"Fragmentacao TCP ativa ({FRAGMENT_SIZE} bytes)")
    logger.info(f"DNS Servers: {', '.join(DNS_SERVERS)}")
    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()

if __name__ == "__main__":
    import random
    start_proxy()
