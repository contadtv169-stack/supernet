import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import os
import uuid
from datetime import datetime, timedelta

TOKEN = "MTUxNDI3NTU4Mjc0NDE5OTM4OA.GwmhpG.c4NXR-Y-98BY1Ez2bWBsyQCpQ0wkpSlFOqs-3g"
GUILD_ID = 1514275582744199388
API_URL = "http://localhost:5000"
KRYPT_CI = "krypt_ci_49e0355123ad4d54fa"
KRYPT_CS = "krypt_cs_952dfe7561989e86e889204c1f1ab313"
KRYPT_PIX = "https://kryptgateway.netlify.app/api/gateway/pix-create"
KRYPT_CRYPTO = "https://kryptgateway.netlify.app/api/gateway/crypto-create"
SERVER_IP = "162.120.186.147"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

pedidos = {}
planos = {
    "basico": {"nome": "Basico", "preco": 19.90, "velocidade": "10 Mbps", "dias": 30, "role": "Cliente"},
    "premium": {"nome": "Premium", "preco": 39.90, "velocidade": "25 Mbps", "dias": 30, "role": "Cliente Premium"},
}

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"SuperNet Bot online: {bot.user} | Guild: {GUILD_ID}")

def gerar_login():
    return "SN" + uuid.uuid4().hex[:6].upper()

def gerar_senha():
    return uuid.uuid4().hex[:16]

def criar_pix(valor, nome, documento, descricao):
    payload = {"amount": valor, "payerName": nome, "payerDocument": documento, "description": descricao}
    headers = {"Content-Type": "application/json", "ci": KRYPT_CI, "cs": KRYPT_CS}
    try:
        r = requests.post(KRYPT_PIX, json=payload, headers=headers, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def criar_crypto(valor, descricao):
    payload = {"amount": valor, "network": "TRC20", "description": descricao}
    headers = {"Content-Type": "application/json", "ci": KRYPT_CI, "cs": KRYPT_CS}
    try:
        r = requests.post(KRYPT_CRYPTO, json=payload, headers=headers, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@bot.tree.command(name="comprar", description="Comprar plano de internet", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(plano="Plano: basico (R$19,90) ou premium (R$39,90)")
async def comprar(interaction: discord.Interaction, plano: str):
    plano = plano.lower()
    if plano not in planos:
        await interaction.response.send_message("Planos: `basico` (R$19,90) ou `premium` (R$39,90)", ephemeral=True)
        return
    p = planos[plano]
    pedido_id = uuid.uuid4().hex[:8]
    pedidos[pedido_id] = {
        "user_id": str(interaction.user.id),
        "user_name": interaction.user.name,
        "plano": plano,
        "status": "aguardando_pagamento",
    }
    embed = discord.Embed(title="SuperNet - Novo Pedido", color=0x00d4ff)
    embed.add_field(name="Plano", value=p["nome"], inline=True)
    embed.add_field(name="Valor", value=f"R$ {p['preco']:.2f}", inline=True)
    embed.add_field(name="Velocidade", value=p["velocidade"], inline=True)
    embed.add_field(name="Pedido ID", value=f"`{pedido_id}`", inline=False)
    embed.set_footer(text="Use /pix ou /crypto para pagar | Use /status para verificar")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pix", description="Gerar pagamento via PIX", guild=discord.Object(id=GUILD_ID))
async def pix(interaction: discord.Interaction):
    pid = None
    for k, v in pedidos.items():
        if v["user_id"] == str(interaction.user.id) and v["status"] == "aguardando_pagamento":
            pid = k
            break
    if not pid:
        await interaction.response.send_message("Use `/comprar` primeiro!", ephemeral=True)
        return
    p = planos[pedidos[pid]["plano"]]
    result = criar_pix(p["preco"], interaction.user.name, "00000000000", f"Plano {p['nome']} SuperNet - {pid}")
    embed = discord.Embed(title="Pagamento PIX", color=0x00d4ff)
    embed.add_field(name="Pedido", value=f"`{pid}`", inline=True)
    embed.add_field(name="Valor", value=f"R$ {p['preco']:.2f}", inline=True)
    if "error" in result:
        embed.add_field(name="QR Code", value=result.get("qrCode", "PIX gerado - verifique no app do banco"), inline=False)
        embed.add_field(name="Copia e Cola", value=result.get("copyPaste", result.get("emv", "N/A")), inline=False)
    else:
        embed.add_field(name="QR Code", value=result.get("qrCode", "PIX gerado"), inline=False)
        embed.add_field(name="Copia e Cola", value=result.get("copyPaste", result.get("emv", "N/A")), inline=False)
    embed.set_footer(text="Apos pagar, use /confirmar para receber suas credenciais")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="crypto", description="Gerar pagamento via USDT TRC20", guild=discord.Object(id=GUILD_ID))
async def crypto(interaction: discord.Interaction):
    pid = None
    for k, v in pedidos.items():
        if v["user_id"] == str(interaction.user.id) and v["status"] == "aguardando_pagamento":
            pid = k
            break
    if not pid:
        await interaction.response.send_message("Use `/comprar` primeiro!", ephemeral=True)
        return
    p = planos[pedidos[pid]["plano"]]
    result = criar_crypto(p["preco"], f"Plano {p['nome']} SuperNet - {pid}")
    embed = discord.Embed(title="Pagamento USDT TRC20", color=0x00d4ff)
    embed.add_field(name="Pedido", value=f"`{pid}`", inline=True)
    embed.add_field(name="Valor", value=f"R$ {p['preco']:.2f}", inline=True)
    if "error" in result:
        embed.add_field(name="Endereco", value=result.get("address", "Endereco gerado"), inline=False)
    else:
        embed.add_field(name="Endereco", value=result.get("address", "N/A"), inline=False)
    embed.add_field(name="Rede", value="TRC20", inline=True)
    embed.set_footer(text="Apos pagar, use /confirmar para receber suas credenciais")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="confirmar", description="Confirmar pagamento e gerar credenciais", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(pedido_id="ID do pedido")
async def confirmar(interaction: discord.Interaction, pedido_id: str):
    pid = pedido_id.lower()
    if pid not in pedidos:
        await interaction.response.send_message("Pedido nao encontrado. Use `/comprar` primeiro.", ephemeral=True)
        return
    ped = pedidos[pid]
    if ped["user_id"] != str(interaction.user.id):
        await interaction.response.send_message("Este pedido nao e seu.", ephemeral=True)
        return
    p = planos[ped["plano"]]
    login = gerar_login()
    senha = gerar_senha()
    expira = (datetime.utcnow() + timedelta(days=p["dias"])).strftime("%d/%m/%Y")
    wg_config = f"""[Interface]
PrivateKey = {uuid.uuid4().hex}
Address = 10.0.0.{hash(interaction.user.id) % 253 + 2}/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = {SERVER_IP}:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
    ped["status"] = "ativo"
    ped["login"] = login
    ped["senha"] = senha
    embed = discord.Embed(title="Pagamento Confirmado!", color=0x22c55e)
    embed.add_field(name="Plano", value=p["nome"], inline=True)
    embed.add_field(name="Validade", value=expira, inline=True)
    embed.add_field(name="", value="**Suas Credenciais de Acesso:**", inline=False)
    embed.add_field(name="Login", value=f"`{login}`", inline=True)
    embed.add_field(name="Senha", value=f"`{senha}`", inline=True)
    embed.add_field(name="Servidor", value=f"`{SERVER_IP}`", inline=True)
    embed.add_field(name="WireGuard Porta", value="`51820`", inline=True)
    embed.add_field(name="Proxy HTTP", value=f"`{SERVER_IP}:8080`", inline=True)
    embed.add_field(name="Configuracao WireGuard", value=f"```ini\n{wg_config}\n```", inline=False)
    embed.set_footer(text="Salve essas informacoes! Use /senha se perder.")
    await interaction.response.send_message(embed=embed)
    try:
        role = discord.utils.get(interaction.guild.roles, name=p["role"])
        if role:
            await interaction.user.add_roles(role)
    except:
        pass

@bot.tree.command(name="credenciais", description="Exibir suas credenciais de acesso", guild=discord.Object(id=GUILD_ID))
async def credenciais(interaction: discord.Interaction):
    user_pedidos = [(k, v) for k, v in pedidos.items() if v["user_id"] == str(interaction.user.id) and v.get("status") == "ativo"]
    if not user_pedidos:
        await interaction.response.send_message("Voce nao possui nenhuma assinatura ativa. Use `/comprar`.", ephemeral=True)
        return
    pid, ped = user_pedidos[-1]
    p = planos[ped["plano"]]
    embed = discord.Embed(title="Suas Credenciais SuperNet", color=0x00d4ff)
    embed.add_field(name="Login", value=f"`{ped.get('login', 'N/A')}`", inline=True)
    embed.add_field(name="Senha", value=f"`{ped.get('senha', 'N/A')}`", inline=True)
    embed.add_field(name="Servidor", value=f"`{SERVER_IP}`", inline=True)
    embed.add_field(name="WireGuard", value=f"`{SERVER_IP}:51820`", inline=True)
    embed.add_field(name="Proxy DPI", value=f"`{SERVER_IP}:8080`", inline=True)
    embed.add_field(name="Plano", value=p["nome"], inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="Verificar status do pedido", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(pedido_id="ID do pedido (opcional)")
async def status(interaction: discord.Interaction, pedido_id: str = None):
    if pedido_id:
        pid = pedido_id.lower()
        if pid in pedidos:
            ped = pedidos[pid]
            await interaction.response.send_message(f"Pedido `{pid}`: **{ped['status']}** | Plano: {ped['plano']}")
        else:
            await interaction.response.send_message(f"Pedido `{pid}` nao encontrado.", ephemeral=True)
    else:
        user_pedidos = [(k, v) for k, v in pedidos.items() if v["user_id"] == str(interaction.user.id)]
        if user_pedidos:
            msg = "\n".join([f"`{k}`: {v['status']} - {v['plano']}" for k, v in user_pedidos])
            await interaction.response.send_message(f"Seus pedidos:\n{msg}")
        else:
            await interaction.response.send_message("Nenhum pedido encontrado.", ephemeral=True)

@bot.tree.command(name="renovar", description="Renovar seu plano", guild=discord.Object(id=GUILD_ID))
async def renovar(interaction: discord.Interaction):
    user_pedidos = [(k, v) for k, v in pedidos.items() if v["user_id"] == str(interaction.user.id)]
    if not user_pedidos:
        await interaction.response.send_message("Use `/comprar` para assinar um plano.", ephemeral=True)
        return
    _, ped = user_pedidos[-1]
    plano = ped["plano"]
    p = planos[plano]
    pid = uuid.uuid4().hex[:8]
    pedidos[pid] = {"user_id": str(interaction.user.id), "user_name": interaction.user.name, "plano": plano, "status": "aguardando_pagamento", "renovacao": True}
    embed = discord.Embed(title="Renovacao de Plano", color=0xf59e0b)
    embed.add_field(name="Plano", value=p["nome"], inline=True)
    embed.add_field(name="Valor", value=f"R$ {p['preco']:.2f}", inline=True)
    embed.add_field(name="Pedido ID", value=f"`{pid}`", inline=True)
    embed.set_footer(text="Use /pix ou /crypto para pagar")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="senha", description="Recuperar sua senha de acesso", guild=discord.Object(id=GUILD_ID))
async def senha(interaction: discord.Interaction):
    user_pedidos = [(k, v) for k, v in pedidos.items() if v["user_id"] == str(interaction.user.id) and v.get("status") == "ativo"]
    if not user_pedidos:
        await interaction.response.send_message("Voce nao possui assinatura ativa.", ephemeral=True)
        return
    _, ped = user_pedidos[-1]
    await interaction.response.send_message(f"**Login:** `{ped.get('login', 'N/A')}`\n**Senha:** `{ped.get('senha', 'N/A')}`", ephemeral=True)

@bot.tree.command(name="ajuda", description="Exibir todos os comandos", guild=discord.Object(id=GUILD_ID))
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="SuperNet - Comandos", color=0x00d4ff)
    embed.add_field(name="/comprar [basico|premium]", value="Comprar plano de internet", inline=False)
    embed.add_field(name="/pix", value="Gerar pagamento via PIX", inline=False)
    embed.add_field(name="/crypto", value="Gerar pagamento via USDT TRC20", inline=False)
    embed.add_field(name="/confirmar [id]", value="Confirmar pagamento e gerar credenciais", inline=False)
    embed.add_field(name="/credenciais", value="Exibir suas credenciais de acesso", inline=False)
    embed.add_field(name="/status [id]", value="Ver status do pedido", inline=False)
    embed.add_field(name="/renovar", value="Renovar seu plano", inline=False)
    embed.add_field(name="/senha", value="Recuperar sua senha", inline=False)
    embed.add_field(name="/ajuda", value="Exibir esta mensagem", inline=False)
    embed.set_footer(text="SuperNet 6.0.0 - contadtv169-stack")
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
