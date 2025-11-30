```mermaid
flowchart TD
    U[Usuário (Terminal)] -->|pergunta| CLI[agent.py CLI]
    CLI --> LG[LangGraph\n(StateGraph)]

    LG --> NODE[Node: executar_agente]

    NODE --> LCAG[Agente LangChain\n(OpenAI Functions + Tools)]
    LCAG --> TOOL_DOC[Tool: consultar_documentacao\n(RAG sobre docs/)]
    LCAG --> TOOL_FS[Tools: buscar_arquivos / ler_arquivo / escrever_arquivo]

    TOOL_DOC --> CHROMA[(Chroma .rag_db)]
    CHROMA --> TOOL_DOC

    TOOL_FS --> PROJETOS[(Projetos\nVue2 / Vue3 / NestJS)]
    TOOL_FS --> DOCS[(Pasta docs/)]

    LCAG --> NODE
    NODE --> LG
    LG --> CLI
    CLI --> U[Usuário (Terminal)]

    CLI --> DOC_TODO[docs/todo.md]
    CLI --> DOC_EXEC[docs/execucoes/*.md]
    CLI --> DOC_ALTERADOS[docs/arquivos_alterados.md]
```
