import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "MTUxNDI3NTU4Mjc0NDE5OTM4OA.GwmhpG.c4NXR-Y-98BY1Ez2bWBsyQCpQ0wkpSlFOqs-3g")
GUILD_ID = int(os.getenv("GUILD_ID", "1514275582744199388"))
KRYPT_CI = os.getenv("KRYPT_CI", "krypt_ci_49e0355123ad4d54fa")
KRYPT_CS = os.getenv("KRYPT_CS", "krypt_cs_952dfe7561989e86e889204c1f1ab313")
KRYPT_PIX = os.getenv("KRYPT_PIX", "https://kryptgateway.netlify.app/api/gateway/pix-create")
KRYPT_CRYPTO = os.getenv("KRYPT_CRYPTO", "https://kryptgateway.netlify.app/api/gateway/crypto-create")
KRYPT_CASHOUT = os.getenv("KRYPT_CASHOUT", "https://kryptgateway.netlify.app/api/merchant/cashout")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

clientes_db = {}
planos = {
    "basico": {"nome": "Basico", "preco": 19.90, "velocidade": "10 Mbps", "dias": 30},
    "premium": {"nome": "Premium", "preco": 39.90, "velocidade": "25 Mbps", "dias": 30},
}

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"SuperNet Bot online como {bot.user}")

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
@app_commands.describe(plano="basico ou premium")
async def comprar(interaction: discord.Interaction, plano: str):
    plano = plano.lower()
    if plano not in planos:
        await interaction.response.send_message("Planos: basico (R$19,90) ou premium (R$39,90)", ephemeral=True)
        return
    p = planos[plano]
    embed = discord.Embed(title=f"Plano {p['nome']}", color=0x00d4ff)
    embed.add_field(name="Preco", value=f"R${p['preco']:.2f}")
    embed.add_field(name="Velocidade", value=p["velocidade"])
    embed.add_field(name="Validade", value=f"{p['dias']} dias")
    embed.set_footer(text="Use /pix ou /crypto para pagar")
    await interaction.response.send_message(embed=embed)
    clientes_db[str(interaction.user.id)] = {"plano": plano, "status": "aguardando_pagamento"}

@bot.tree.command(name="pix", description="Gerar QR Code PIX para pagamento", guild=discord.Object(id=GUILD_ID))
async def pix(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in clientes_db:
        await interaction.response.send_message("Use /comprar primeiro!", ephemeral=True)
        return
    plano = clientes_db[user_id]["plano"]
    p = planos[plano]
    result = criar_pix(p["preco"], interaction.user.name, "00000000000", f"Plano {p['nome']} SuperNet")
    if "error" in result:
        await interaction.response.send_message(f"Erro: {result['error']}", ephemeral=True)
        return
    embed = discord.Embed(title="Pagamento PIX", color=0x00d4ff)
    embed.add_field(name="Valor", value=f"R${p['preco']:.2f}")
    embed.add_field(name="QR Code", value=result.get("qrCode", "Verifique o pagamento"))
    embed.add_field(name="Copia e Cola", value=result.get("copyPaste", "N/A"))
    embed.set_footer(text="Apos pagar, use /status para confirmar")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="crypto", description="Gerar endereco USDT TRC20 para pagamento", guild=discord.Object(id=GUILD_ID))
async def crypto(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in clientes_db:
        await interaction.response.send_message("Use /comprar primeiro!", ephemeral=True)
        return
    plano = clientes_db[user_id]["plano"]
    p = planos[plano]
    result = criar_crypto(p["preco"], f"Plano {p['nome']} SuperNet")
    if "error" in result:
        await interaction.response.send_message(f"Erro: {result['error']}", ephemeral=True)
        return
    embed = discord.Embed(title="Pagamento USDT TRC20", color=0x00d4ff)
    embed.add_field(name="Valor", value=f"R${p['preco']:.2f}")
    embed.add_field(name="Endereco", value=result.get("address", "N/A"))
    embed.add_field(name="Rede", value="TRC20")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status", description="Verificar status do pedido", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(pedido_id="ID do pedido")
async def status(interaction: discord.Interaction, pedido_id: str = None):
    user_id = str(interaction.user.id)
    if user_id in clientes_db:
        dados = clientes_db[user_id]
        await interaction.response.send_message(f"Status: {dados['status']} | Plano: {dados['plano']}")
    else:
        await interaction.response.send_message("Nenhum pedido encontrado.", ephemeral=True)

@bot.tree.command(name="ajuda", description="Exibir ajuda e comandos", guild=discord.Object(id=GUILD_ID))
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="SuperNet - Ajuda", color=0x00d4ff)
    embed.add_field(name="/comprar [basico|premium]", value="Iniciar compra", inline=False)
    embed.add_field(name="/pix", value="Pagamento via PIX", inline=False)
    embed.add_field(name="/crypto", value="Pagamento via USDT TRC20", inline=False)
    embed.add_field(name="/status [id]", value="Ver status do pedido", inline=False)
    embed.add_field(name="/ajuda", value="Mostrar esta mensagem", inline=False)
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
