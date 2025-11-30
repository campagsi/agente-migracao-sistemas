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
    try:
        for caminho in raiz.rglob("*"):
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
