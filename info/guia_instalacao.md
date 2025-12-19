# Guia de instalação — Agente RAG Certidão Imobiliária

Este guia explica como preparar o ambiente local para executar os scripts `ingest.py`, `agent.py` e, opcionalmente, o `server.py` (API compatível com OpenAI). Todos os passos usam apenas ferramentas já presentes no repositório.

## 1. Pré-requisitos

- **Python 3.10+** (mesma versão usada no `venv` incluído).
- **Git** para clonar/copiar o projeto, caso ainda não esteja na sua máquina.
- **Chave de API da OpenAI** válida para uso dos modelos (`gpt-4o-mini` por padrão).
- **VS Code + Continue.dev** apenas se desejar conversar com o agente via extensão.

## 2. Clonar o projeto (opcional)

Se ainda não possui o diretório `agente-rag`, clone ou copie:

```bash
git clone <url-do-repo> agente-rag
cd agente-rag
```

Se a pasta já estiver no monorepo, basta navegar até ela.

## 3. Criar e ativar o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
```

> A pasta `venv/` já existe, mas é recomendado recriá-la para garantir compatibilidade com sua versão do Python.

## 4. Instalar dependências Python

Atualize o `pip` e instale as libs utilizadas pelos scripts do agente:

```bash
pip install --upgrade pip
pip install \
  langchain_classic langchain_core langchain_community langchain_openai \
  langchain_text_splitters langchain_chroma langgraph chromadb python-dotenv \
  fastapi uvicorn pydantic
```

Caso use outra máquina depois, gere um `requirements.txt` com `pip freeze > requirements.txt` e reutilize.

## 5. Configurar variáveis de ambiente

1. Copie `.env` para um arquivo seguro (ex.: `.env.local`) se quiser manter valores sensíveis fora do controle de versão.
2. Defina:
   - `OPENAI_API_KEY=<sua-chave>`
   - `OPENAI_MODEL=gpt-4o-mini` (ou outro modelo suportado)
   - `AGENT_MAX_ITERATIONS`, `AGENT_MAX_EXECUTION_TIME` conforme sua necessidade.
   - `AGENT_CONFIG_PATH=config/agent_config.json` (padrão já apontado).
3. Certifique-se de que o arquivo `.env` esteja no mesmo diretório dos scripts executados (`agent.py`, `ingest.py`, `server.py`).

O arquivo `config/agent_config.json` centraliza caminhos dos projetos e aliases de use cases. Ajuste `projectDirs` se a estrutura local for diferente.

## 6. Preparar a base vetorial (ingestão)

Sempre que atualizar arquivos em `docs/`, execute:

```bash
python3 ingest.py
```

Esse comando cria/atualiza a pasta `.rag_db/` com os embeddings usados pelo agente. O script imprime `Ingestão concluída...` ao finalizar.

## 7. Executar o agente no terminal

Após o ingest, rode:

```bash
python agent.py
```

O agente utiliza LangGraph + LangChain para responder perguntas e atualizar arquivos como `docs/todo.md`, `docs/arquivos_alterados.md` e `docs/execucoes/…`.

## 8. (Opcional) Iniciar o servidor compatível com OpenAI

Para expor o agente via API REST — útil para a extensão Continue.dev — inicie:

```bash
python server.py
```

O endpoint fica disponível em `http://127.0.0.1:8001/v1/chat/completions`. Configure o Continue.dev (ou outro cliente) apontando `apiBase` para essa URL e use `apiKey: DUMMY` ou qualquer valor fictício.

## 9. Fluxo sugerido de uso diário

1. Ative o `venv`.
2. Atualize a documentação em `docs/`.
3. Rode `python ingest.py`.
4. Execute `python agent.py` ou suba o `server.py`.
5. Consulte os arquivos dentro de `docs/` para acompanhar histórico de tarefas e execuções.

## 10. Solução rápida de problemas

| Sintoma | Ação sugerida |
| --- | --- |
| `ModuleNotFoundError: langchain_classic` | Reexecutar o passo 4 instalando dependências. |
| Erro ao chamar API OpenAI local (`connection refused`) | Verifique se `server.py` está rodando (`pkill -f server.py` / `python server.py`). |
| Respostas incompletas ou base vazia | Certifique-se de ter executado `python ingest.py` após editar `docs/`. |
| Continue.dev não mostra o modelo | Reinicie o VS Code (`Ctrl+Shift+P → Developer: Reload Window`). |

Seguindo estes passos, o ambiente do agente RAG estará pronto para ingestão de documentos, execução via terminal ou exposição como API compatível com OpenAI.
