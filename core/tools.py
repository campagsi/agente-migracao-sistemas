from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from . import config
from .utils import (
    eh_backend,
    identificar_caso_uso,
    registrar_alteracao,
    resolver_projeto_busca,
)


def ler_arquivo(caminho: str) -> str:
    if not caminho:
        return "Erro: nenhum caminho informado."
    caminho_real = Path(caminho).expanduser()
    if not caminho_real.is_file():
        return f"Erro: o arquivo '{caminho_real}' não existe."
    try:
        conteudo = caminho_real.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Erro: não foi possível decodificar '{caminho_real}' como UTF-8."
    if len(conteudo) > config.MAX_ARQUIVO_CARACTERES:
        trecho = conteudo[: config.MAX_ARQUIVO_CARACTERES]
        aviso = (
            f"Arquivo '{caminho_real}' possui {len(conteudo)} caracteres; "
            f"retornando apenas os primeiros {config.MAX_ARQUIVO_CARACTERES}. "
            "Solicite trechos específicos se precisar do restante."
        )
        return f"{aviso}\n\n{trecho}"
    return conteudo


def escrever_arquivo(caminho: str, conteudo: str) -> str:
    if not caminho:
        return "Erro: nenhum caminho informado."
    caminho_real = Path(caminho).expanduser()
    caminho_real.parent.mkdir(parents=True, exist_ok=True)
    caminho_real.write_text(conteudo, encoding="utf-8")
    registrar_alteracao(caminho_real)
    return conteudo


def _coletar_arquivos_por_nome(
    raiz: Path, filtro: str, limite: int = 40
) -> Tuple[List[str], bool, str | None]:
    if not raiz.exists():
        return [], False, f"Erro: diretório '{raiz}' não encontrado."
    filtro_normalizado = filtro.lower().strip()
    if not filtro_normalizado:
        return [], False, "Erro: informe um trecho do nome do arquivo a ser buscado."

    resultados: list[str] = []
    atingiu_limite = False

    # pastas que queremos ignorar em QUALQUER ponto do caminho
    IGNORAR_DIRS = {"node_modules", "modules", ".git", "dist", "build", "__pycache__"}

    try:
        for caminho in raiz.rglob("*"):
            # se qualquer parte do caminho for uma das pastas ignoradas, pula
            if any(part in IGNORAR_DIRS for part in caminho.parts):
                continue

            if caminho.is_file() and filtro_normalizado in caminho.name.lower():
                resultados.append(str(caminho))
                if len(resultados) >= limite:
                    atingiu_limite = True
                    break
    except PermissionError as exc:
        return [], False, f"Erro: permissão negada ao varrer '{raiz}': {exc}"
    return resultados, atingiu_limite, None


def _buscar_arquivos_em_diretorio(raiz: Path, filtro: str) -> str:
    resultados, atingiu_limite, erro = _coletar_arquivos_por_nome(raiz, filtro)
    if erro:
        return erro
    if not resultados:
        return f"Nenhum arquivo contendo '{filtro}' foi encontrado em {raiz}."
    resultado_lista = "\n".join(resultados)
    if atingiu_limite:
        resultado_lista += "\n... (limite de 40 resultados atingido)"
    return resultado_lista


def _buscar_arquivos_backend_por_filtro(filtro: str, raiz: Path) -> str:
    filtros = [filtro]
    caso_uso = identificar_caso_uso(filtro)
    fallback_usado = False
    if caso_uso:
        filtros.extend(config.USE_CASE_BACKEND_HINTS.get(caso_uso, []))
        fallback_usado = True

    encontrados: list[str] = []
    vistos: set[str] = set()
    atingiu_limite_global = False
    encontrou_principal = False

    for indice, termo in enumerate(filtros):
        parciais, atingiu_limite_local, erro = _coletar_arquivos_por_nome(raiz, termo)
        if erro:
            return erro
        if indice == 0 and parciais:
            encontrou_principal = True
        for caminho in parciais:
            if caminho in vistos:
                continue
            encontrados.append(caminho)
            vistos.add(caminho)
            if len(encontrados) >= 40:
                atingiu_limite_global = True
                break
        if atingiu_limite_global:
            break
        if atingiu_limite_local and len(encontrados) >= 40:
            atingiu_limite_global = True
            break

    if not encontrados:
        return f"Nenhum arquivo contendo '{filtro}' foi encontrado em {raiz}."

    resposta = "\n".join(encontrados)
    if atingiu_limite_global:
        resposta += "\n... (limite de 40 resultados atingido)"
    if fallback_usado and not encontrou_principal and caso_uso:
        resposta = (
            f"Nenhum arquivo contendo '{filtro}' foi encontrado diretamente. "
            f"Listando arquivos relacionados ao caso de uso {caso_uso.upper()}:\n"
            f"{resposta}"
        )
    return resposta


def buscar_arquivos(projeto: str, filtro: str) -> str:
    projeto_resolvido = resolver_projeto_busca(projeto)
    if not projeto_resolvido:
        opcoes = ", ".join(
            sorted(
                {
                    alias
                    for aliases in config.PROJECT_ALIAS_GROUPS.values()
                    for alias in aliases
                }
            )
        )
        return (
            "Erro: projeto não reconhecido. Informe um dos seguintes nomes ou aliases: "
            f"{opcoes}."
        )

    raiz = config.PROJECT_PATHS.get(projeto_resolvido)
    if not raiz:
        return f"Erro: o diretório do projeto '{projeto_resolvido}' não está configurado."

    if eh_backend(projeto_resolvido):
        return _buscar_arquivos_backend_por_filtro(filtro, raiz)

    return _buscar_arquivos_em_diretorio(raiz, filtro)

def _slugify_nome(nome: str) -> str:
    """Gera um slug simples, só com letras/números/minusculas e hífen."""
    if not nome:
        return "plano"
    nome = nome.strip().lower()
    slug_chars: list[str] = []
    for ch in nome:
        if ch.isalnum():
            slug_chars.append(ch)
        else:
            slug_chars.append("-")
    slug = "".join(slug_chars).strip("-")
    return slug or "plano"

def criar_ou_atualizar_plano(projeto: str, nome_plano: str, conteudo: str) -> str:
    """
    Cria ou atualiza um arquivo de planejamento em docs/planejamentos/<projeto>/<slug>.md.

    - `projeto`: nome ou alias do projeto (ex.: 'frontend', 'backend', 'certidao').
    - `nome_plano`: nome lógico do plano (ex.: 'Planejamento T6', 'Migração USC_04_142').
    - `conteudo`: conteúdo em markdown, normalmente gerado pelo LLM.
    """
    if not nome_plano:
        return "Erro: informe um nome para o plano."

    projeto_resolvido = resolver_projeto_busca(projeto)
    if not projeto_resolvido:
        # Se não reconhecer o projeto, joga em uma pasta 'geral'
        projeto_resolvido = "geral"

    try:
        base_docs: Path = getattr(config, "DOCS_DIR", Path("docs"))
    except Exception:
        base_docs = Path("docs")

    slug = _slugify_nome(nome_plano)
    caminho_plano = base_docs / "planejamentos" / projeto_resolvido / f"{slug}.md"
    caminho_plano.parent.mkdir(parents=True, exist_ok=True)

    # Se já existir, sobrescreve com a nova versão (replanejamento).
    cabecalho = f"# {nome_plano}\n\n"
    if not conteudo.strip():
        conteudo_final = cabecalho + "_(plano criado sem conteúdo; preencha posteriormente)_\n"
    else:
        conteudo_final = cabecalho + conteudo.strip() + "\n"

    caminho_plano.write_text(conteudo_final, encoding="utf-8")
    registrar_alteracao(caminho_plano)

    return (
        "Plano salvo com sucesso.\n"
        f"Projeto: {projeto_resolvido}\n"
        f"Arquivo: {caminho_plano}"
    )


def registrar_decisao_arquitetura(
    titulo: str,
    contexto: str,
    decisao: str,
    consequencias: str | None = None,
) -> str:
    """
    Registra uma decisão de arquitetura em docs/decisoes_arquitetura.md.

    Cada chamada apende um bloco markdown com:
    - data/hora
    - título
    - contexto
    - decisão
    - consequências (opcional)
    """
    if not titulo:
        return "Erro: informe um título para a decisão."
    if not contexto:
        return "Erro: informe um contexto para a decisão."
    if not decisao:
        return "Erro: informe a descrição da decisão tomada."

    try:
        base_docs: Path = getattr(config, "DOCS_DIR", Path("docs"))
    except Exception:
        base_docs = Path("docs")

    caminho_decisoes = base_docs / "decisoes_arquitetura.md"
    caminho_decisoes.parent.mkdir(parents=True, exist_ok=True)

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    bloco = [
        "---",
        f"**Data/Hora:** {agora}",
        f"**Título:** {titulo.strip()}",
        "",
        "### Contexto",
        contexto.strip(),
        "",
        "### Decisão",
        decisao.strip(),
    ]

    if consequencias and consequencias.strip():
        bloco.extend(
            [
                "",
                "### Consequências",
                consequencias.strip(),
            ]
        )

    bloco.extend(["", ""])  # linha em branco final

    with caminho_decisoes.open("a", encoding="utf-8") as f:
        f.write("\n".join(bloco))

    registrar_alteracao(caminho_decisoes)

    return f"Decisão registrada em: {caminho_decisoes}"


def listar_projetos_configurados() -> str:
    """
    Lista projetos configurados em config.PROJECT_PATHS e seus aliases
    em config.PROJECT_ALIAS_GROUPS.
    """
    linhas: list[str] = []

    projetos = getattr(config, "PROJECT_PATHS", {}) or {}
    aliases = getattr(config, "PROJECT_ALIAS_GROUPS", {}) or {}

    if not projetos:
        return "Nenhum projeto configurado em config.PROJECT_PATHS."

    linhas.append("Projetos configurados:\n")
    for nome, caminho in projetos.items():
        linhas.append(f"- **{nome}** → {caminho}")

        # Procura aliases que apontam para esse projeto
        aliases_projeto = [
            alias
            for key, group in aliases.items()
            if key == nome
            for alias in group
        ]
        if aliases_projeto:
            linhas.append(f"  - Aliases: {', '.join(sorted(set(aliases_projeto)))}")

    return "\n".join(linhas)
