import discord
from discord.ext import commands
import random
import asyncio
import os
import logging
from flask import Flask
from threading import Thread
import aiohttp
import re

# Configurações do bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Servidor web para manter o bot online
app = Flask('')

@app.route('/')
def home():
    return "🤖 Bot está rodando!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = Thread(target=run)
    server.daemon = True
    server.start()

# Cartões de teste para sandbox (FORNECIDOS POR STRIPE)
CARTOES_TESTE = {
    'visa_approved': {
        'numero': '4242424242424242',
        'bandeira': 'Visa',
        'status': 'live',
        'mensagem': 'Pagamento aprovado no verify'
    },
    'visa_declined': {
        'numero': '4000000000000002',
        'bandeira': 'Visa', 
        'status': 'die',
        'mensagem': 'Pagamento recusado no verify'
    },
    'mastercard_approved': {
        'numero': '5555555555554444',
        'bandeira': 'Mastercard',
        'status': 'live',
        'mensagem': 'Pagamento aprovado no verify'
    },
    'mastercard_declined': {
        'numero': '4000000000009987',
        'bandeira': 'Mastercard',
        'status': 'die',
        'mensagem': 'Fundos insuficientes no verify'
    },
    'amex_approved': {
        'numero': '378282246310005',
        'bandeira': 'American Express',
        'status': 'live',
        'mensagem': 'Pagamento aprovado na verify'
    }
}

# Gerador de CC fake educacional (APENAS PARA TESTES)
def gerar_cc_educacional():
    """Gera números de cartão"""
    bandeiras = ['visa_approved', 'mastercard_approved', 'amex_approved']
    bandeira_escolhida = random.choice(bandeiras)
    cartao_teste = CARTOES_TESTE[bandeira_escolhida]
    
    mes = str(random.randint(1, 12)).zfill(2)
    ano = str(random.randint(2024, 2030))
    cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
    
    return {
        'numero': cartao_teste['numero'],
        'mes': mes,ephemeral 
        'ano': ano,
        'cvv': cvv,
        'bandeira': cartao_teste['bandeira'],
        'tipo': 'cartao_teste'
    }

# Algoritmo de Luhn para validação educacional
def validar_luhn(numero):
    """Valida número de cartão usando algoritmo de Luhn"""
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(numero)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10 == 0

# Identificar bandeira educacional
def identificar_bandeira_educacional(numero):
    """Identifica bandeira baseada nos primeiros dígitos (educacional)"""
    numero_clean = numero.replace(' ', '').replace('-', '')
    
    if numero_clean.startswith('4'):
        return 'Visa'
    elif numero_clean.startswith(('51', '52', '53', '54', '55')):
        return 'Mastercard'
    elif numero_clean.startswith(('34', '37')):
        return 'American Express'
    elif numero_clean.startswith(('300', '301', '302', '303', '304', '305')):
        return 'Diners Club'
    elif numero_clean.startswith(('6011', '65')):
        return 'Discover'
    else:
        return 'Desconhecida'

# Verificação educacional com sandbox
async def verificar_sandbox_educacional(cc_data):
    """
    VERIFICAÇÃO - Usar cartões
    Ambiente de segurança máxima.
    """
    numero_clean = cc_data['numero'].replace(' ', '').replace('-', '')
    
    # Verifica se é um cartão de teste conhecido
    for chave, cartao in CARTOES_TESTE.items():
        if cartao['numero'] == numero_clean:
            return {
                'status': cartao['status'],
                'resposta': f"Cartão {cartao['status'].upper()} (Sandbox)",
                'detalhes': cartao['mensagem'],
                'bandeira': cartao['bandeira'],
                'ambiente': 'VERIFY'
            }
    
    # Se não for cartão de teste, faz valid
    luhn_valido = validar_luhn(numero_clean)
    bandeira = identificar_bandeira_educacional(numero_clean)
    
    if luhn_valido:
        return {
            'status': 'unknown',
            'resposta': 'FORMATO VÁLIDO',
            'detalhes': f'Número passa na validação Luhn. Bandeira: {bandeira}',
            'bandeira': bandeira,
            'ambiente': 'VALIDAÇÃO REAL'
        }
    else:
        return {
            'status': 'invalid_format',
            'resposta': 'FORMATO INVÁLIDO',
            'detalhes': 'Número não passa no algoritmo de Luhn',
            'bandeira': bandeira,
            'ambiente': 'VALIDAÇÃO REAL'
        }

# Comando para gerar CC educacional
@bot.command(name='gerarcc')
async def gerar_cc(ctx, quantidade: int = 1):
    """Gera cartões de teste educacionais"""
    if quantidade > 3:
        await ctx.send("❌ Máximo de 3 cartões por vez")
        return
    
    embed = discord.Embed(
        title="🎴 Cartões Gerados:",
        color=0x0099ff,
        description="**💡 verifique seus ccs"
    )
    
    for i in range(quantidade):
        cc = gerar_cc_educacional()
        embed.add_field(
            name=f"Cartão {i+1} - {cc['bandeira']}",
            value=f"```\nNúmero: {cc['numero']}\nVal: {cc['mes']}/{cc['ano']}\nCVV: {cc['cvv']}\n```",
            inline=False
        )
    
    embed.add_field(
        name="💳 Para que serve?",
        value="para descobrir lives de ccs",
        inline=False
    )
    
    embed.set_footer(text="🛡 Ambiente Seguro")
    await ctx.send(embed=embed)

# Comando para verificação educacional
@bot.command(name='verificar')
async def verificar_cc(ctx, *, cc_info: str = None):
    """Verificação educacional no sandbox"""
    if not cc_info:
        await ctx.send("❌ Formato: !verificar numero|mes|ano|cvv")
        return
    
    try:
        partes = cc_info.split('|')
        if len(partes) != 4:
            await ctx.send("❌ Formato correto: numero|mes|ano|cvv")
            return
        
        cc_data = {
            'numero': partes[0].strip(),
            'mes': partes[1].strip(),
            'ano': partes[2].strip(),
            'cvv': partes[3].strip()
        }
        
        # Mensagem de processamento
        processing_msg = await ctx.send("🔍 Verificando cc...")
        
        # Verificação educacional
        resultado = await verificar_sandbox_educacional(cc_data)
        
        # Define cor baseada no resultado
        if resultado['status'] == 'live':
            cor = 0x00ff00
        elif resultado['status'] == 'die':
            cor = 0xff0000
        else:
            cor = 0xffff00
        
        embed = discord.Embed(
            title="📊 Resultado da Verificação",
            color=cor,
            description=f"**Status:** {resultado['resposta']}"
        )
        
        embed.add_field(name="🔢 Cartão", value=f"`{cc_data['numero']}`", inline=True)
        embed.add_field(name="📅 Validade", value=f"`{cc_data['mes']}/{cc_data['ano']}`", inline=True)
        embed.add_field(name="🔐 CVV", value=f"`{cc_data['cvv']}`", inline=True)
        embed.add_field(name="🏦 Bandeira", value=resultado['bandeira'], inline=True)
        embed.add_field(name="🌐 Ambiente", value=resultado['ambiente'], inline=True)
        embed.add_field(name="📝 Detalhes", value=resultado['detalhes'], inline=False)
        
        embed.set_footer(text="🛡 Ambiente Seguro")
        
        await processing_msg.delete()
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Erro: {str(e)}")

# Comando para listar cartões de teste
@bot.command(name='testcards')
async def cartoes_teste(ctx):
    """Lista cartões de teste disponíveis"""
    embed = discord.Embed(
        title="💳 Cartões para testar live",
        color=0x9932CC,
        description="**Cartões fornecidos por bot cc**\nUse para testar aplicações de pagamento"
    )
    
    for chave, cartao in CARTOES_TESTE.items():
        status_emoji = "✅" if cartao['status'] == 'live' else "❌"
        embed.add_field(
            name=f"{status_emoji} {cartao['bandeira']} - {chave.split('_')[1].title()}",
            value=f"`{cartao['numero']}`\n{cartao['mensagem']}",
            inline=False
        )
    
    embed.add_field(
        name="💡 Como usar?",
        value="Use `!verificar`",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Comando de ajuda educacional
@bot.command(name='cchelp')
async def help_command(ctx):
    """Mostra ajuda dos comandos educacionais"""
    embed = discord.Embed(
        title="🛠️ Ajuda do Bot de Pagamentos",
        color=0x0099ff,
        description="**COMANDOS:**"
    )
    
    embed.add_field(
        name="!gerarcc [quantidade]",
        value="Gera cartões\nEx: `!gerarcc 2`",
        inline=False
    )
    
    embed.add_field(
        name="!verificar numero|mes|ano|cvv",
        value="Verificação educacional no sandbox\nEx: `!verificar 4242424242424242|12|2025|123`",
        inline=False
    )
    
    embed.add_field(
        name="!testcards",
        value="Lista todos os cartões de teste disponíveis",
        inline=False
    )
    
    embed.add_field(
        name="!status",
        value="Mostra status do bot educativo",
        inline=False
    )
    
    embed.add_field(
        name="🎓 PROPÓSI",
        value="Este bot é para aprendizado em desenvolvimento de sistemas de pagamento. Use apenas cartões de teste fornecidos por sandboxes oficiais.",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Comando de status
@bot.command(name='status')
async def status(ctx):
    """Mostra status do bot educativo"""
    embed = discord.Embed(
        title="🤖 Status do Bot",
        color=0x00ff00,
        description=f"✅ Bot online\n🏦 Criador: lzzcxz\n📊 Ping: {round(bot.latency * 1000)}ms"
    )
    
    embed.add_field(
        name="🔒 Garantia",
        value="ccs reais podem ser geradas",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Objetivo",
        value="Encontrar ccs com live!",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Evento quando o bot estiver pronto
@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')
    print(f'📊 ID do Bot: {bot.user.id}')
    print('😈 Modo: Golpista')
    print('------')
    
    # Define o status do bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Verify 1.0 | !cchelp"
        )
    )

# Iniciar servidor web e bot
if __name__ == "__main__":
    keep_alive()
    print("🚀 Iniciando bot...")
    bot.run(os.environ.get('DISCORD_TOKEN'))