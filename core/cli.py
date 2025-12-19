import sys

from . import config, documentation
from .rag_agent import build_graph_agent
from .utils import (
    anexar_registro_tasks,
    registrar_arquivos_alterados_resumido,
    registrar_relatorio_execucao,
    carregar_contexto_de_docs
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

def _verificar_documentacao_projetos() -> None:
    pendentes = documentation.listar_documentacao_pendente()
    if not pendentes:
        return

    print("⚠️  Não encontrei documentação em docs/projetos para alguns diretórios configurados:")
    for chave, _ in pendentes:
        caminho = config.PROJECT_PATHS.get(chave)
        caminho_txt = str(caminho) if caminho else "(não configurado)"
        print(f"- {chave}: {caminho_txt}")

    for chave, _ in pendentes:
        caminho = config.PROJECT_PATHS.get(chave)
        caminho_txt = str(caminho) if caminho else "(não configurado)"
        while True:
            resposta = input(f"Deseja gerar documentação base para '{chave}' ({caminho_txt}) agora? [s/N]: ").strip().lower()
            if resposta in {"s", "sim"}:
                try:
                    doc_path = documentation.gerar_documentacao_projeto(chave)
                except ValueError as exc:
                    print(f"Não foi possível gerar documentação de {chave}: {exc}")
                except Exception as exc:  # noqa: BLE001
                    print(f"Erro inesperado ao gerar documentação de {chave}: {exc}")
                else:
                    print(f"Documentação criada em {doc_path}. Execute `python ingest.py` após revisar o conteúdo.")
                break
            if resposta in {"n", "nao", "não", ""}:
                print(f"Ok, documentação de '{chave}' não será gerada agora.")
                break
            print("Resposta inválida. Digite 's' para gerar ou 'n' para pular.")


def run():
    _verificar_documentacao_projetos()

    if not config.DB_DIR.exists():
        print("Base vetorial não encontrada. Execute `python ingest.py` primeiro.")
        sys.exit(1)

    rag_history: list[tuple[str, str]] = []
    graph_app = build_graph_agent(rag_history)
    history: list = []
    
    ## context_state = {key: None for key in CONTEXT_FIELDS}
    ## carrega as decisoes registra em decisoes_arquitetura.md
    context_state = carregar_contexto_de_docs() 

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
            "__contador__": 0,
            **context_state,
        }
        novo_estado = graph_app.invoke(estado_inicial, config={"recursion_limit": 100})
        answer = novo_estado["answer"]

        print(f"Agente: {answer}\n")

        anexar_registro_tasks(pergunta, answer)
        arquivos_alterados = sorted(config.ALTERACOES_ATUAIS)
        registrar_relatorio_execucao(pergunta, answer, arquivos_alterados)
        registrar_arquivos_alterados_resumido(arquivos_alterados)

        context_state = {key: novo_estado.get(key) for key in CONTEXT_FIELDS}
        history = novo_estado.get("history", history)
