from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from . import config
from .utils import registrar_alteracao


def _project_doc_path(project_key: str) -> Path:
    return config.PROJECT_DOCS_DIR / f"{project_key}.md"


def listar_documentacao_pendente() -> list[tuple[str, Path]]:
    pendentes: list[tuple[str, Path]] = []
    for chave, caminho in config.PROJECT_PATHS.items():
        if not caminho:
            continue
        doc_path = _project_doc_path(chave)
        if not doc_path.is_file():
            pendentes.append((chave, doc_path))
            continue
        try:
            conteudo = doc_path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            pendentes.append((chave, doc_path))
            continue
        if not conteudo:
            pendentes.append((chave, doc_path))
    return pendentes


def gerar_documentacao_projeto(project_key: str) -> Path:
    raiz = config.PROJECT_PATHS.get(project_key)
    if not raiz:
        raise ValueError(f"Projeto '{project_key}' não possui caminho configurado.")
    doc_path = _project_doc_path(project_key)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    conteudo = _montar_documentacao_projeto(project_key, raiz)
    doc_path.write_text(conteudo, encoding="utf-8")
    registrar_alteracao(doc_path)
    return doc_path


def _montar_documentacao_projeto(project_key: str, raiz: Path) -> str:
    titulo = project_key.replace("_", " ").title()
    stack = config.PROJECT_FRAMEWORKS.get(project_key, "Não especificado")
    readme = _extrair_readme(raiz)
    estrutura = _listar_estrutura_principal(raiz)
    dependencias = _formatar_dependencias(raiz)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    blocos: list[str] = [
        f"# Projeto {titulo}",
        "",
        f"- **Caminho local:** `{raiz}`",
        f"- **Stack declarada:** {stack}",
        f"- **Documento gerado automaticamente em:** {timestamp}",
        "",
        "> Revise e complemente este arquivo antes de rodar `python ingest.py` para atualizar a base RAG.",
        "",
        "## Visão geral",
        readme or "Documentação ainda não encontrada no repositório. Descreva aqui objetivo, contexto e integrações.",
        "",
        "## Estrutura principal",
        "```text",
        estrutura,
        "```",
        "",
        "## Tecnologias e dependências principais",
        dependencias or "- Nenhuma dependência identificada automaticamente.",
        "",
        "## Procedimentos sugeridos para ingestão",
        "- Mantenha esta documentação atualizada sempre que houver mudanças relevantes.",
        "- Após revisar, execute `python ingest.py` para incorporar este arquivo ao banco vetorial.",
        "- Registre decisões adicionais em `docs/decisoes_arquitetura.md` quando necessário.",
    ]
    return "\n".join(blocos).strip() + "\n"


def _extrair_readme(raiz: Path, limite: int = 4000) -> str | None:
    candidatos = [
        "README.md",
        "Readme.md",
        "readme.md",
        "README.MD",
        "README",
        "README.txt",
    ]
    for nome in candidatos:
        caminho = raiz / nome
        if caminho.is_file():
            try:
                conteudo = caminho.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            conteudo = conteudo.strip()
            if not conteudo:
                continue
            if len(conteudo) > limite:
                return conteudo[:limite].rsplit("\n", 1)[0] + "\n\n*(trecho truncado para 4000 caracteres)*"
            return conteudo
    return None


def _listar_estrutura_principal(raiz: Path, max_profundidade: int = 2, max_itens: int = 80) -> str:
    if not raiz or not raiz.exists():
        return "Diretório não encontrado no caminho configurado."

    linhas: list[str] = [f"{raiz.name or raiz}/"]
    contador = 0

    def caminhar(diretorio: Path, prefixo: str, profundidade: int) -> None:
        nonlocal contador
        if profundidade > max_profundidade or contador >= max_itens:
            return
        try:
            entradas = sorted(diretorio.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            linhas.append(f"{prefixo}|-- [sem permissão]")
            return
        for indice, entry in enumerate(entradas):
            if contador >= max_itens:
                linhas.append(f"{prefixo}|-- ... (limite de itens atingido)")
                return
            ultimo = indice == len(entradas) - 1
            conector = "`-- " if ultimo else "|-- "
            nome = f"{entry.name}/" if entry.is_dir() else entry.name
            linhas.append(f"{prefixo}{conector}{nome}")
            contador += 1
            if entry.is_dir():
                novo_prefixo = f"{prefixo}    " if ultimo else f"{prefixo}|   "
                caminhar(entry, novo_prefixo, profundidade + 1)

    caminhar(raiz, "", 1)
    return "\n".join(linhas)


def _formatar_dependencias(raiz: Path) -> str | None:
    blocos: list[str] = []

    pacote = raiz / "package.json"
    if pacote.is_file():
        try:
            dados = json.loads(pacote.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            dados = {}
        dependencias = dados.get("dependencies") or {}
        dev_dependencias = dados.get("devDependencies") or {}
        if dependencias:
            blocos.append(_formatar_lista_dependencias("Dependencies (npm)", dependencias.keys()))
        if dev_dependencias:
            blocos.append(_formatar_lista_dependencias("DevDependencies (npm)", dev_dependencias.keys()))

    requirements = raiz / "requirements.txt"
    if requirements.is_file():
        linhas = [
            linha.strip()
            for linha in requirements.read_text(encoding="utf-8").splitlines()
            if linha.strip() and not linha.strip().startswith("#")
        ]
        if linhas:
            blocos.append(_formatar_lista_dependencias("requirements.txt", linhas))

    return "\n\n".join(blocos) if blocos else None


def _formatar_lista_dependencias(titulo: str, itens: Iterable[str], limite: int = 20) -> str:
    itens_ordenados = sorted(itens)
    exibidos = itens_ordenados[:limite]
    linhas = [f"- **{titulo}:**"]
    for item in exibidos:
        linhas.append(f"  - {item}")
    if len(itens_ordenados) > limite:
        linhas.append(f"  - ... (+{len(itens_ordenados) - limite} dependências)")
    return "\n".join(linhas)
