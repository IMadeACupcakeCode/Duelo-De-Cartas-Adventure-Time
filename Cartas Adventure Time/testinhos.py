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

# Importar DuelManager
from duel_manager import DuelManager, get_rules_embed

# Instanciar DuelManager
duel_manager = DuelManager(all_cards, get_card_data)

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

    embed = duel_manager.start_duel(ctx, opponent)
    await ctx.send(embed=embed)

@bot.command()
async def hand(ctx):
    embed = duel_manager.get_hand_embed(ctx.author.id)
    await ctx.author.send(embed=embed)

@bot.command()
async def summon(ctx, *, card_identifier: str = None):
    if not card_identifier:
        await ctx.send("❌ Especifique o número ou nome da carta entre aspas! Ex: `$summon 1` ou `$summon \"Nome da Carta\"`")
        return
    result = duel_manager.summon_card(ctx, card_identifier)
    if isinstance(result, str):
        await ctx.send(result)
    else:
        await ctx.send(embed=result)

@bot.command()
async def attack(ctx, creature_index: int = None, target: str = None):
    if target != "player" and target is not None:
        await ctx.send("❌ Use `$attack [número] player` para atacar o oponente diretamente.")
        return
    embed = duel_manager.attack_player(ctx, creature_index)
    await ctx.send(embed=embed)

@bot.command()
async def draw(ctx):
    result = duel_manager.draw_card(ctx)
    if isinstance(result, str):
        await ctx.send(result)
    else:
        await ctx.author.send(embed=result)

@bot.command()
async def board(ctx):
    embed = duel_manager.get_board_embed(ctx)
    if isinstance(embed, str):
        await ctx.send(embed)
    else:
        await ctx.send(embed=embed)

@bot.command()
async def rules(ctx):
    embed = get_rules_embed()
    await ctx.send(embed=embed)

@bot.command()
async def endturn(ctx):
    result = duel_manager.end_turn(ctx)
    if isinstance(result, str):
        await ctx.send(result)
    else:
        await ctx.send(embed=result)

@bot.command()
async def duelstatus(ctx):
    embed = duel_manager.get_status_embed(ctx)
    if isinstance(embed, str):
        await ctx.send(embed)
    else:
        await ctx.author.send(embed=embed)

@bot.command()
async def endduel(ctx):
    result = duel_manager.end_duel(ctx)
    if isinstance(result, str):
        await ctx.send(result)
    else:
        await ctx.send(embed=result)

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
