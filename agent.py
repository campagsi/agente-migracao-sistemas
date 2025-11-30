"""Entrypoint e re-exports do agente RAG."""

from core import cli, config, utils
from core.rag_agent import build_graph_agent
from core.utils import (
    anexar_registro_tasks,
    formatar_listas_alteracoes,
    registrar_alteracao,
    registrar_arquivos_alterados_resumido,
    registrar_relatorio_execucao,
)

BASE_DIR = config.BASE_DIR
ALTERACOES_ATUAIS = config.ALTERACOES_ATUAIS
DB_DIR = config.DB_DIR
DOCS_DIR = config.DOCS_DIR


def build_agent(rag_history: list[tuple[str, str]]):
    return build_graph_agent(rag_history)


if __name__ == "__main__":
    cli.run()
