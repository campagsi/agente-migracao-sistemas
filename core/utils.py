from datetime import datetime
from pathlib import Path
from typing import Tuple

from . import config

USE_CASE_ALIAS_MAP: dict[str, str] = {}
PROJECT_ALIAS_MAP: dict[str, str] = {}


def _normalizar_identificador(valor: str) -> str:
    return (
        valor.lower()
        .strip()
        .replace("-", "_")
        .replace(".", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )


for _caso, _aliases in config.USE_CASE_ALIAS_GROUPS.items():
    for _alias in _aliases:
        USE_CASE_ALIAS_MAP[_normalizar_identificador(_alias)] = _caso

for _projeto, _aliases in config.PROJECT_ALIAS_GROUPS.items():
    for _alias in _aliases:
        PROJECT_ALIAS_MAP[_normalizar_identificador(_alias)] = _projeto


def identificar_caso_uso(valor: str) -> str | None:
    return USE_CASE_ALIAS_MAP.get(_normalizar_identificador(valor))


def resolver_projeto_busca(valor: str) -> str | None:
    return PROJECT_ALIAS_MAP.get(_normalizar_identificador(valor))


def eh_backend(chave: str) -> bool:
    return chave.startswith("backend")


def _obter_nome_projeto(chave: str) -> str:
    stack = config.PROJECT_FRAMEWORKS.get(chave)
    if not stack:
        return chave.replace("_", " ").title()
    return f"{stack} ({chave})"


def _obter_grupos_projetos() -> list[Tuple[str, str]]:
    grupos: list[Tuple[str, str]] = []
    for chave in sorted(config.PROJECT_PATHS.keys()):
        raiz = config.PROJECT_PATHS[chave]
        if not raiz:
            continue
        grupos.append((_obter_nome_projeto(chave), str(raiz)))
    return grupos


def agrupar_alteracoes_por_contexto(arquivos: list[str]) -> list[Tuple[str, list[str]]]:
    grupos_base = _obter_grupos_projetos()
    agrupados: dict[str, list[str]] = {
        "Documentação do agente": [],
        **{nome: [] for nome, _ in grupos_base},
    }
    for caminho in arquivos:
        normalizado = str(Path(caminho).resolve(strict=False))
        encontrado = False
        for nome, raiz in grupos_base:
            if raiz and normalizado.startswith(raiz):
                agrupados[nome].append(normalizado)
                encontrado = True
                break
        if not encontrado:
            agrupados["Documentação do agente"].append(normalizado)
    resultado = [("Documentação do agente", sorted(agrupados["Documentação do agente"]))]
    resultado.extend((nome, sorted(agrupados[nome])) for nome, _ in grupos_base)
    return resultado


def formatar_listas_alteracoes(arquivos: list[str]) -> str:
    if not arquivos:
        return "- Nenhum arquivo alterado."
    blocos: list[str] = []
    for contexto, itens in agrupar_alteracoes_por_contexto(arquivos):
        if itens:
            corpo = "\n".join(f"- {item}" for item in itens)
        else:
            corpo = "- Nenhum arquivo alterado."
        blocos.append(f"**{contexto}:**\n{corpo}")
    return "\n\n".join(blocos)


def registrar_alteracao(caminho: Path) -> None:
    config.ALTERACOES_ATUAIS.add(str(caminho))


def anexar_registro_tasks(pergunta: str, resposta: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config.TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    bloco = (
        f"\n## Registro {timestamp}\n"
        f"- Pergunta: {pergunta}\n"
        "- Plano e ações técnicas:\n"
        f"{resposta.strip()}\n"
    )
    with config.TASKS_FILE.open("a", encoding="utf-8") as arquivo:
        arquivo.write(bloco)
    registrar_alteracao(config.TASKS_FILE)


def registrar_relatorio_execucao(pergunta: str, resposta: str, arquivos_alterados: list[str]) -> None:
    config.EXECUCOES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    relatorio = config.EXECUCOES_DIR / f"execucao_{timestamp}.md"
    arquivos_para_relatorio = list(arquivos_alterados)
    arquivos_para_relatorio.append(str(relatorio))
    lista = formatar_listas_alteracoes(arquivos_para_relatorio)
    conteudo = (
        f"# Execução {timestamp}\n\n"
        f"**Pergunta:** {pergunta}\n\n"
        f"**Resposta:**\n{resposta.strip()}\n\n"
        f"**Arquivos alterados:**\n{lista}\n"
    )
    relatorio.write_text(conteudo, encoding="utf-8")
    registrar_alteracao(relatorio)


def registrar_arquivos_alterados_resumido(arquivos_alterados: list[str]) -> None:
    if not arquivos_alterados:
        return
    config.ARQUIVOS_ALTERADOS_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lista = formatar_listas_alteracoes(arquivos_alterados)
    bloco = f"\n## Execução {timestamp}\n\n{lista}\n"
    with config.ARQUIVOS_ALTERADOS_FILE.open("a", encoding="utf-8") as f:
        f.write(bloco)
    registrar_alteracao(config.ARQUIVOS_ALTERADOS_FILE)
