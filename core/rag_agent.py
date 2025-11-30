import os
from typing import Any, Tuple, TypedDict

from langchain_classic.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent

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

    agent_tools = [
        consultar_documentacao,
        buscar_arquivos_tool,
        ler_arquivo_tool,
        escrever_arquivo_tool,
    ]

    def _react_model(_: Any, __: Any) -> LegacyChatOpenAI:
        return LegacyChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)

    agent = create_react_agent(
        model=_react_model,
        tools=agent_tools,
        prompt=SYSTEM_PROMPT,
        version="v2",
        name="agente_certidao",
    )
    return agent


class AgentState(TypedDict):
    input: str
    answer: str


def build_graph_agent(rag_history: list[tuple[str, str]]):
    react_agent = build_react_agent(rag_history)
    max_iterations = _obter_limite_agente(
        "AGENT_MAX_ITERATIONS", config.DEFAULT_AGENT_MAX_ITERATIONS
    )

    def executar_agente(state: AgentState) -> AgentState:
        pergunta = state["input"]
        callback_handler = TerminalCallbackHandler()
        mensagens = [
            HumanMessage(content=pergunta),
        ]
        resultado = react_agent.invoke(
            {"messages": mensagens, "remaining_steps": max_iterations},
            config={"callbacks": [callback_handler]},
        )
        mensagens_resultado = resultado.get("messages", [])
        ultima_resposta = next(
            (m for m in reversed(mensagens_resultado) if isinstance(m, AIMessage)), None
        )
        answer = ultima_resposta.content if ultima_resposta else ""
        rag_history.append((pergunta, answer))
        return {"input": pergunta, "answer": answer}

    graph = StateGraph(AgentState)
    graph.add_node("executar_agente", executar_agente)
    graph.set_entry_point("executar_agente")
    graph.add_edge("executar_agente", END)
    return graph.compile()
