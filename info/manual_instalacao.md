# Manual simplificado de instalação — Agente RAG Certidão Imobiliária

Este README rápido resume o que você precisa para preparar o agente responsável pela migração (scripts `agent.py` e `ingest.py`) localizado em `./agente-rag`.

## 1. Pré-requisitos básicos

- **Python 3.10+** (ou a mesma versão usada no virtualenv `venv`).  
- **Git** (a própria pasta já está clonada no monorepo, mas você pode copiar `./agente-rag` para outro lugar).  
- **Chave OpenAI válida** para as chamadas (defina no próximo passo).

## 2. Criar e ativar o ambiente

```bash
cd agente-rag
python -m venv venv
source venv/bin/activate          # Linux/macOS
venv\\Scripts\\activate.bat        # Windows cmd
```

> O `venv` já existe no repositório, mas recomendo recriar/atualizar para garantir compatibilidade.

## 3. Instalar dependências

```bash
pip install --upgrade pip
pip install \
  langchain_classic langchain_community langchain_chroma langchain_core \
  langchain_text_splitters langchain_openai langgraph chromadb python-dotenv
```

Se preferir, extraia o `pip freeze` do `venv` actual e salve em `requirements.txt` para reutilizar futuramente.

## 4. Configurar as variáveis de ambiente

- Copie `agente-rag/.env` para um arquivo seguro (por exemplo `.env.local`) e substitua `OPENAI_API_KEY` pelo seu valor real; o arquivo atual já traz a chave de exemplo e o modelo por padrão (`OPENAI_MODEL=gpt-4o-mini`).  
- Certifique-se de que o `.env` usado pela execução (`ingest.py` e `agent.py`) esteja no mesmo diretório do script e seja carregado com `load_dotenv`.
- A configuração de paths, aliases e hints agora está centralizada em `agente-rag/config/agent_config.json`. Ajuste os caminhos dos projetos (`projectDirs`) ou adicione novos aliases à medida que outros repositórios forem analisados. O `AGENT_CONFIG_PATH` definida no `.env` aponta para este arquivo e pode ser trocada caso você queira manter múltiplas configurações.

## 5. Gerar base de conhecimento (ingestão)

```bash
python ingest.py
```

- O script lê todos os arquivos dentro da pasta `docs/`, divide em chunks e salva embeddings em `.rag_db`.  
- A execução deve terminar com a mensagem `Ingestão concluída...` e criar `.rag_db/` (considere versionar apenas os dados específicos, se necessário).

## 6. Rodar o agente

```bash
python agent.py
```

- O `agent.py` usa `LangGraph` para orquestrar o fluxo de perguntas/ações com a base vetorial recém-criada.  
- Se `.rag_db` estiver faltando, ele lembrará de rodar `python ingest.py` antes.

## 7. Notas adicionais

- Mantenha `docs/todo.md`, `docs/arquivos_alterados.md` e `docs/system_prompt.md` atualizados: eles alimentam prompts, tarefas e histórico do agente.  
- Sempre ative o `venv` antes de executar qualquer script para garantir que as dependências (e a chave do OpenAI) sejam resolvidas corretamente.  
- Para atualizar dependências depois de alterar `agent.py` ou `ingest.py`, reexecute o passo 3 ou gere um novo `pip freeze`.

Pronto! Com esses passos o agente RAG estará instalado e você poderá consultá-lo via terminal dentro de `./agente-rag`. Se precisar expandir para outros repositórios (frontend/backend), os metadados já indexados em `docs/` serão usados automaticamente.
