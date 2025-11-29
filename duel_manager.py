import discord
from discord.ext import commands
import random
import json
import os

# Carregar configuração
with open('config.json', 'r') as f:
    config = json.load(f)

class DuelManager:
    def __init__(self, all_cards, get_card_data_func):
        self.active_duels = {}  # user_id: opponent_id
        self.duel_turns = {}    # user_id: True/False (sua vez)
        self.duel_hp = {}       # user_id: hp
        self.duel_deck = {}     # user_id: list of card names
        self.duel_hand = {}     # user_id: list of card names
        self.duel_board = {}    # user_id: list of summoned creatures (dicts with name, atk, def, etc.)
        self.duel_mana = {}     # user_id: current mana
        self.duel_max_mana = {} # user_id: max mana
        self.duel_graveyard = {} # user_id: list of discarded cards
        self.duel_message_ids = {}  # user_id: message_id do status
        self.all_cards = all_cards
        self.get_card_data = get_card_data_func

    def start_duel(self, ctx, opponent):
        user_id = ctx.author.id
        opponent_id = opponent.id

        # Iniciar duelo
        self.active_duels[user_id] = opponent_id
        self.active_duels[opponent_id] = user_id
        self.duel_turns[user_id] = True
        self.duel_turns[opponent_id] = False
        self.duel_hp[user_id] = config['duel']['starting_hp']
        self.duel_hp[opponent_id] = config['duel']['starting_hp']
        self.duel_mana[user_id] = config['duel']['starting_mana']
        self.duel_mana[opponent_id] = config['duel']['starting_mana']
        self.duel_max_mana[user_id] = config['duel']['starting_mana']
        self.duel_max_mana[opponent_id] = config['duel']['starting_mana']

        # Decks aleatórios
        all_card_names = [card[0] for card in self.all_cards[:30]]
        self.duel_deck[user_id] = random.sample(all_card_names, config['duel']['deck_size'])
        self.duel_deck[opponent_id] = random.sample(all_card_names, config['duel']['deck_size'])

        # Mãos iniciais
        self.duel_hand[user_id] = random.sample(self.duel_deck[user_id], config['duel']['hand_size'])
        self.duel_hand[opponent_id] = random.sample(self.duel_deck[opponent_id], config['duel']['hand_size'])

        # Remover cartas da mão do deck
        for card in self.duel_hand[user_id]:
            self.duel_deck[user_id].remove(card)
        for card in self.duel_hand[opponent_id]:
            self.duel_deck[opponent_id].remove(card)

        self.duel_board[user_id] = []
        self.duel_board[opponent_id] = []
        self.duel_graveyard[user_id] = []
        self.duel_graveyard[opponent_id] = []

        embed = discord.Embed(
            title="⚔️ **DUEL INICIADO!** ⚔️",
            description=f"{ctx.author.mention} desafiou {opponent.mention} para um duelo!",
            color=0xff0000
        )
        embed.add_field(name=f"{ctx.author.display_name}", value=f"❤️ HP: {self.duel_hp[user_id]}\n🔵 Mana: {self.duel_mana[user_id]}/{self.duel_max_mana[user_id]}", inline=True)
        embed.add_field(name=f"{opponent.display_name}", value=f"❤️ HP: {self.duel_hp[opponent_id]}\n🔵 Mana: {self.duel_mana[opponent_id]}/{self.duel_max_mana[opponent_id]}", inline=True)
        embed.add_field(name="🎯 Vez de:", value=f"{ctx.author.mention}", inline=False)
        embed.set_footer(text="Use $hand para ver suas cartas | $rules para ver as regras")

        return embed

    def get_hand_embed(self, user_id):
        hand_cards = self.duel_hand[user_id]
        if not hand_cards:
            return discord.Embed(
                title="🃏 **Sua Mão**",
                description="Sua mão está vazia!",
                color=0xfff100
            )

        embed = discord.Embed(
            title="🃏 **Sua Mão**",
            description=f"Você tem {len(hand_cards)} cartas na mão:",
            color=0xfff100
        )

        for i, card_name in enumerate(hand_cards, 1):
            card_data = self.get_card_data(card_name)
            cost = card_data[4] if card_data else "?"
            embed.add_field(name=f"{i}. {card_name}", value=f"💎 Custo: {cost}", inline=True)

        embed.add_field(name="💡 Como usar:", value="$summon [número] para invocar\n$attack [número] player para atacar\n$draw para comprar\n$endturn para passar", inline=False)

        return embed

    def summon_card(self, ctx, card_index):
        user_id = ctx.author.id
        if user_id not in self.active_duels:
            return "❌ Você não está em um duelo!"

        if not self.duel_turns[user_id]:
            return "❌ Não é sua vez!"

        if card_index < 1 or card_index > len(self.duel_hand[user_id]):
            return f"❌ Número inválido! Use um número entre 1 e {len(self.duel_hand[user_id])}."

        card_name = self.duel_hand[user_id][card_index - 1]
        card_data = self.get_card_data(card_name)
        mana_cost = int(card_data[4]) if card_data else len(card_name) // 3 + 1

        if self.duel_mana[user_id] < mana_cost:
            return f"❌ Você não tem mana suficiente! Precisa de {mana_cost} mana, você tem {self.duel_mana[user_id]}."

        # Invocar
        self.duel_mana[user_id] -= mana_cost
        self.duel_hand[user_id].remove(card_name)

        creature = {
            'name': card_name,
            'atk': int(card_data[5]) if card_data else random.randint(1, 5),
            'def': int(card_data[6]) if card_data else random.randint(1, 5)
        }
        self.duel_board[user_id].append(creature)

        embed = discord.Embed(
            title="🪄 **Carta Invocada!**",
            description=f"{ctx.author.mention} invocou **{card_name}**!",
            color=0xfff100
        )
        embed.add_field(name="👹 Nome:", value=card_name, inline=True)
        embed.add_field(name="⚔️ ATK:", value=creature['atk'], inline=True)
        embed.add_field(name="🛡️ DEF:", value=creature['def'], inline=True)
        embed.add_field(name="🔵 Mana restante:", value=f"{self.duel_mana[user_id]}/{self.duel_max_mana[user_id]}", inline=False)
        if card_data:
            embed.set_thumbnail(url=os.getenv('CARD_IMAGES_URL').format(urllib.parse.quote(card_name)))

        return embed

    def attack_player(self, ctx, creature_index):
        user_id = ctx.author.id
        if user_id not in self.active_duels:
            return "❌ Você não está em um duelo!"

        if not self.duel_turns[user_id]:
            return "❌ Não é sua vez!"

        if not self.duel_board[user_id]:
            return "❌ Você não tem criaturas no campo!"

        if creature_index < 1 or creature_index > len(self.duel_board[user_id]):
            return f"❌ Número inválido! Use um número entre 1 e {len(self.duel_board[user_id])}."

        creature = self.duel_board[user_id][creature_index - 1]
        opponent_id = self.active_duels[user_id]

        self.duel_hp[opponent_id] -= creature['atk']

        embed = discord.Embed(
            title="⚔️ **Ataque Direto!**",
            description=f"{ctx.author.mention} atacou {ctx.guild.get_member(opponent_id).mention} diretamente!",
            color=0xe74c3c
        )
        embed.add_field(name="💥 Dano causado:", value=f"❤️ -{creature['atk']} HP", inline=True)
        embed.add_field(name="❤️ HP restante do oponente:", value=f"{self.duel_hp[opponent_id]}", inline=True)

        if self.duel_hp[opponent_id] <= 0:
            embed.add_field(name="🏆 Resultado:", value=f"{ctx.author.mention} venceu!", inline=False)
            self.cleanup_duel(user_id, opponent_id)
            return embed

        return embed

    def draw_card(self, ctx):
        user_id = ctx.author.id
        if user_id not in self.active_duels:
            return "❌ Você não está em um duelo!"

        if not self.duel_turns[user_id]:
            return "❌ Não é sua vez!"

        if not self.duel_deck[user_id]:
            return "❌ Seu deck está vazio!"

        new_card = random.choice(self.duel_deck[user_id])
        self.duel_hand[user_id].append(new_card)
        self.duel_deck[user_id].remove(new_card)

        embed = discord.Embed(
            title="🃏 **Carta Comprada!**",
            description=f"{ctx.author.mention} comprou uma carta!",
            color=0xfff100
        )
        embed.add_field(name="🎴 Carta:", value=new_card, inline=False)
        embed.add_field(name="📚 Cartas na mão agora:", value=len(self.duel_hand[user_id]), inline=True)

        return embed

    def end_turn(self, ctx):
        user_id = ctx.author.id
        if user_id not in self.active_duels:
            return "❌ Você não está em um duelo!"

        if not self.duel_turns[user_id]:
            return "❌ Não é sua vez!"

        opponent_id = self.active_duels[user_id]

        # Passar turno
        self.duel_turns[user_id] = False
        self.duel_turns[opponent_id] = True

        # Aumentar mana do oponente
        self.duel_max_mana[opponent_id] += 1
        self.duel_mana[opponent_id] = self.duel_max_mana[opponent_id]

        # Oponente compra
        if self.duel_deck[opponent_id]:
            new_card = random.choice(self.duel_deck[opponent_id])
            self.duel_hand[opponent_id].append(new_card)
            self.duel_deck[opponent_id].remove(new_card)

        embed = discord.Embed(
            title="🔄 **Turno Passado!**",
            description=f"Agora é a vez de {ctx.guild.get_member(opponent_id).mention}!",
            color=0x2ecc71
        )
        embed.add_field(
            name=f"🎮 Vez de {ctx.guild.get_member(opponent_id).display_name}:",
            value=f"🔵 Mana: {self.duel_mana[opponent_id]}/{self.duel_max_mana[opponent_id]}\n🃏 Cartas na mão: {len(self.duel_hand[opponent_id])}",
            inline=False
        )

        return embed

    def get_board_embed(self, ctx):
        user_id = ctx.author.id
        if user_id not in self.active_duels:
            return "❌ Você não está em um duelo!"

        opponent_id = self.active_duels[user_id]

        embed = discord.Embed(
            title="🏟️ **Campo de Batalha**",
            color=int(config['colors']['info'], 16)
        )

        # Suas criaturas
        if self.duel_board[user_id]:
            your_creatures = ""
            for i, creature in enumerate(self.duel_board[user_id], 1):
                your_creatures += f"{i}. {creature['name']} (⚔️ {creature['atk']}, 🛡️ {creature['def']})\n"
            embed.add_field(name=f"🛡️ Criaturas de {ctx.author.display_name}", value=your_creatures, inline=False)
        else:
            embed.add_field(name=f"🛡️ Criaturas de {ctx.author.display_name}", value="Nenhuma criatura no campo", inline=False)

        # Criaturas do oponente
        if self.duel_board[opponent_id]:
            opp_creatures = ""
            for i, creature in enumerate(self.duel_board[opponent_id], 1):
                opp_creatures += f"{i}. {creature['name']} (⚔️ {creature['atk']}, 🛡️ {creature['def']})\n"
            embed.add_field(name=f"⚔️ Criaturas de {ctx.guild.get_member(opponent_id).display_name}", value=opp_creatures, inline=False)
        else:
            embed.add_field(name=f"⚔️ Criaturas de {ctx.guild.get_member(opponent_id).display_name}", value="Nenhuma criatura no campo", inline=False)

        return embed

    def end_duel(self, ctx):
        user_id = ctx.author.id
        if user_id not in self.active_duels:
            return "❌ Você não está em um duelo!"

        opponent_id = self.active_duels[user_id]
        opponent = ctx.guild.get_member(opponent_id)

        embed = discord.Embed(
            title="🏁 **Duelo Encerrado**",
            description=f"{ctx.author.mention} encerrou o duelo contra {opponent.mention}.",
            color=int(config['colors']['warning'], 16)
        )

        self.cleanup_duel(user_id, opponent_id)
        return embed

    def get_status_embed(self, ctx):
        user_id = ctx.author.id
        if user_id not in self.active_duels:
            return "❌ Você não está em um duelo!"

        opponent_id = self.active_duels[user_id]

        embed = discord.Embed(
            title="📊 **Status do Duelo**",
            color=int(config['colors']['primary'], 16)
        )

        embed.add_field(
            name=f"❤️ {ctx.author.display_name}",
            value=f"HP: {self.duel_hp[user_id]}\n{config['emojis']['mana']} Mana: {self.duel_mana[user_id]}/{self.duel_max_mana[user_id]}\n{config['emojis']['card']} Cartas na mão: {len(self.duel_hand[user_id])}\nCriaturas no campo: {len(self.duel_board[user_id])}",
            inline=True
        )

        embed.add_field(
            name=f"❤️ {ctx.guild.get_member(opponent_id).display_name}",
            value=f"HP: {self.duel_hp[opponent_id]}\n{config['emojis']['mana']} Mana: {self.duel_mana[opponent_id]}/{self.duel_max_mana[opponent_id]}\n{config['emojis']['card']} Cartas na mão: {len(self.duel_hand[opponent_id])}\nCriaturas no campo: {len(self.duel_board[opponent_id])}",
            inline=True
        )

        current_player = ctx.author.display_name if self.duel_turns[user_id] else ctx.guild.get_member(opponent_id).display_name
        embed.add_field(name="🎯 Vez atual:", value=current_player, inline=False)

        return embed

    def cleanup_duel(self, user_id, opponent_id):
        for uid in [user_id, opponent_id]:
            if uid in self.active_duels:
                del self.active_duels[uid]
            if uid in self.duel_turns:
                del self.duel_turns[uid]
            if uid in self.duel_hp:
                del self.duel_hp[uid]
            if uid in self.duel_mana:
                del self.duel_mana[uid]
            if uid in self.duel_max_mana:
                del self.duel_max_mana[uid]
            if uid in self.duel_deck:
                del self.duel_deck[uid]
            if uid in self.duel_hand:
                del self.duel_hand[uid]
            if uid in self.duel_board:
                del self.duel_board[uid]
            if uid in self.duel_graveyard:
                del self.duel_graveyard[uid]
            if uid in self.duel_message_ids:
                del self.duel_message_ids[uid]

# Função para criar embed de regras
def get_rules_embed():
    embed = discord.Embed(
        title="📜 **Regras do Duelo - Guerra De Cartas**",
        description="Bem-vindo ao sistema de duelos! Aqui estão as regras básicas:",
        color=0xfff100
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
        value="• Cada jogador começa com 3 cartas\n• Cartas têm custo de mana\n• Invocação consome mana",
        inline=False
    )

    embed.add_field(
        name="⚔️ **Combate**",
        value="• `$summon [número]` - Invocar criatura\n• `$attack [número] player` - Atacar oponente\n• `$draw` - Comprar carta\n• `$endturn` - Passar turno",
        inline=False
    )

    embed.add_field(
        name="🎲 **Turnos**",
        value="• Alternem turnos\n• Oponente ganha mana e compra carta no seu turno\n• Use `$duelstatus` para ver o estado",
        inline=False
    )

    embed.set_footer(text="Divirta-se duelando! 🃏⚔️")

    return embed
