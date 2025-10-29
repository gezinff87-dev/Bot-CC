import discord
from discord.ext import commands
import random
import os
from flask import Flask
from threading import Thread

# Configurações do bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Servidor web para manter o bot online
app = Flask('')

@app.route('/')
def home():
    return "Bot está rodando!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = Thread(target=run)
    server.daemon = True
    server.start()

# Comando simples para testar
@bot.command(name='teste')
async def teste(ctx):
    await ctx.send("Bot funcionando!")

@bot.command(name='gerarcc')
async def gerar_cc(ctx, quantidade: int = 1):
    if quantidade > 3:
        await ctx.send("Máximo de 3 cartões!")
        return
    
    embed = discord.Embed(title="Cartões de Teste", color=0x00ff00)
    
    for i in range(quantidade):
        numero = '4' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
        mes = str(random.randint(1, 12)).zfill(2)
        ano = str(random.randint(2024, 2030))
        cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        
        embed.add_field(
            name=f"Cartão {i+1}",
            value=f"Numero: {numero}\nVal: {mes}/{ano}\nCVV: {cvv}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!teste"))

# Iniciar
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get('DISCORD_TOKEN'))
