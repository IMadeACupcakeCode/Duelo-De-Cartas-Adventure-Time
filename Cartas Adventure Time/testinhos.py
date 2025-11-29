import os
import discord
from discord.ext import commands, tasks
import csv
import datetime
import urllib.parse
import random
import asyncio
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

def log_write(text):
    with open("log.log","a") as log:
        all = "[{}] : \t{}\n".format(str(datetime.datetime.now()),text)
        print(text)
        log.write(all)

log_write("Starting BOT!!!")

TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    log_write("ERROR: DISCORD_TOKEN not found in .env file!")
    exit(1)
if TOKEN == "SEU_TOKEN_AQUI":
    log_write("ERROR: Please set your real Discord token in .env file!")
    exit(1)

log_write(f"Token loaded: {TOKEN[:20]}...")
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix='$', intents=intents)
bot.remove_command('help')

# Armazenar o canal de boas-vindas para cada servidor
welcome_channels = {}

# Carregar cartas do CSV
all_cards = []
with open('./cards.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        if row:  # Evitar linhas vazias
            all_cards.append(row)

def get_card_data(card_name):
    for card in all_cards:
        if card[0] == card_name:
            return card
    return None

# Dicionário para armazenar últimos resultados de busca por usuário
last_search = {}

# Sistema de irritação: conta erros de comando por usuário
user_errors = {}  # user_id: count
IRRIATION_LIMIT = 3  # Após 3 erros, começa a xingar

# Sistema de inatividade: última atividade por canal
last_activity = {}  # channel_id: timestamp
inactive_channels = set()  # Para não enviar múltiplas vezes

# Sistema de duelos
active_duels = {}  # user_id: opponent_id
duel_turns = {}    # user_id: True/False (sua vez)
duel_hp = {}       # user_id: hp
duel_deck = {}     # user_id: list of card names
duel_hand = {}     # user_id: list of card names
duel_board = {}    # user_id: list of summoned creatures (dicts with name, atk, def, etc.)
duel_mana = {}     # user_id: current mana
duel_max_mana = {} # user_id: max mana
duel_graveyard = {} # user_id: list of discarded cards
duel_message_ids = {}  # user_id: message_id do status

def can_send_in_channel(channel):
    """Verifica se o bot pode enviar mensagens no canal."""
    return channel.permissions_for(channel.guild.me).send_messages

def is_welcome_channel(ctx):
    """Verifica se o comando foi executado no canal de boas-vindas."""
    guild_id = ctx.guild.id
    if guild_id in welcome_channels:
        return ctx.channel.id == welcome_channels[guild_id]
    return False

async def send_shutdown_message():
    embed = discord.Embed(description="Toda Terça Têm De Novo, A Parada É Semanal... Falow!", color=0xfff100)
    embed.set_image(url="https://i.imgur.com/FLiISC7.gif")
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if can_send_in_channel(channel):
                try:
                    await channel.send(embed=embed)
                except:
                    pass
    log_write("Bot shutting down...")

@bot.event
async def on_ready():
    log_write('Bot successfully connected to Discord!')
    await bot.change_presence(activity=discord.Game(name='Card Wars'))
    log_write('We have logged in as {0.user}'.format(bot))
    # Enviar mensagem de boas-vindas apenas em canais com palavras-chave relacionadas a cartas
    embed = discord.Embed(title="**🎮 Hora Do Games! Guerra De Cartas, Seus Mangolóides! Ohooooow**", description="O bot tá ligado e pronto pra zoar geral! Use `$help` pra ver os comandos e começar a guerra!", color=0xfff100)
    embed.set_image(url="https://media.tenor.com/tIqmPatn9J0AAAAM/vivian-james-vivian.gif")

    card_keywords = ["cartas", "guerra de cartas", "card wars", "card", "war"]

    for guild in bot.guilds:
        target_channel = None
        # Procurar por canal com palavras-chave relacionadas a cartas no nome
        for channel in guild.text_channels:
            channel_name_lower = channel.name.lower()
            if any(keyword in channel_name_lower for keyword in card_keywords) and can_send_in_channel(channel):
                target_channel = channel
                break

        # Só enviar se encontrou um canal apropriado
        if target_channel:
            try:
                await target_channel.send(embed=embed)
                welcome_channels[guild.id] = target_channel.id  # Armazenar o canal de boas-vindas
                log_write(f"Welcome message sent to {target_channel.name} in {guild.name}")
            except Exception as e:
                log_write(f"Failed to send welcome message to {target_channel.name}: {e}")
        else:
            log_write(f"No suitable channel found in {guild.name} for welcome message")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # Atualizar atividade em todos os canais onde o bot pode ver mensagens
    if can_send_in_channel(message.channel):
        last_activity[message.channel.id] = datetime.datetime.now()
        inactive_channels.discard(message.channel.id)  # Remover se estava inativo
    await bot.process_commands(message)

@tasks.loop(minutes=30)
async def inactivity_check():
    now = datetime.datetime.now()
    for channel_id, last_time in list(last_activity.items()):
        if (now - last_time).total_seconds() > 1800:  # 30 minutos
            if channel_id not in inactive_channels:
                channel = bot.get_channel(channel_id)
                if channel and can_send_in_channel(channel):
                    embed = discord.Embed(description="Toda Terça Têm De Novo, A Parada É Semanal... Falow!", color=0xfff100)
                    embed.set_image(url="https://i.imgur.com/FLiISC7.gif")
                    await channel.send(embed=embed)
                    inactive_channels.add(channel_id)
                    log_write(f"Aviso de inatividade enviado no canal {channel_id}")

@bot.event
async def on_command_error(ctx, error):
    user_id = ctx.author.id
    user_errors[user_id] = user_errors.get(user_id, 0) + 1

    # Frases de erro aleatórias
    error_phrases = [
        "Aprende a escrever certo, energumeno... O comando tá errado!",
        "Seu burro, aprende a digitar direito!",
        "Comando errado, seu analfabeto!",
        "Você é burro demais para usar comandos simples!",
        "Erro no comando, seu imbecil!",
        "Escreve direito, seu ignorante!",
        "Comando inválido, seu idiota!",
        "Você é tão burro que nem comandos consegue usar!",
        "Erro de digitação, seu estúpido!",
        "Aprende a escrever, seu retardado!"
    ]
    await ctx.send(random.choice(error_phrases))
    await ctx.send("https://media.tenor.com/qvvKGZhH0ysAAAAC/anime-girl.gif")

    # Se irritado, adicionar insulto ácido
    if user_errors[user_id] >= IRRIATION_LIMIT:
        irritated_insults = [
            f"{ctx.author.mention}, você é tão burro que até o comando errado você erra!",
            f"{ctx.author.mention}, sua inteligência é zero: nem erro consegue cometer direito!",
            f"{ctx.author.mention}, você é um fracasso ambulante: erra até comandos simples!",
            f"{ctx.author.mention}, sua vida é uma merda, e agora você fede o chat com erros!",
            f"{ctx.author.mention}, você é como Bolsonaro: mente, erra e ainda acha que está certo!",
            f"{ctx.author.mention}, Lula roubou bilhões, mas você rouba minha paciência com erros!",
            f"{ctx.author.mention}, você é tão gordo de burro que nem cabe no chat!",
            f"{ctx.author.mention}, sua mãe deve ter caído na cabeça quando te pariu!",
            f"{ctx.author.mention}, você é um aborto que sobreviveu: erro de nascimento!",
            f"{ctx.author.mention}, seu pau é tão pequeno quanto sua inteligência!"
        ]
        await ctx.send(random.choice(irritated_insults))

    # Tentar sugerir comando similar com embed bonito
    import difflib
    message = ctx.message.content[len(bot.command_prefix):].split()[0] if ctx.message.content.startswith(bot.command_prefix) else ctx.message.content.split()[0]
    commands = [cmd.name for cmd in bot.commands]
    close_matches = difflib.get_close_matches(message, commands, n=1, cutoff=0.6)

    if close_matches:
        # Criar embed elegante para a sugestão
        suggestion_embed = discord.Embed(
            title="💡 **Oops! Comando não encontrado**",
            description=f"Não encontrei o comando `${message}`, mas talvez você quis dizer isso:",
            color=0x3498db
        )

        suggested_command = close_matches[0]
        suggestion_embed.add_field(
            name="🎯 **Sugestão**",
            value=f"```${suggested_command}```",
            inline=False
        )

        # Adicionar contexto irritado se necessário
        if user_errors[user_id] >= IRRIATION_LIMIT:
            suggestion_embed.add_field(
                name="😤 **Dica do Bot**",
                value="Mas como você é burro, provavelmente erra isso também! 😏",
                inline=False
            )
            suggestion_embed.set_footer(text="💀 Pratique mais, campeão!")
        else:
            suggestion_embed.add_field(
                name="✨ **Como usar**",
                value=f"Tente: `${suggested_command} [argumentos]`",
                inline=False
            )
            suggestion_embed.set_footer(text="🤖 Bot criado com ❤️ para Card Wars!")

        await ctx.send(embed=suggestion_embed)
    else:
        # Embed quando não há sugestões
        no_suggestion_embed = discord.Embed(
            title="❓ **Comando não encontrado**",
            description="Não consegui encontrar nenhum comando similar. Use `$help` para ver todos os comandos disponíveis!",
            color=0xe74c3c
        )

        no_suggestion_embed.add_field(
            name="📚 **Precisa de ajuda?**",
            value="Digite `$help` para ver a lista completa de comandos!",
            inline=False
        )

        no_suggestion_embed.set_footer(text="🎮 Guerra De Cartas - Seu bot favorito!")

        await ctx.send(embed=no_suggestion_embed)

    log_write("No arguments given with $c lol")
    log_write("")

@bot.command()
async def help(ctx):
    """Mostra os comandos disponíveis no servidor."""

    embed = discord.Embed(
        title="🎮 **Guerra De Cartas - Comandos Disponíveis**",
        description="Bem-vindo ao bot de Card Wars! Aqui estão todos os comandos disponíveis:",
        color=0xfff100
    )

    embed.add_field(
        name="🔍 **Busca de Cartas**",
        value="`$c [nome da carta]` - Mostra detalhes completos da carta\n"
              "`$img [nome da carta]` - Mostra apenas a imagem da carta\n"
              "`$c [número]` - Seleciona carta de resultados múltiplos\n"
              "`$img [número]` - Seleciona imagem de resultados múltiplos",
        inline=False
    )

    embed.add_field(
        name="⚔️ **Sistema de Duelos**",
        value="`$duel @usuário` - Inicia um duelo com decks aleatórios\n"
              "`$hand` - Mostra sua mão de cartas\n"
              "`$summon [índice]` - Convoca uma criatura da mão\n"
              "`$attack [índice] [alvo]` - Ataca com uma criatura\n"
              "`$draw` - Compra uma carta extra\n"
              "`$board` - Mostra o campo de batalha\n"
              "`$rules` - Mostra as regras do jogo\n"
              "`$endturn` - Passa o turno\n"
              "`$duelstatus` - Mostra HP e turno atual\n"
              "`$endduel` - Encerra o duelo",
        inline=False
    )

    embed.add_field(
        name="🎲 **Comandos de Lazer**",
        value="`$meme` - Envia um meme aleatório\n"
              "`$joke` - Conta uma piada\n"
              "`$insult [@usuário]` - Insulta alguém (aleatório se não marcar)\n"
              "`$quote` - Citação famosa de jogos\n"
              "`$roll [lados] [quantidade]` - Rola dados\n"
              "`$flip` - Cara ou coroa",
        inline=False
    )

    embed.add_field(
        name="💡 **Dicas**",
        value="• Use aspas para busca exata: `$c \"Jake\"`\n"
              "• Limite de 24 resultados por busca\n"
              "• Comandos funcionam em qualquer canal!",
        inline=False
    )

    embed.set_footer(text="Bot criado com ❤️ para amantes de Card Wars!")

    await ctx.send(embed=embed)

def search_cards(query, user_id):
    """Função auxiliar para buscar cartas no CSV."""
    with open('./cards.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')

        search = []
        if query.startswith('"') and query.endswith('"'):
            query_clean = query.replace('"', "").lower()
            for row in reader:
                if query_clean == row[0].lower():
                    search.append(row)
        else:
            for row in reader:
                if query.lower() in row[0].lower():
                    search.append(row)

        return search

def create_card_embed(card_data):
    """Função auxiliar para criar embed de carta."""
    embed = discord.Embed(color=0xfff100)
    embed.set_author(name=card_data[0], icon_url=os.getenv('BOT_ICON_URL'))
    embed.add_field(name="Baralho / Quantidade", value=card_data[8].rstrip(), inline=False)
    embed.set_thumbnail(url=os.getenv('CARD_IMAGES_URL').format(urllib.parse.quote(card_data[0])))

    card_type = card_data[2].rstrip()
    if card_type == "Creature":
        embed.add_field(name="Paisagem", value=card_data[3].rstrip(), inline=True)
        embed.add_field(name="Tipo", value=card_type, inline=True)
        embed.add_field(name="Custo", value=card_data[4].rstrip(), inline=True)
        embed.add_field(name="ATA", value=card_data[5].rstrip(), inline=True)
        embed.add_field(name="DEF", value=card_data[6].rstrip(), inline=True)
        embed.add_field(name="Descrição", value=card_data[1].rstrip(), inline=True)

    elif card_type in ["Spell", "Building", "Teamwork"]:
        embed.add_field(name="Paisagem", value=card_data[3].rstrip(), inline=True)
        embed.add_field(name="Tipo", value=card_type, inline=True)
        embed.add_field(name="Custo", value=card_data[4].rstrip(), inline=True)
        embed.add_field(name="Descrição", value=card_data[1].rstrip(), inline=True)

    elif card_type == "Hero":
        embed.add_field(name="Tipo", value=card_type, inline=True)
        embed.add_field(name="Descrição", value=card_data[1].rstrip(), inline=True)

    embed.add_field(name="Relatar um problema:", value=f"Mensagem <@!{os.getenv('OWNER_ID')}>", inline=True)
    return embed

@bot.command()
async def c(ctx, *, arg):
    user_id = ctx.author.id

    # Verificar se é seleção por número de resultados múltiplos
    if arg.isdigit() and user_id in last_search:
        num = int(arg) - 1
        if 0 <= num < len(last_search[user_id]):
            card_data = last_search[user_id][num]
            embed = create_card_embed(card_data)
            await ctx.send(file=discord.File(f"./images/{card_data[0]}.jpg"))
            await ctx.send(embed=embed)
            log_write(f"Carta {card_data[0]} mostrada (seleção por número)")
        else:
            await ctx.send(f"Número inválido. Use um número entre 1 e {len(last_search[user_id])}.")
        return

    # Buscar carta por nome
    search_results = search_cards(arg, user_id)

    if len(search_results) == 0:
        embed = discord.Embed(
            title="🔍 **Nenhum resultado encontrado**",
            description=f"Não encontrei nenhuma carta com o nome '{arg}'. Tente novamente!",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
        log_write(f"Busca por '{arg}' - Nenhum resultado")

    elif len(search_results) > 24:
        embed = discord.Embed(
            title="⚠️ **Muitos resultados**",
            description=f"Sua busca retornou {len(search_results)} cartas. Seja mais específico!",
            color=0xf39c12
        )
        await ctx.send(embed=embed)
        log_write(f"Busca por '{arg}' - Muitos resultados ({len(search_results)})")

    elif len(search_results) > 1:
        embed = discord.Embed(
            title="📋 **Múltiplos Resultados**",
            description="Encontrei várias cartas. Selecione uma:",
            color=0x3498db
        )

        result_list = ""
        for i, card in enumerate(search_results[:10], 1):  # Mostrar apenas os primeiros 10
            result_list += f"{i}. {card[0]}\n"
        if len(search_results) > 10:
            result_list += f"... e mais {len(search_results) - 10} cartas"

        embed.add_field(name="Cartas encontradas:", value=result_list, inline=False)
        embed.add_field(
            name="Como escolher:",
            value='Use `$c [número]` para ver detalhes ou `$img [número]` para ver apenas a imagem',
            inline=False
        )
        await ctx.send(embed=embed)
        last_search[user_id] = search_results
        log_write(f"Busca por '{arg}' - {len(search_results)} resultados")

    else:  # len(search_results) == 1
        card_data = search_results[0]
        embed = create_card_embed(card_data)
        await ctx.send(file=discord.File(f"./images/{card_data[0]}.jpg"))
        await ctx.send(embed=embed)
        log_write(f"Carta {card_data[0]} mostrada")

@bot.command()
async def img(ctx, *, arg):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    user_id = ctx.author.id

    # Verificar se é seleção por número de resultados múltiplos
    if arg.isdigit() and user_id in last_search:
        num = int(arg) - 1
        if 0 <= num < len(last_search[user_id]):
            card_data = last_search[user_id][num]
            await ctx.send(file=discord.File(f"./images/{card_data[0]}.jpg"))
            log_write(f"Imagem de {card_data[0]} enviada (seleção por número)")
        else:
            await ctx.send(f"Número inválido. Use um número entre 1 e {len(last_search[user_id])}.")
        return

    # Buscar carta por nome
    search_results = search_cards(arg, user_id)

    if len(search_results) == 0:
        embed = discord.Embed(
            title="🔍 **Nenhuma imagem encontrada**",
            description=f"Não encontrei nenhuma carta com o nome '{arg}'. Tente novamente!",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
        log_write(f"Busca de imagem por '{arg}' - Nenhum resultado")

    elif len(search_results) > 24:
        embed = discord.Embed(
            title="⚠️ **Muitas imagens**",
            description=f"Sua busca retornou {len(search_results)} cartas. Seja mais específico!",
            color=0xf39c12
        )
        await ctx.send(embed=embed)
        log_write(f"Busca de imagem por '{arg}' - Muitos resultados ({len(search_results)})")

    elif len(search_results) > 1:
        embed = discord.Embed(
            title="📋 **Múltiplas Imagens**",
            description="Encontrei várias cartas. Selecione uma:",
            color=0x3498db
        )

        result_list = ""
        for i, card in enumerate(search_results[:10], 1):  # Mostrar apenas os primeiros 10
            result_list += f"{i}. {card[0]}\n"
        if len(search_results) > 10:
            result_list += f"... e mais {len(search_results) - 10} cartas"

        embed.add_field(name="Cartas encontradas:", value=result_list, inline=False)
        embed.add_field(
            name="Como escolher:",
            value='Use `$c [número]` para ver detalhes ou `$img [número]` para ver apenas a imagem',
            inline=False
        )
        await ctx.send(embed=embed)
        last_search[user_id] = search_results
        log_write(f"Busca de imagem por '{arg}' - {len(search_results)} resultados")

    else:  # len(search_results) == 1
        card_data = search_results[0]
        await ctx.send(file=discord.File(f"./images/{card_data[0]}.jpg"))
        # Descrição opcional
        desc_embed = discord.Embed(
            title=f"📖 Descrição de {card_data[0]}",
            description=card_data[1].rstrip() if card_data[1] else "Sem descrição.",
            color=0xfff100
        )
        await ctx.send(embed=desc_embed)
        log_write(f"Imagem de {card_data[0]} enviada")

# ========== COMANDOS DE DUELO ==========

@bot.command()
async def duel(ctx, opponent: discord.Member = None):
    if opponent is None:
        await ctx.send("❌ Você precisa mencionar um oponente! Use: `$duel @usuário`")
        return

    if opponent == ctx.author:
        await ctx.send("❌ Você não pode duelar contra si mesmo!")
        return

    if opponent.bot:
        await ctx.send("❌ Você não pode duelar contra bots!")
        return

    user_id = ctx.author.id
    opponent_id = opponent.id

    # Verificar se já está em duelo
    if user_id in active_duels or opponent_id in active_duels:
        await ctx.send("❌ Um dos jogadores já está em um duelo!")
        return

    # Iniciar duelo
    active_duels[user_id] = opponent_id
    active_duels[opponent_id] = user_id
    duel_turns[user_id] = True  # Jogador que iniciou começa
    duel_turns[opponent_id] = False
    duel_hp[user_id] = 20
    duel_hp[opponent_id] = 20
    duel_mana[user_id] = 1
    duel_mana[opponent_id] = 1
    duel_max_mana[user_id] = 1
    duel_max_mana[opponent_id] = 1

    # Decks aleatórios simples (usando cartas disponíveis)
    all_card_names = [card[0] for card in all_cards[:30]]  # Usar primeiras 30 cartas
    duel_deck[user_id] = random.sample(all_card_names, 20)
    duel_deck[opponent_id] = random.sample(all_card_names, 20)

    # Mãos iniciais
    duel_hand[user_id] = random.sample(duel_deck[user_id], 3)
    duel_hand[opponent_id] = random.sample(duel_deck[opponent_id], 3)

    # Remover cartas da mão do deck
    for card in duel_hand[user_id]:
        duel_deck[user_id].remove(card)
    for card in duel_hand[opponent_id]:
        duel_deck[opponent_id].remove(card)

    duel_board[user_id] = []
    duel_board[opponent_id] = []
    duel_graveyard[user_id] = []
    duel_graveyard[opponent_id] = []

    embed = discord.Embed(
        title="⚔️ **DUELO INICIADO!** ⚔️",
        description=f"{ctx.author.mention} desafiou {opponent.mention} para um duelo!",
        color=0xff0000
    )
    embed.add_field(name=f"{ctx.author.display_name}", value=f"❤️ HP: {duel_hp[user_id]}\n🔵 Mana: {duel_mana[user_id]}/{duel_max_mana[user_id]}", inline=True)
    embed.add_field(name=f"{opponent.display_name}", value=f"❤️ HP: {duel_hp[opponent_id]}\n🔵 Mana: {duel_mana[opponent_id]}/{duel_max_mana[opponent_id]}", inline=True)
    embed.add_field(name="🎯 Vez de:", value=f"{ctx.author.mention}", inline=False)
    embed.set_footer(text="Use $hand para ver suas cartas | $rules para ver as regras")

    await ctx.send(embed=embed)
    log_write(f"Duelo iniciado: {ctx.author.name} vs {opponent.name}")

@bot.command()
async def hand(ctx):
    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo! Use `$duel @usuário` para iniciar um.")
        return

    hand_cards = duel_hand[user_id]
    if not hand_cards:
        await ctx.author.send("❌ Sua mão está vazia!")
        return

    embed = discord.Embed(
        title="🃏 **Sua Mão**",
        description=f"Você tem {len(hand_cards)} cartas na mão:",
        color=0xfff100
    )

    for i, card_name in enumerate(hand_cards, 1):
        card_data = get_card_data(card_name)
        cost = card_data[4] if card_data else "?"
        embed.add_field(name=f"{i}. {card_name}", value=f"Custo: {cost}", inline=True)

    embed.add_field(name="💡 Como usar:", value="$summon [número] para invocar\n$endturn para passar turno", inline=False)

    await ctx.author.send(embed=embed)

@bot.command()
async def summon(ctx, card_index: int = None):
    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo!")
        return

    if not duel_turns[user_id]:
        await ctx.send("❌ Não é sua vez!")
        return

    if card_index is None or card_index < 1 or card_index > len(duel_hand[user_id]):
        await ctx.send(f"❌ Número inválido! Use um número entre 1 e {len(duel_hand[user_id])}.")
        return

    card_name = duel_hand[user_id][card_index - 1]

    card_data = get_card_data(card_name)
    mana_cost = int(card_data[4]) if card_data else len(card_name) // 3 + 1
    if duel_mana[user_id] < mana_cost:
        await ctx.send(f"❌ Você não tem mana suficiente! Precisa de {mana_cost} mana, você tem {duel_mana[user_id]}.")
        return

    # Invocar carta
    duel_mana[user_id] -= mana_cost
    duel_hand[user_id].remove(card_name)

    # Criar criatura simples
    creature = {
        'name': card_name,
        'atk': int(card_data[5]) if card_data else random.randint(1, 5),
        'def': int(card_data[6]) if card_data else random.randint(1, 5)
    }
    duel_board[user_id].append(creature)

    embed = discord.Embed(
        title="🪄 **Carta Invocada!**",
        description=f"{ctx.author.mention} invocou **{card_name}**!",
        color=0xfff100
    )
    embed.add_field(name="Nome:", value=card_name, inline=True)
    embed.add_field(name="ATK:", value=creature['atk'], inline=True)
    embed.add_field(name="DEF:", value=creature['def'], inline=True)
    embed.add_field(name="Mana restante:", value=f"{duel_mana[user_id]}/{duel_max_mana[user_id]}", inline=False)
    if card_data:
        embed.set_thumbnail(url=os.getenv('CARD_IMAGES_URL').format(urllib.parse.quote(card_name)))

    await ctx.send(embed=embed)
    log_write(f"{ctx.author.name} invocou {card_name}")

@bot.command()
async def attack(ctx, creature_index: int = None, target: str = None):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo!")
        return

    if not duel_turns[user_id]:
        await ctx.send("❌ Não é sua vez!")
        return

    if not duel_board[user_id]:
        await ctx.send("❌ Você não tem criaturas no campo!")
        return

    if creature_index is None or creature_index < 1 or creature_index > len(duel_board[user_id]):
        await ctx.send(f"❌ Número inválido! Use um número entre 1 e {len(duel_board[user_id])}.")
        return

    creature = duel_board[user_id][creature_index - 1]
    opponent_id = active_duels[user_id]

    if target == "player" or target is None:
        # Atacar jogador diretamente
        duel_hp[opponent_id] -= creature['atk']
        embed = discord.Embed(
            title="⚔️ **Ataque Direto!**",
            description=f"{ctx.author.mention} atacou {ctx.guild.get_member(opponent_id).mention} diretamente!",
            color=0xe74c3c
        )
        embed.add_field(name="Dano causado:", value=f"❤️ -{creature['atk']} HP", inline=True)
        embed.add_field(name="HP restante do oponente:", value=f"❤️ {duel_hp[opponent_id]}", inline=True)
    else:
        await ctx.send("❌ Use `$attack [número] player` para atacar o oponente diretamente.")
        return

    await ctx.send(embed=embed)

    # Verificar se alguém ganhou
    if duel_hp[opponent_id] <= 0:
        winner = ctx.author
        loser = ctx.guild.get_member(opponent_id)

        embed_win = discord.Embed(
            title="🏆 **VITÓRIA!** 🏆",
            description=f"{winner.mention} venceu o duelo contra {loser.mention}!",
            color=0xf1c40f
        )
        await ctx.send(embed=embed_win)

        # Limpar duelo
        cleanup_duel(user_id, opponent_id)
        log_write(f"Duelo terminado: {winner.name} venceu")
    else:
        log_write(f"{ctx.author.name} atacou diretamente causando {creature['atk']} de dano")

@bot.command()
async def draw(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo!")
        return

    if not duel_turns[user_id]:
        await ctx.send("❌ Não é sua vez!")
        return

    if not duel_deck[user_id]:
        await ctx.send("❌ Seu deck está vazio!")
        return

    # Comprar uma carta
    new_card = random.choice(duel_deck[user_id])
    duel_hand[user_id].append(new_card)
    duel_deck[user_id].remove(new_card)

    embed = discord.Embed(
        title="🃏 **Carta Comprada!**",
        description=f"{ctx.author.mention} comprou uma carta!",
        color=0xfff100
    )
    embed.add_field(name="Carta:", value=new_card, inline=False)
    embed.add_field(name="Cartas na mão agora:", value=len(duel_hand[user_id]), inline=True)

    await ctx.author.send(embed=embed)
    log_write(f"{ctx.author.name} comprou {new_card}")

@bot.command()
async def board(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo!")
        return

    opponent_id = active_duels[user_id]

    embed = discord.Embed(
        title="🏟️ **Campo de Batalha**",
        color=0x27ae60
    )

    # Suas criaturas
    if duel_board[user_id]:
        your_creatures = ""
        for i, creature in enumerate(duel_board[user_id], 1):
            your_creatures += f"{i}. {creature['name']} (ATK: {creature['atk']}, DEF: {creature['def']})\n"
        embed.add_field(name=f"🛡️ Criaturas de {ctx.author.display_name}", value=your_creatures, inline=False)
    else:
        embed.add_field(name=f"🛡️ Criaturas de {ctx.author.display_name}", value="Nenhuma criatura no campo", inline=False)

    # Criaturas do oponente
    if duel_board[opponent_id]:
        opp_creatures = ""
        for i, creature in enumerate(duel_board[opponent_id], 1):
            opp_creatures += f"{i}. {creature['name']} (ATK: {creature['atk']}, DEF: {creature['def']})\n"
        embed.add_field(name=f"⚔️ Criaturas de {ctx.guild.get_member(opponent_id).display_name}", value=opp_creatures, inline=False)
    else:
        embed.add_field(name=f"⚔️ Criaturas de {ctx.guild.get_member(opponent_id).display_name}", value="Nenhuma criatura no campo", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def rules(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    embed = discord.Embed(
        title="📜 **Regras do Duelo - Guerra De Cartas**",
        description="Bem-vindo ao sistema de duelos! Aqui estão as regras básicas:",
        color=0x8e44ad
    )

    embed.add_field(
        name="🎯 **Objetivo**",
        value="Reduza o HP do oponente a 0 para vencer!",
        inline=False
    )

    embed.add_field(
        name="🔵 **Mana**",
        value="• Comece com 1 mana\n• Ganhe 1 mana máxima por turno\n• Use mana para invocar cartas",
        inline=False
    )

    embed.add_field(
        name="🃏 **Cartas**",
        value="• Cada jogador começa com 3 cartas\n• Custo de mana baseado no nome da carta\n• Invocação consome mana",
        inline=False
    )

    embed.add_field(
        name="⚔️ **Combate**",
        value="• `$summon [número]` - Invocar criatura\n• `$attack [número] player` - Atacar oponente\n• `$endturn` - Passar turno",
        inline=False
    )

    embed.add_field(
        name="🎲 **Turnos**",
        value="• Alternem turnos\n• Oponente ganha mana e compra carta no seu turno\n• Use `$duelstatus` para ver o estado",
        inline=False
    )

    embed.set_footer(text="Divirta-se duelando! 🃏⚔️")

    await ctx.send(embed=embed)

@bot.command()
async def endturn(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo!")
        return

    if not duel_turns[user_id]:
        await ctx.send("❌ Não é sua vez!")
        return

    opponent_id = active_duels[user_id]

    # Passar turno
    duel_turns[user_id] = False
    duel_turns[opponent_id] = True

    # Aumentar mana máxima do oponente e dar mana cheia
    duel_max_mana[opponent_id] += 1
    duel_mana[opponent_id] = duel_max_mana[opponent_id]

    # Oponente compra uma carta
    if duel_deck[opponent_id]:
        new_card = random.choice(duel_deck[opponent_id])
        duel_hand[opponent_id].append(new_card)
        duel_deck[opponent_id].remove(new_card)

    embed = discord.Embed(
        title="🔄 **Turno Passado!**",
        description=f"Agora é a vez de {ctx.guild.get_member(opponent_id).mention}!",
        color=0x2ecc71
    )
    embed.add_field(
        name=f"Vez de {ctx.guild.get_member(opponent_id).display_name}:",
        value=f"🔵 Mana: {duel_mana[opponent_id]}/{duel_max_mana[opponent_id]}\n🃏 Cartas na mão: {len(duel_hand[opponent_id])}",
        inline=False
    )

    await ctx.send(embed=embed)
    log_write(f"{ctx.author.name} passou o turno para {ctx.guild.get_member(opponent_id).name}")

@bot.command()
async def duelstatus(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo!")
        return

    opponent_id = active_duels[user_id]

    embed = discord.Embed(
        title="📊 **Status do Duelo**",
        color=0xfff100
    )

    embed.add_field(
        name=f"❤️ {ctx.author.display_name}",
        value=f"HP: {duel_hp[user_id]}\nMana: {duel_mana[user_id]}/{duel_max_mana[user_id]}\nCartas na mão: {len(duel_hand[user_id])}\nCriaturas no campo: {len(duel_board[user_id])}",
        inline=True
    )

    embed.add_field(
        name=f"❤️ {ctx.guild.get_member(opponent_id).display_name}",
        value=f"HP: {duel_hp[opponent_id]}\nMana: {duel_mana[opponent_id]}/{duel_max_mana[opponent_id]}\nCartas na mão: {len(duel_hand[opponent_id])}\nCriaturas no campo: {len(duel_board[opponent_id])}",
        inline=True
    )

    current_player = ctx.author.display_name if duel_turns[user_id] else ctx.guild.get_member(opponent_id).display_name
    embed.add_field(name="🎯 Vez atual:", value=current_player, inline=False)

    await ctx.author.send(embed=embed)

@bot.command()
async def endduel(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    user_id = ctx.author.id
    if user_id not in active_duels:
        await ctx.send("❌ Você não está em um duelo!")
        return

    opponent_id = active_duels[user_id]
    opponent = ctx.guild.get_member(opponent_id)

    embed = discord.Embed(
        title="🏁 **Duelo Encerrado**",
        description=f"{ctx.author.mention} encerrou o duelo contra {opponent.mention}.",
        color=0x95a5a6
    )

    await ctx.send(embed=embed)

    # Limpar duelo
    cleanup_duel(user_id, opponent_id)
    log_write(f"Duelo encerrado por {ctx.author.name}")

def cleanup_duel(user_id, opponent_id):
    """Limpa os dados do duelo."""
    for uid in [user_id, opponent_id]:
        if uid in active_duels:
            del active_duels[uid]
        if uid in duel_turns:
            del duel_turns[uid]
        if uid in duel_hp:
            del duel_hp[uid]
        if uid in duel_mana:
            del duel_mana[uid]
        if uid in duel_max_mana:
            del duel_max_mana[uid]
        if uid in duel_deck:
            del duel_deck[uid]
        if uid in duel_hand:
            del duel_hand[uid]
        if uid in duel_board:
            del duel_board[uid]
        if uid in duel_graveyard:
            del duel_graveyard[uid]
        if uid in duel_message_ids:
            del duel_message_ids[uid]

# ========== COMANDOS DE LAZER ==========

@bot.command()
async def meme(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    # Lista todos os arquivos da pasta memes
    memes_path = "./memes"
    try:
        all_files = os.listdir(memes_path)
        # Filtra apenas arquivos de imagem/vídeo suportados
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4']
        meme_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in image_extensions)]

        if not meme_files:
            embed = discord.Embed(
                title="😔 **Sem Memes**",
                description="Não encontrei nenhum meme na pasta!",
                color=0xe74c3c
            )
            await ctx.send(embed=embed)
            return

        # Seleciona um meme aleatório
        selected_meme = random.choice(meme_files)
        meme_path = os.path.join(memes_path, selected_meme)

        # Cria embed baseado no tipo de arquivo
        embed = discord.Embed(
            title="😂 **Meme Aleatório**",
            description=f"Arquivo: `{selected_meme}`",
            color=0xffd700
        )

        # Verifica se é vídeo ou imagem
        if selected_meme.lower().endswith('.mp4'):
            # Para vídeos, envia o arquivo diretamente
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File(meme_path))
        else:
            # Para imagens/GIFs, usa o embed
            embed.set_image(url=f"attachment://{selected_meme}")
            await ctx.send(embed=embed, file=discord.File(meme_path))

        log_write(f"Meme '{selected_meme}' enviado por {ctx.author.name}")

    except Exception as e:
        embed = discord.Embed(
            title="❌ **Erro**",
            description="Ocorreu um erro ao buscar memes!",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
        log_write(f"Erro ao enviar meme: {e}")

@bot.command()
async def joke(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    jokes = [
        "Por que o computador foi ao médico? Porque tinha vírus! 🦠",
        "O que o pato disse para a pata? Vem quá! 🦆",
        "Por que o livro de matemática estava triste? Porque tinha muitos problemas! 📚",
        "O que é que tem 4 patas e voa? Duas galinhas! 🐔",
        "Por que o esqueleto não brigou com ninguém? Porque não tinha estômago para isso! 💀"
    ]

    embed = discord.Embed(
        title="😂 **Piada Aleatória**",
        description=random.choice(jokes),
        color=0xffd700
    )

    await ctx.send(embed=embed)
    log_write(f"Piada enviada por {ctx.author.name}")

@bot.command()
async def insult(ctx, target: discord.Member = None):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    insults = [
        "é mais burro que uma porta!",
        "tem QI de uma planta!",
        "é tão feio que assusta espelho!",
        "é mais lento que tartaruga carregando piano!",
        "é tão chato que aborrece até bocejo!",
        "é mais inútil que guarda-chuva no deserto!",
        "é tão gordo que precisa de mapa pra se encontrar!",
        "é mais velho que a invenção da roda!",
        "é tão pobre que pede esmola pro mendigo!",
        "é mais sujo que gambá no lixo!"
    ]

    if target is None:
        target = ctx.author
        embed = discord.Embed(
            title="😈 **Auto-Insulto**",
            description=f"{target.mention} {random.choice(insults)} 🤡",
            color=0x8b4513
        )
    else:
        embed = discord.Embed(
            title="😈 **Insulto**",
            description=f"{target.mention} {random.choice(insults)} 🤡",
            color=0x8b4513
        )

    await ctx.send(embed=embed)
    log_write(f"Insulto enviado por {ctx.author.name} para {target.name}")

@bot.command()
async def quote(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    quotes = [
        "\"A vida é como um jogo, mas alguns preferem ficar assistindo.\" - Mestre dos Games",
        "\"Quem ri por último, ri melhor. Mas quem ri primeiro, ri mais.\" - Palhaço Sábio",
        "\"O importante não é vencer todos os dias, mas lutar todos os dias.\" - Lutador Anônimo",
        "\"A preguiça é a mãe de todos os vícios, mas é uma ótima companhia.\" - Preguiçoso Filosofo",
        "\"Se a vida te dá limões, faça uma limonada. Se der abacaxis, faça suco.\" - Cozinheiro Otimista"
    ]

    embed = discord.Embed(
        title="💭 **Citação Inspiradora**",
        description=random.choice(quotes),
        color=0x9370db
    )

    await ctx.send(embed=embed)
    log_write(f"Citação enviada por {ctx.author.name}")

@bot.command()
async def roll(ctx, sides: int = 6, count: int = 1):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    if sides < 2 or sides > 100:
        await ctx.send("❌ Número de lados deve ser entre 2 e 100!")
        return

    if count < 1 or count > 10:
        await ctx.send("❌ Número de dados deve ser entre 1 e 10!")
        return

    results = [random.randint(1, sides) for _ in range(count)]
    total = sum(results)

    embed = discord.Embed(
        title="🎲 **Resultado dos Dados**",
        color=0x32cd32
    )

    if count == 1:
        embed.add_field(name=f"Dado de {sides} lados:", value=f"**{results[0]}**", inline=False)
    else:
        embed.add_field(name=f"{count} dados de {sides} lados:", value=f"Resultados: {', '.join(map(str, results))}\n**Total: {total}**", inline=False)

    await ctx.send(embed=embed)
    log_write(f"Dados rolados por {ctx.author.name}: {results} (total: {total})")

@bot.command()
async def flip(ctx):
    if not is_welcome_channel(ctx):
        await ctx.send("❌ Os comandos só funcionam no canal de boas-vindas do bot!")
        return

    result = random.choice(["Cara", "Coroa"])
    emoji = "🪙" if result == "Cara" else "👑"

    embed = discord.Embed(
        title="🪙 **Cara ou Coroa**",
        description=f"O resultado é: **{result}** {emoji}!",
        color=0xffd700
    )

    await ctx.send(embed=embed)
    log_write(f"Cara ou coroa por {ctx.author.name}: {result}")

# Tratamento de erros de login
try:
    bot.run(TOKEN)
except discord.LoginFailure as e:
    log_write(f"ERROR: Falha no login - Token inválido ou expirado: {e}")
    print("ERRO: Token do Discord inválido! Verifique o arquivo .env")
except Exception as e:
    log_write(f"ERROR: Erro ao conectar bot: {e}")
    print(f"ERRO: Falha ao conectar bot: {e}")
