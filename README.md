# README - Bot de Cartas Adventure Time (Card Wars)

Este é um bot Discord para jogar Card Wars com cartas de Adventure Time. Ele permite visualizar detalhes e imagens das cartas de forma rápida e fácil.

## Funcionalidades
- Busca de cartas por nome.
- Exibição de detalhes completos das cartas (tipo, custo, ataque, defesa, etc.).
- Visualização de imagens das cartas.
- Suporte a prefixos `$` ou menção ao bot (`@bot`).
- Busca exata com aspas.
- Sistema de duelos entre usuários.
- Comandos de lazer (memes, piadas, insultos, etc.).
- Restrições de canais e roles para controle de uso.

## Permissões e Restrições
- O bot só envia mensagens automáticas (boas-vindas, avisos de inatividade, shutdown) em canais cujo nome contenha "guerra de cartas" ou "card war".
- Para usar comandos, o usuário deve ter uma role no servidor com nome contendo "guerra de cartas" ou "card war".
- Se o usuário não tiver a role, receberá uma mensagem de erro ao tentar usar comandos.
- Isso permite controlar quem pode interagir com o bot e em quais canais ele opera.

## Requisitos
- Python 3.8 ou superior.
- Biblioteca discord.py (instalada automaticamente no Passo 1).

## Passo 1: Instalação
1. Instale o Python (versão 3.8 ou superior) se não tiver.
2. Instale a biblioteca discord.py: Abra o terminal e execute:
   ```
   pip install discord.py
   ```

## Passo 2: Criar o Bot no Discord
1. Vá para [https://discord.com/developers/applications](https://discord.com/developers/applications).
2. Clique em "New Application" e dê um nome (ex: Card Wars Bot).
3. Na aba "Bot", clique em "Add Bot".
4. **Importante:** Na seção "Privileged Gateway Intents", ative "Message Content Intent".
5. Copie o "Token" (guarde em segredo).
6. Na aba "General Information", copie o "Application ID".
7. Vá para `https://discord.com/api/oauth2/authorize?client_id=SEU_APPLICATION_ID&permissions=2048&scope=bot`
   Substitua `SEU_APPLICATION_ID` e autorize o bot no seu servidor.

## Passo 3: Preparar os Arquivos
1. No diretório do código (onde está `testinhos.py`), certifique-se de ter o arquivo `cards.csv` com os dados das cartas.
   - Formato CSV: Nome,Descrição,Tipo,Paisagem,Custo,ATA,DEF,?,Baralho/Quantidade,Conjunto
   - Exemplo:
     ```
     Jake,"O cachorro amarelo amigo do Finn","Creature","Forest","2","3","4","","Forest Deck","Base Set"
     ```

2. Certifique-se de ter a pasta `images/` com imagens .jpg/.png das cartas, nomeadas exatamente como os nomes das cartas (ex: `Jake.jpg`).

## Passo 4: Configurar o Código
1. Instale a biblioteca python-dotenv: `pip install python-dotenv`
2. Crie um arquivo `.env` no diretório do código com:
   ```
   DISCORD_TOKEN=SEU_TOKEN_AQUI
   BOT_ICON_URL=https://tse3.mm.bing.net/th/id/OIP.UWjdkRvAf4Ez6L-sbeIenAHaFl?w=589&h=444&rs=1&pid=ImgDetMain&o=7&rm=3
   CARD_IMAGES_URL=https://yourserver.com/cardwarsimages/{}.jpg
   OWNER_ID=SEU_ID_DO_DISCORD
   ```
3. Substitua os valores pelos seus próprios (token do bot, URL do ícone, URL das imagens, seu ID do Discord).

## Passo 5: Executar o Bot
1. Abra o terminal no diretório do código.
2. Execute: `python testinhos.py`
3. O bot deve aparecer online no seu servidor com status "Card Wars".

## Tabela de Comandos

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `$help` | Mostra ajuda nas DMs. | `$help` |
| `$c [nome da carta]` | Mostra detalhes da carta em embed. | `$c Jake` |
| `$img [nome da carta]` | Envia a imagem da carta. | `$img Jake` |
| `$c [número]` | Seleciona carta de múltiplos resultados para detalhes. | `$c 1` |
| `$img [número]` | Seleciona carta de múltiplos resultados para imagem. | `$img 2` |
| **Duelos:** | | |
| `$duel @usuário` | Inicia um duelo com decks aleatórios. | `$duel @amigo` |
| `$hand` | Mostra sua mão de cartas. | `$hand` |
| `$summon [índice]` | Convoca criatura da mão (gasta mana). | `$summon 1` |
| `$attack [índice] [alvo]` | Ataca com criatura (alvo: número ou 'player'). | `$attack 1 2` ou `$attack 1 player` |
| `$draw` | Compra uma carta extra. | `$draw` |
| `$board` | Mostra o campo de batalha. | `$board` |
| `$rules` | Mostra as regras do jogo. | `$rules` |
| `$endturn` | Passa turno (oponente ganha mana e compra). | `$endturn` |
| `$duelstatus` | Mostra HP e turno. | `$duelstatus` |
| `$endduel` | Encerra o duelo. | `$endduel` |
| **Lazer:** | | |
| `$meme` | Envia um meme aleatório. | `$meme` |
| `$joke` | Conta uma piada aleatória. | `$joke` |
| `$insult [@usuário]` | Insulta o usuário mencionado (aleatório se não marcar). | `$insult @user` |
| `$quote` | Citação famosa de jogos. | `$quote` |
| `$roll [lados] [quantidade]` | Rola dados e soma. | `$roll 6 2` |
| `$flip` | Cara ou coroa. | `$flip` |
