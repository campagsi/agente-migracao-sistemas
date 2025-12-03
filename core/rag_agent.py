import os
from typing import Any, Tuple, TypedDict

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_chroma import Chroma
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from . import config
from . import tools


class LegacyChatOpenAI(ChatOpenAI):
    @staticmethod
    def _merge_callback_config(config: RunnableConfig | None, callbacks: Any | None) -> RunnableConfig | None:
        if callbacks is None:
            return config
        merged: dict[str, Any]
        if config is None:
            merged = {}
        elif isinstance(config, dict):
            merged = dict(config)
        else:
            merged = dict(config)
        merged["callbacks"] = callbacks
        return merged

    def invoke(self, input: Any, config: RunnableConfig | None = None, *, stop: list[str] | None = None, callbacks: Any | None = None, **kwargs: Any):
        config = self._merge_callback_config(config, callbacks)
        return super().invoke(input, config=config, stop=stop, **kwargs)

    async def ainvoke(self, input: Any, config: RunnableConfig | None = None, *, stop: list[str] | None = None, callbacks: Any | None = None, **kwargs: Any):
        config = self._merge_callback_config(config, callbacks)
        return await super().ainvoke(input, config=config, stop=stop, **kwargs)


class TerminalCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print("[Agente] Consultando LLM...", flush=True)

    def on_llm_end(self, response, **kwargs):
        print("[Agente] LLM respondeu.", flush=True)

    def on_tool_start(self, serialized, input_str, **kwargs):
        nome = serialized.get("name", "ferramenta")
        print(f"[Agente] Executando tool '{nome}'...", flush=True)

    def on_tool_end(self, output, **kwargs):
        print("[Agente] Tool concluída.", flush=True)


def _carregar_system_prompt() -> str:
    if not config.SYSTEM_PROMPT_FILE.is_file():
        raise FileNotFoundError(f"Arquivo de system prompt não encontrado em '{config.SYSTEM_PROMPT_FILE}'.")
    template = config.SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    contexto = {
        "frontend_legado": str(config.PROJECT_PATHS.get("frontend_legado") or ""),
        "frontend_atual": str(config.PROJECT_PATHS.get("frontend_atual") or ""),
        "backend_atual": str(config.PROJECT_PATHS.get("backend_atual") or ""),
        "backend_legado": str(config.PROJECT_PATHS.get("backend_legado") or ""),
        "use_case_section": config.format_use_case_descriptions(),
    }
    return template.format(**contexto)


SYSTEM_PROMPT = _carregar_system_prompt()


def _obter_limite_agente(variavel: str, padrao: int) -> int:
    valor = os.getenv(variavel)
    if not valor:
        return padrao
    try:
        convertido = int(valor)
    except ValueError:
        return padrao
    return convertido if convertido > 0 else padrao


def build_rag_chain(rag_history: list[tuple[str, str]]) -> ConversationalRetrievalChain:
    embeddings = OpenAIEmbeddings()
    vector_store = Chroma(persist_directory=str(config.DB_DIR), embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    llm = LegacyChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )


def build_react_agent(rag_history: list[tuple[str, str]]):
    rag_chain = build_rag_chain(rag_history)

    @tool("consultar_documentacao")
    def consultar_documentacao(pergunta: str) -> str:
        """Consulta a base RAG usando o histórico atual e devolve fontes."""
        resultado = rag_chain.invoke({"question": pergunta, "chat_history": rag_history})
        fontes = resultado.get("source_documents", [])
        referencias = "\n".join(sorted({doc.metadata.get("source", "desconhecido") for doc in fontes}))
        if referencias:
            return f"{resultado['answer']}\n\nFontes:\n{referencias}"
        return resultado["answer"]

    @tool("buscar_arquivos")
    def buscar_arquivos_tool(projeto: str, filtro: str) -> str:
        """Busca arquivos por nome dentro do projeto pedido."""
        return tools.buscar_arquivos(projeto, filtro)

    @tool("ler_arquivo")
    def ler_arquivo_tool(caminho: str) -> str:
        """Retorna o conteúdo (ou erro) do arquivo informado."""
        return tools.ler_arquivo(caminho)

    @tool("escrever_arquivo")
    def escrever_arquivo_tool(caminho: str, conteudo: str) -> str:
        """Substitui o conteúdo de um arquivo e registra a alteração."""
        return tools.escrever_arquivo(caminho, conteudo)

    @tool("criar_ou_atualizar_plano")
    def criar_ou_atualizar_plano_tool(projeto: str, nome_plano: str, conteudo: str) -> str:
        """
        Cria ou atualiza um arquivo de planejamento em docs/planejamentos.
        Use para registrar planos por etapas (ex.: 'Planejamento T6').
        """
        return tools.criar_ou_atualizar_plano(projeto, nome_plano, conteudo)

    @tool("registrar_decisao_arquitetura")
    def registrar_decisao_arquitetura_tool(
        titulo: str,
        contexto: str,
        decisao: str,
        consequencias: str | None = None,
    ) -> str:
        """
        Registra uma decisão de arquitetura em docs/decisoes_arquitetura.md.
        """
        return tools.registrar_decisao_arquitetura(
            titulo=titulo,
            contexto=contexto,
            decisao=decisao,
            consequencias=consequencias,
        )

    @tool("listar_projetos_configurados")
    def listar_projetos_configurados_tool() -> str:
        """
        Lista os projetos e aliases configurados no agente.
        """
        return tools.listar_projetos_configurados()


    agent_tools = [
        consultar_documentacao,
        buscar_arquivos_tool,
        ler_arquivo_tool,
        escrever_arquivo_tool,
        criar_ou_atualizar_plano_tool,
        registrar_decisao_arquitetura_tool,
        listar_projetos_configurados_tool,
    ]

    # def _react_model(_: Any, __: Any) -> LegacyChatOpenAI:
    #     return LegacyChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    
    llm = LegacyChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)

    agent = create_react_agent(
        # model=_react_model,
        model=llm,
        tools=agent_tools,
        prompt=SYSTEM_PROMPT,
        version="v2",
        name="agente_certidao",
    )
    return agent


class AgentState(TypedDict):
    input: str                   # pergunta atual do usuário
    answer: str                  # última resposta gerada pelo agente
    history: list[BaseMessage]   # histórico acumulado de mensagens (Human, AI, etc.)
    tarefa_atual: str | None     # ex: "T6"
    caso_uso: str | None         # ex: "usc_04_142"
    prioridade: str | None       # ex: "alta"
    planejamento_format: str | None  # ex: "todo" ou "topicos"
    prazo: str | None            # prazo (livre, formato string)
    integracoes_externas: str | None # integrações externas informadas pelo usuário
    implementado_frontend: str | None
    endpoints_backend: str | None
    regras_negocio: str | None



def build_graph_agent(rag_history: list[tuple[str, str]]):
    react_agent = build_react_agent(rag_history)
    max_iterations = _obter_limite_agente(
        "AGENT_MAX_ITERATIONS", config.DEFAULT_AGENT_MAX_ITERATIONS
    )

    def executar_agente(state: AgentState) -> AgentState:
        pergunta = state["input"]
        callback_handler = TerminalCallbackHandler()
        historia_anterior = state.get("history") or []

        confirmacoes = {
            "sim",
            "sim.",
            "yes",
            "claro",
            "pode fazer isso",
            "pode prosseguir",
            "prossiga",
        }
        pergunta_normalizada = pergunta.strip().lower()
        eh_confirmacao = pergunta_normalizada in confirmacoes

        ultimo_ai: AIMessage | None = None
        if historia_anterior:
            for msg in reversed(historia_anterior):
                if isinstance(msg, AIMessage):
                    ultimo_ai = msg
                    break

        context_parts: list[str] = []
        field_labels = [
            ("tarefa_atual", "Tarefa atual"),
            ("caso_uso", "Caso de uso"),
            ("prioridade", "Prioridade"),
            ("planejamento_format", "Formato de planejamento"),
            ("prazo", "Prazo"),
            ("integracoes_externas", "Integrações externas"),
            ("implementado_frontend", "Frontend implementado"),
            ("endpoints_backend", "Endpoints backend"),
            ("regras_negocio", "Regras de negócio"),
        ]
        for field, label in field_labels:
            valor = state.get(field)
            if valor:
                context_parts.append(f"{label}: {valor}")

        if eh_confirmacao and ultimo_ai:
            ultima_pergunta = ultimo_ai.content.strip()
            if ultima_pergunta.endswith("?") or "?" in ultima_pergunta:
                context_parts.append(
                    "Confirmação do usuário: aceitou a última sugestão do agente."
                )

        mensagens = historia_anterior.copy()
        if context_parts:
            context_text = " | ".join(context_parts)
            mensagens.insert(0, SystemMessage(content=context_text))

        mensagens.append(HumanMessage(content=pergunta))

        resultado = react_agent.invoke(
            {"messages": mensagens, "remaining_steps": max_iterations},
            config={"callbacks": [callback_handler]},
        )

        mensagens_resultado = resultado.get("messages", [])
        ultima_resposta = next(
            (m for m in reversed(mensagens_resultado) if isinstance(m, AIMessage)), None
        )
        answer = ultima_resposta.content if ultima_resposta else ""

        novo_historico = historia_anterior.copy()
        novo_historico.append(HumanMessage(content=pergunta))
        if ultima_resposta:
            novo_historico.append(ultima_resposta)

        rag_history.append((pergunta, answer))

        return {
            "input": pergunta,
            "answer": answer,
            "history": novo_historico,
            "tarefa_atual": state.get("tarefa_atual"),
            "caso_uso": state.get("caso_uso"),
            "prioridade": state.get("prioridade"),
            "planejamento_format": state.get("planejamento_format"),
            "prazo": state.get("prazo"),
            "integracoes_externas": state.get("integracoes_externas"),
            "implementado_frontend": state.get("implementado_frontend"),
            "endpoints_backend": state.get("endpoints_backend"),
            "regras_negocio": state.get("regras_negocio"),
        }

    graph = StateGraph(AgentState)
    graph.add_node("executar_agente", executar_agente)
    graph.set_entry_point("executar_agente")
    graph.add_edge("executar_agente", END)
    return graph.compile()
