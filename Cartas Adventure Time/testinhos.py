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

# Carregar cartas do CSV
all_cards = []
with open('./cards.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        if row:  # Evitar linhas vazias
            all_cards.append(row)

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

    # Tentar sugerir comando similar
    import difflib
    message = ctx.message.content[len(bot.command_prefix):].split()[0] if ctx.message.content.startswith(bot.command_prefix) else ctx.message.content.split()[0]
    commands = [cmd.name for cmd in bot.commands]
    close_matches = difflib.get_close_matches(message, commands, n=1, cutoff=0.6)
    if close_matches:
        suggestion = f"Talvez você quis dizer: `${close_matches[0]}`?"
        if user_errors[user_id] >= IRRIATION_LIMIT:
            suggestion += f" Mas como você é burro, provavelmente erra isso também!"
        await ctx.send(suggestion)
    else:
        await ctx.send("Comandos disponíveis: $help")

    log_write("No arguments given with $c lol")
    log_write("")

@bot.command()
async def c(ctx, *, arg):
    embed = discord.Embed(color=0xfff100)
    user_id = ctx.author.id

    # Verificar se é seleção por número
    if arg.isdigit() and user_id in last_search:
        num = int(arg) - 1
        if 0 <= num < len(last_search[user_id]):
            returned_card = last_search[user_id][num]
            # Mostrar a carta selecionada
            embed = discord.Embed(color=0xfff100)
            embed.set_author(name=returned_card[0], icon_url=os.getenv('BOT_ICON_URL'))
            embed.add_field(name="Baralho / Quantidade", value=returned_card[8].rstrip(), inline=False)
            embed.set_thumbnail(url=os.getenv('CARD_IMAGES_URL').format(urllib.parse.quote(returned_card[0])))

            if (returned_card[2].rstrip() == "Creature"):
                embed.add_field(name="Paisagem", value=returned_card[3].rstrip(), inline=True)
                embed.add_field(name="Tipo", value=returned_card[2].rstrip(), inline=True)
                embed.add_field(name="Custo", value=returned_card[4].rstrip(), inline=True)
                embed.add_field(name="ATA", value=returned_card[5].rstrip(), inline=True)
                embed.add_field(name="DEF", value=returned_card[6].rstrip(), inline=True)
                embed.add_field(name="Descrição", value=returned_card[1].rstrip(), inline=True)

            if (returned_card[2].rstrip() == "Spell" or returned_card[2].rstrip() == "Building" or returned_card[2].rstrip() == "Teamwork"):
                embed.add_field(name="Paisagem", value=returned_card[3].rstrip(), inline=True)
                embed.add_field(name="Tipo", value=returned_card[2].rstrip(), inline=True)
                embed.add_field(name="Custo", value=returned_card[4].rstrip(), inline=True)
                embed.add_field(name="Descrição", value=returned_card[1].rstrip(), inline=True)

            if (returned_card[2].rstrip() == "Hero"):
                embed.add_field(name="Tipo", value=returned_card[2].rstrip(), inline=True)
                embed.add_field(name="Descrição", value=returned_card[1].rstrip(), inline=True)

            embed.add_field(name="Relatar um problema: ", value=f"Mensagem <@!{os.getenv('OWNER_ID')}>", inline=True)
            await ctx.send(file=discord.File(f"./images/{returned_card[0]}.jpg"))
            await ctx.send(embed=embed)
            log_write(returned_card[0])
            log_write("")

@bot.command()
async def img(ctx, *, arg):
    embed = discord.Embed(color=0xfff100)
    user_id = ctx.author.id

    # Verificar se é seleção por número
    if arg.isdigit() and user_id in last_search:
        num = int(arg) - 1
        if 0 <= num < len(last_search[user_id]):
            returned_card = last_search[user_id][num]
            await ctx.send(file=discord.File("./images/{}.jpg".format(returned_card[0])))
            log_write("Imagem de {} enviada".format(returned_card[0]))
            return
        else:
            await ctx.send("Número inválido. Use um número entre 1 e {}.".format(len(last_search[user_id])))
            return

    with open('./cards.csv') as cfile:
        csv_file = csv.reader(cfile, delimiter=',',quotechar='"')
        # Find card and return value
        log_write("{1} \timg {0}".format(arg,ctx.message.author))

        search=[]
        if (arg.startswith('"') and arg.endswith('"')):
            arg_clean = arg.replace('"',"").lower()
            for row in csv_file:
                if arg_clean == row[0].lower():
                    search.append(row)
        else:
            for row in csv_file:
                if arg.lower() in row[0].lower():
                    search.append(row)

        if len(search) != 1:
            if len(search) == 0:
                embed.set_author(name="Nenhum resultado encontrado, tente novamente.".format(str(len(search))))
                await ctx.send(embed=embed)
                log_write("Call for {} cards.".format(str(len(search))))
                return

            if len(search) > 24:
                embed.set_author(name="Essa busca excede o limite ({} cartas retornadas). Seja mais específico.".format(str(len(search))))
                await ctx.send(embed=embed)
                log_write("Call for {} cards.".format(str(len(search))))
                return

            if len(search) > 1:
                embed.set_author(name="Múltiplos Resultados:")

                x=1
                for ting in search:
                    embed.add_field(name=str(x)+".", value=ting[0], inline=False)
                    x+=1

                embed.add_field(name="Dica Quente", value='Use `$img [número]` para selecionar uma carta. Ou insira aspas para busca mais específica, ex "Jake"', inline=False)
                await ctx.send(embed=embed)
                last_search[user_id] = search  # Salvar para seleção posterior
                log_write("Mulitple ({}) Results found".format(str(len(search))))

        if len(search) == 1:
            returned_card=search[0]

            await ctx.send(file=discord.File("./images/{}.jpg".format(returned_card[0])))
            # Enviar descrição em português
            embed = discord.Embed(title=f"📖 Descrição de {returned_card[0]}", description=returned_card[1].rstrip() if returned_card[1] else "Sem descrição.", color=0xfff100)
            await ctx.send(embed=embed)
            print(','.join(str(v) for v in search))
            log_write("")
            return
        else:
            await ctx.send("Número inválido. Use um número entre 1 e {}.".format(len(last_search[user_id])))
            return

    with open('./cards.csv') as cfile:
        csv_file = csv.reader(cfile, delimiter=',',quotechar='"')
        # Find card and return value
        log_write("{1} \t$c {0}".format(arg,ctx.message.author))

        search=[]
        if (arg.startswith('"') and arg.endswith('"')):
            arg_clean = arg.replace('"',"").lower()
            for row in csv_file:
                if arg_clean == row[0].lower():
                    search.append(row)
        else:
            for row in csv_file:
                if arg.lower() in row[0].lower():
                    search.append(row)

        if len(search) != 1:
            if len(search) == 0:
                embed.set_author(name="Nenhum resultado encontrado, tente novamente.".format(str(len(search))))
                await ctx.send(embed=embed)
                log_write("Call for {} cards.".format(str(len(search))))
                return

            if len(search) > 24:
                embed.set_author(name="Essa busca excede o limite ({} cartas retornadas). Seja mais específico.".format(str(len(search))))
                await ctx.send(embed=embed)
                log_write("Call for {} cards.".format(str(len(search))))
                return

            if len(search) > 1:
                embed.set_author(name="Múltiplos Resultados:")

                x=1
                for ting in search:
                    embed.add_field(name=str(x)+".", value=ting[0], inline=False)
                    x+=1

                embed.add_field(name="Dica Quente", value='Use `$c [número]` para selecionar uma carta. Ou insira aspas para busca mais específica, ex "Jake"', inline=False)
                await ctx.send(embed=embed)
                last_search[user_id] = search  # Salvar para seleção posterior
                log_write("Mulitple ({}) Results found".format(str(len(search))))

        if len(search) == 1:
            returned_card=search[0]

            embed = discord.Embed(color=0xfff100)

            embed.set_author(name=returned_card[0], icon_url=os.getenv('BOT_ICON_URL'))
            embed.add_field(name="Baralho / Quantidade", value=returned_card[8].rstrip(), inline=False)
            embed.set_thumbnail(url=os.getenv('CARD_IMAGES_URL').format(urllib.parse.quote(returned_card[0])))

            if (returned_card[2].rstrip() == "Creature"):
                embed.add_field(name="Paisagem", value=returned_card[3].rstrip(), inline=True)
                embed.add_field(name="Tipo", value=returned_card[2].rstrip(), inline=True)
                embed.add_field(name="Custo", value=returned_card[4].rstrip(), inline=True)
                embed.add_field(name="ATA", value=returned_card[5].rstrip(), inline=True)
                embed.add_field(name="DEF", value=returned_card[6].rstrip(), inline=True)
                embed.add_field(name="Descrição", value=returned_card[1].rstrip(), inline=True)

            if (returned_card[2].rstrip() == "Spell" or returned_card[2].rstrip() == "Building" or returned_card[2].rstrip() == "Teamwork"):
                embed.add_field(name="Paisagem", value=returned_card[3].rstrip(), inline=True)
                embed.add_field(name="Tipo", value=returned_card[2].rstrip(), inline=True)
                embed.add_field(name="Custo", value=returned_card[4].rstrip(), inline=True)
                embed.add_field(name="Descrição", value=returned_card[1].rstrip(), inline=True)

            if (returned_card[2].rstrip() == "Hero"):
                embed.add_field(name="Tipo", value=returned_card[2].rstrip(), inline=True)
                embed.add_field(name="Descrição", value=returned_card[1].rstrip(), inline=True)
                #embed.add_field(name="Card Set", value=returned_card[9].rstrip(), inline=True)

            embed.add_field(name="Relatar um problema: ", value=f"Mensagem <@!{os.getenv('OWNER_ID')}>", inline=True)
            await ctx.send(embed=embed)
            log_write(returned_card[0])
            log_write("")

# Tratamento de erros de login
try:
    bot.run(TOKEN)
except discord.LoginFailure as e:
    log_write(f"ERROR: Falha no login - Token inválido ou expirado: {e}")
    print("ERRO: Token do Discord inválido! Verifique o arquivo .env")
except Exception as e:
    log_write(f"ERROR: Erro ao conectar bot: {e}")
    print(f"ERRO: Falha ao conectar bot: {e}")
