import sys

from . import config
from .rag_agent import build_graph_agent
from .utils import (
    anexar_registro_tasks,
    registrar_arquivos_alterados_resumido,
    registrar_relatorio_execucao,
)

CONTEXT_FIELDS = [
    "tarefa_atual",
    "caso_uso",
    "prioridade",
    "planejamento_format",
    "prazo",
    "integracoes_externas",
    "implementado_frontend",
    "endpoints_backend",
    "regras_negocio",
]


def run():
    if not config.DB_DIR.exists():
        print("Base vetorial não encontrada. Execute `python ingest.py` primeiro.")
        sys.exit(1)

    rag_history: list[tuple[str, str]] = []
    graph_app = build_graph_agent(rag_history)
    history: list = []
    context_state = {key: None for key in CONTEXT_FIELDS}

    print("Agente RAG Certidão Imobiliária – digite 'sair' para encerrar.")

    while True:
        config.ALTERACOES_ATUAIS.clear()
        pergunta = input("Você: ").strip()
        if not pergunta:
            continue
        if pergunta.lower() in {"sair", "exit", "quit"}:
            print("Até mais!")
            break

        estado_inicial = {
            "input": pergunta,
            "answer": "",
            "history": history,
            **context_state,
        }
        novo_estado = graph_app.invoke(estado_inicial)
        answer = novo_estado["answer"]

        print(f"Agente: {answer}\n")

        anexar_registro_tasks(pergunta, answer)
        arquivos_alterados = sorted(config.ALTERACOES_ATUAIS)
        registrar_relatorio_execucao(pergunta, answer, arquivos_alterados)
        registrar_arquivos_alterados_resumido(arquivos_alterados)

        context_state = {key: novo_estado.get(key) for key in CONTEXT_FIELDS}
        history = novo_estado.get("history", history)
