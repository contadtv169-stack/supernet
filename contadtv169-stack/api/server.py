from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

clientes_db = {}
pagamentos_db = []

@app.route("/")
def home():
    return jsonify({"service": "SuperNet API", "status": "online", "version": "6.0.0"})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/dashboard")
def dashboard():
    return jsonify({
        "clientes_ativos": len([c for c in clientes_db.values() if c.get("status") == "ativo"]),
        "vendas_hoje": 0,
        "faturamento_mensal": 0,
        "saldo_krypt": 0,
    })

@app.route("/api/clientes", methods=["GET"])
def listar_clientes():
    return jsonify(list(clientes_db.values()))

@app.route("/api/clientes", methods=["POST"])
def criar_cliente():
    data = request.json
    cliente_id = str(len(clientes_db) + 1)
    clientes_db[cliente_id] = {
        "id": cliente_id,
        "nome": data.get("nome", ""),
        "discord": data.get("discord", ""),
        "plano": data.get("plano", "basico"),
        "status": "ativo",
        "expira": data.get("expira", ""),
    }
    return jsonify(clientes_db[cliente_id]), 201

@app.route("/api/clientes/<id>", methods=["PUT"])
def atualizar_cliente(id):
    data = request.json
    if id in clientes_db:
        clientes_db[id].update(data)
        return jsonify(clientes_db[id])
    return jsonify({"error": "Cliente nao encontrado"}), 404

@app.route("/api/clientes/<id>/bloquear", methods=["POST"])
def bloquear_cliente(id):
    if id in clientes_db:
        clientes_db[id]["status"] = "bloqueado"
        return jsonify(clientes_db[id])
    return jsonify({"error": "Cliente nao encontrado"}), 404

@app.route("/api/clientes/<id>/desbloquear", methods=["POST"])
def desbloquear_cliente(id):
    if id in clientes_db:
        clientes_db[id]["status"] = "ativo"
        return jsonify(clientes_db[id])
    return jsonify({"error": "Cliente nao encontrado"}), 404

@app.route("/api/pagamentos", methods=["GET"])
def listar_pagamentos():
    return jsonify(pagamentos_db)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
