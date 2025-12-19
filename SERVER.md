# 🏗️ Manual de Instalação – Agente RAG  + Servidor OpenAI-Compatible

# 📌 Visão Geral

Este documento descreve a instalação, configuração e execução do:

Agente RAG  (LangChain + LangGraph + RAG)

Servidor compatível com API OpenAI (server.py)

Integração com a extensão Continue.dev no VS Code

O objetivo é permitir conversar com o agente  usando uma interface de chat dentro do VS Code.

# 1️⃣ Requisitos

✔ Sistema

## Linux recomendado (Ubuntu/Xubuntu)

Windows + WSL2 funciona

✔ Python

## Python 3.10+

✔ VS Code

Extensão Continue.dev instalada
👉 https://marketplace.visualstudio.com/items?itemName=Continue.continue

# 2️⃣ Instalando as Dependências

## Crie e ative um ambiente virtual:

- python3 -m venv venv
- source venv/bin/activate

## Instale as dependências principais:

pip install langchain langchain-core langchain-community langchain-openai langchain-chroma langchain-text-splitters langgraph chromadb python-dotenv fastapi uvicorn pydantic

Se necessário:

pip install langchain-classic

# 3️⃣ Estrutura Recomendada de Pastas

agente-rag/ \
│\
├── agent.py\
├── ingest.py\
├── server.py\
├── .env\
│\
└── docs/\
 ├── system_prompt.md\
 ├── todo.md\
 ├── arquivos_alterados.md\
 ├── execucoes/ \
 └── ... (documentação da migração)\

A pasta docs/ é usada pelo RAG.

# 4️⃣ Configuração do .env

Crie ou edite o arquivo .env:

OPENAI_MODEL=gpt-4o-mini \
AGENT_MAX_ITERATIONS=100 \
AGENT_MAX_EXECUTION_TIME=240 \

# 5️⃣ Executando o Ingest das Documentações

Sempre que alterar algo na pasta docs/, execute:

python ingest.py

Isso atualiza a base vetorial .rag_db/.

# 6️⃣ Rodando o Agente no Terminal (opcional)

python agent.py

# 7️⃣ Iniciando o Servidor OpenAI-Compatible

O servidor torna o agente acessível via API REST, compatível com /v1/chat/completions.

## Para iniciar:

python server.py

Ele ficará disponível em:

http://127.0.0.1:8001/v1/chat/completions

# 8️⃣ Integração com VS Code (Continue.dev)

Abra o configurador:

Ctrl + Shift + P → Continue: Edit Config

E adicione ao config.yaml:

name: Agente Certidao 
version: 1.0.0
schema: v1

models:

- name: Agente Certidao
  provider: openai
  model: local-agent
  apiBase: http://127.0.0.1:8001/v1
  apiKey: DUMMY
  roles:
  - chat

context:

- provider: code
- provider: docs
- provider: folder
- provider: terminal

Recarregue o VS Code:

Ctrl + Shift + P → Developer: Reload Window

Agora, no painel Continue, selecione o modelo:

Agente Certidao

# 9️⃣ Conversando com o Agente via VS Code

Abra o painel Continue e digite:

Quero iniciar a migração da USC_04_142.

O agente:
acessa a base vetorial

usa RAG
atualiza docs/todo.md e docs/execucoes/

executa LangGraph

devolve resposta via Continue.dev

# 🔟 Comandos Úteis

## Reiniciar servidor:

pkill -f server.py
python server.py

## Atualizar embeddings:

python ingest.py

Limpar histórico do agente:

Apagar o conteúdo de:

docs/todo.md
docs/arquivos_alterados.md
docs/execucoes/

# 1️⃣1️⃣ Erros Comuns

ModuleNotFoundError: No module named 'langchain_classic'

## Instale:

pip install langchain-classic

Continue não mostra o modelo

## Recarregue a janela:

Ctrl + Shift + P → Developer: Reload Window

Erro 127.0.0.1:8001 refused

## O servidor não está rodando:

python server.py

# 1️⃣2️⃣ Dicas Finais

Execute sempre o server.py antes de abrir o Continue. \
Mantenha tudo dentro da mesma workspace.\
Sempre rode o ingest após atualizar a pasta docs/.\
Seu agente continua atualizando automaticamente:\

todo.md\
execucoes/\
arquivos_alterados.md\
