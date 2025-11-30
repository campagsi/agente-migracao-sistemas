# Arquitetura do Agente RAG de Certidão Imobiliária

## Visão geral

O agente foi projetado para auxiliar na migração do sistema de Certidão Imobiliária:

- De: Vue 2 + backend legado (JBoss / Oracle)
- Para: Vue 3 (Composition API + PiVue) + NestJS

Ele combina:

- **LangChain** → RAG, tools, Agent (OpenAI Functions)
- **Chroma** → base vetorial com a pasta `docs/`
- **LangGraph** → orquestração do fluxo de execução
- **Ferramentas de arquivo** → leitura/escrita em código e documentação

## Componentes principais

1. **Ingestão (`ingest.py`)**

   - Varre `./docs/`
   - Cria documentos com metadados (`source`)
   - Faz chunk com `RecursiveCharacterTextSplitter`
   - Persiste no Chroma em `.rag_db`

2. **Base vetorial (Chroma)**

   - Diretório: `.rag_db/`
   - Armazena os embeddings dos documentos da pasta `docs/`
   - Consultada via `ConversationalRetrievalChain`

3. **Agente (`agent.py`)**

   - Carrega o `system_prompt.md`
   - Monta a tool RAG `consultar_documentacao`
   - Define tools:
     - `consultar_documentacao` (RAG em cima de `docs/`)
     - `buscar_arquivos` (busca por nome de arquivo nos projetos Vue2/Vue3/NestJS)
     - `ler_arquivo` (leitura de arquivos)
     - `escrever_arquivo` (escrita de arquivos + registro de alterações)
   - Cria um agent do LangChain com:
     - `AgentType.OPENAI_FUNCTIONS`
     - Tools acima
     - System message = conteúdo do `docs/system_prompt.md`

4. **Orquestração com LangGraph**

   - Tipo de estado: `AgentState = { "input": str, "answer": str }`
   - Nó único: `executar_agente`
     - Recebe a pergunta do usuário
     - Chama o agente LangChain (com tools + RAG)
     - Atualiza o histórico de RAG
     - Retorna a resposta

5. **Documentação automática**
   - `docs/todo.md`:
     - Cada pergunta gera um bloco com:
       - Pergunta
       - “Plano e ações técnicas” (a própria resposta do agente)
   - `docs/execucoes/execucao_YYYYMMDD_HHMMSS.md`:
     - Pergunta
     - Resposta
     - Lista agrupada de arquivos alterados
   - `docs/arquivos_alterados.md`:
     - Resumo por execução:
       - Timestamp
       - Lista de arquivos alterados agrupados (Frontend Vue2, Vue3, Backend, Documentação)

## Fluxo de uma execução

1. Usuário digita uma pergunta no terminal (`agent.py` / CLI).
2. O LangGraph recebe o estado inicial `{ input: pergunta, answer: "" }`.
3. O nó `executar_agente`:
   1. Cria um handler de callbacks para logar no terminal.
   2. Chama o agente LangChain com:
      - System prompt (`system_prompt.md`)
      - Tools (RAG, arquivos, etc.).
   3. O agente pode:
      - Consultar docs com `consultar_documentacao` (RAG).
      - Buscar arquivos de código com `buscar_arquivos`.
      - Ler e escrever arquivos com `ler_arquivo` e `escrever_arquivo`.
   4. A resposta final é retornada ao grafo.
   5. O histórico de RAG (`rag_history`) é atualizado.
4. O CLI imprime a resposta para o usuário.
5. O agente atualiza a documentação:
   - `docs/todo.md`
   - `docs/execucoes/...`
   - `docs/arquivos_alterados.md`
