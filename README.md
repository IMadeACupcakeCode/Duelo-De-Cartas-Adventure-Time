# 🤖 Duelo De Cartas - Adventure Time

Bot de Discord para jogos de cartas baseado em Adventure Time com sistema completo de duelos!

## 🎮 Funcionalidades

- **Sistema de Seleção de Servidores**: Escolha quais servidores o bot funcionará antes da ativação
- **Busca de Cartas**: Visualize detalhes e imagens das cartas rapidamente
- **Sistema de Duelos**: Batalhe contra outros usuários com decks aleatórios
- **Comandos de Lazer**: Memes, piadas, insultos e jogos divertidos
- **Controle de Rate Limiting**: Evita bloqueios do Discord

## 🚀 Como Usar

### Passo 1: Configuração Inicial
1. Configure seu arquivo `.env` com o token do bot:
   ```
   DISCORD_TOKEN=SEU_TOKEN_AQUI
   BOT_ICON_URL=https://exemplo.com/icon.jpg
   CARD_IMAGES_URL=https://exemplo.com/cards/{}.jpg
   OWNER_ID=SEU_ID_DO_DISCORD
   ```

### Passo 2: Seleção de Servidores
Execute o script de seleção antes de ativar o bot:

```bash
cd "Cartas Adventure Time"
python select_servers.py
```

**Exemplo de saída:**
```
============================================================
🤖 SELEÇÃO DE SERVIDORES PARA O BOT
============================================================

📋 Servidores disponíveis (3):
 1. CoreVerse (1 membros)
 2. Confeitaria Esquizofrênica (1 membros)
 3. Servidor De Testes (1 membros)

📝 Instruções:
• Digite os números dos servidores separados por vírgula (ex: 1,3,5)
• Digite 'all' para selecionar todos
• Digite 'none' para não selecionar nenhum
• Deixe vazio para usar apenas o primeiro servidor
----------------------------------------
🎯 Escolha os servidores: 1,3

✅ 2 servidor(es) selecionado(s): CoreVerse, Servidor De Testes
```

### Passo 3: Ativar o Bot
Após a seleção, execute o bot principal:

```bash
python testinhos.py
```

## 📋 Comandos Disponíveis

### 🔍 **Busca de Cartas**
- `$c [nome]` - Mostra detalhes completos da carta
- `$img [nome]` - Mostra apenas a imagem da carta
- `$c [número]` - Seleciona carta de resultados múltiplos

### ⚔️ **Sistema de Duelos**
- `$duel @usuário` - Inicia duelo com decks aleatórios
- `$hand` - Mostra sua mão de cartas
- `$summon [índice]` - Convoca uma criatura
- `$attack [índice] player` - Ataca o oponente diretamente
- `$draw` - Compra uma carta extra
- `$board` - Mostra o campo de batalha
- `$endturn` - Passa o turno
- `$endduel` - Encerra o duelo

### 🎲 **Comandos de Lazer**
- `$meme` - Envia meme aleatório
- `$joke` - Conta uma piada
- `$insult [@usuário]` - Insulta alguém
- `$roll [lados] [quantidade]` - Rola dados
- `$flip` - Cara ou coroa

## ⚙️ Arquivos Necessários

- `cards.csv` - Dados das cartas
- `images/` - Pasta com imagens das cartas
- `memes/` - Pasta com memes (opcional)
- `.env` - Configurações do bot

## 🔧 Solução de Problemas

### Rate Limiting
- O bot controla automaticamente o envio de mensagens
- Selecione apenas os servidores necessários

### Comandos Não Respondem
- Verifique se o servidor foi selecionado
- Certifique-se de que o bot tem permissões

### Seleção de Servidores
- Execute `python select_servers.py` primeiro
- A seleção é salva em `selected_guilds.txt`

## 📝 Notas Técnicas

- Linguagem: Python 3.8+
- Biblioteca: discord.py
- Rate limiting controlado automaticamente
- Logs salvos em `log.log`

---
**🎮 Divirta-se duelando com cartas de Adventure Time!**
