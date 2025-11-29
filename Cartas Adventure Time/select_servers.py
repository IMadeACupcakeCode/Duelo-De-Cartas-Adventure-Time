#!/usr/bin/env python3
"""
Script para seleção de servidores do bot antes da ativação.
Uso: python select_servers.py
"""

import os
import discord
from dotenv import load_dotenv

load_dotenv()

def main():
    """Função principal para seleção de servidores."""
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found in .env file!")
        return

    if TOKEN == "SEU_TOKEN_AQUI":
        print("❌ ERROR: Please set your real Discord token in .env file!")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"\n🤖 Conectado como {client.user}")
        print("="*60)
        print("🤖 SELEÇÃO DE SERVIDORES PARA O BOT")
        print("="*60)

        if not client.guilds:
            print("❌ Nenhum servidor encontrado!")
            await client.close()
            return

        print(f"\n📋 Servidores disponíveis ({len(client.guilds)}):")
        print("-" * 40)

        guild_list = []
        for i, guild in enumerate(client.guilds, 1):
            member_count = len(guild.members)
            print(f"{i:2d}. {guild.name} ({member_count} membros)")
            guild_list.append(guild)

        print("\n" + "-" * 40)
        print("📝 Instruções:")
        print("• Digite os números dos servidores separados por vírgula (ex: 1,3,5)")
        print("• Digite 'all' para selecionar todos")
        print("• Digite 'none' para não selecionar nenhum")
        print("• Deixe vazio para usar apenas o primeiro servidor")
        print("-" * 40)

        # Usar um loop síncrono fora do event loop
        import asyncio
        loop = asyncio.get_event_loop()
        selected_guilds = await loop.run_in_executor(None, get_user_choice, guild_list)

        # Salvar seleção no arquivo
        try:
            with open('selected_guilds.txt', 'w') as f:
                for guild_id in selected_guilds:
                    f.write(f"{guild_id}\n")
            print(f"\n💾 Seleção salva em 'selected_guilds.txt' ({len(selected_guilds)} servidores)")
        except Exception as e:
            print(f"❌ Erro ao salvar seleção: {e}")

        print(f"\n🎮 Servidores ativos: {len(selected_guilds)}")
        print("="*60)
        print("✅ Configuração concluída! Agora execute o bot principal.")
        print("="*60)

        await client.close()

    try:
        client.run(TOKEN)
    except discord.LoginFailure as e:
        print(f"❌ ERROR: Falha no login - Token inválido: {e}")
    except Exception as e:
        print(f"❌ ERROR: Falha ao conectar: {e}")

def get_user_choice(guild_list):
    """Função síncrona para obter escolha do usuário."""
    while True:
        try:
            choice = input("🎯 Escolha os servidores: ").strip().lower()

            if choice == 'all':
                return {guild.id for guild in guild_list}
            elif choice == 'none':
                return set()
            elif choice == '':
                return {guild_list[0].id} if guild_list else set()
            else:
                # Parse dos números
                indices = []
                for part in choice.split(','):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part)
                        if 1 <= idx <= len(guild_list):
                            indices.append(idx - 1)
                        else:
                            print(f"⚠️ Número {idx} inválido (deve ser entre 1 e {len(guild_list)})")
                            indices = []
                            break

                if indices:
                    return {guild_list[i].id for i in indices}
                else:
                    print("❌ Entrada inválida. Tente novamente.")

        except KeyboardInterrupt:
            print("\n❌ Seleção cancelada pelo usuário.")
            return set()
        except Exception as e:
            print(f"❌ Erro: {e}")
            return set()

if __name__ == "__main__":
    main()
