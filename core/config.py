import json
import os
from pathlib import Path
from typing import Any, TypedDict

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent
load_dotenv(BASE_DIR / ".env")

CONFIG_PATH = Path(os.getenv("AGENT_CONFIG_PATH") or Path("config/agent_config.json"))
if not CONFIG_PATH.is_absolute():
    CONFIG_PATH = (BASE_DIR / CONFIG_PATH).resolve()


def _load_agent_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração do agente não encontrado em '{path}'."
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Não foi possível decodificar o arquivo de configuração '{path}': {exc}."
        ) from exc


AGENT_CONFIG = _load_agent_config(CONFIG_PATH)


class ContextDefinition(TypedDict):
    aliases: list[str]
    descriptions: list[str]
    hints: dict[str, list[str]]


def _require_config_section(section: str) -> dict[str, Any]:
    value = AGENT_CONFIG.get(section)
    if value is None:
        raise RuntimeError(
            f"Configuração obrigatória '{section}' ausente em '{CONFIG_PATH}'."
        )
    if not isinstance(value, dict):
        raise RuntimeError(
            f"Esperado um objeto para '{section}' em '{CONFIG_PATH}', mas foi recebido {type(value).__name__}."
        )
    return value


def _require_str_mapping(section: str) -> dict[str, str]:
    mapping = _require_config_section(section)
    result: dict[str, str] = {}
    for key, value in mapping.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise RuntimeError(
                f"Todos os pares de '{section}' devem ser strings no arquivo '{CONFIG_PATH}'."
            )
        result[key] = value
    return result


def _require_str_list_mapping(section: str) -> dict[str, list[str]]:
    mapping = _require_config_section(section)
    result: dict[str, list[str]] = {}
    for key, value in mapping.items():
        if not isinstance(key, str) or not isinstance(value, list):
            raise RuntimeError(
                f"Entradas de '{section}' devem mapear strings para listas em '{CONFIG_PATH}'."
            )
        if not all(isinstance(item, str) for item in value):
            raise RuntimeError(
                f"Todos os itens das listas em '{section}' precisam ser strings em '{CONFIG_PATH}'."
            )
        result[key] = value
    return result


PROJECT_DIRS: dict[str, str] = _require_str_mapping("projectDirs")
PROJECT_FRAMEWORKS: dict[str, str] = _require_str_mapping("projectFrameworks")


def _path_from_env(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser().resolve(strict=False)


PROJECT_PATHS: dict[str, Path | None] = {
    chave: _path_from_env(valor) for chave, valor in PROJECT_DIRS.items()
}

PROJECT_ALIAS_GROUPS: dict[str, list[str]] = _require_str_list_mapping(
    "projectAliasGroups"
)


def _ensure_str_list(value: Any, contexto: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RuntimeError(
            f"O campo '{contexto}' deve ser uma lista de strings em '{CONFIG_PATH}'."
        )
    if not all(isinstance(item, str) for item in value):
        raise RuntimeError(
            f"Todos os itens de '{contexto}' devem ser strings em '{CONFIG_PATH}'."
        )
    return value


def _parse_context_definitions(section: str) -> dict[str, ContextDefinition]:
    raw = _require_config_section(section)
    contexts: dict[str, ContextDefinition] = {}
    for nome, dados in raw.items():
        if not isinstance(dados, dict):
            raise RuntimeError(
                f"As entradas de '{section}' devem ser objetos; '{nome}' não é válido."
            )
        aliases = _ensure_str_list(dados.get("aliases", []), f"{section}.{nome}.aliases")
        descriptions = _ensure_str_list(
            dados.get("descriptions", []), f"{section}.{nome}.descriptions"
        )
        hints_raw = dados.get("hints", {})
        if hints_raw is None:
            hints_raw = {}
        if not isinstance(hints_raw, dict):
            raise RuntimeError(
                f"As dicas de '{section}.{nome}.hints' devem ser um objeto."
            )
        hints: dict[str, list[str]] = {}
        for hint_tipo, lista in hints_raw.items():
            hints[hint_tipo] = _ensure_str_list(
                lista, f"{section}.{nome}.hints.{hint_tipo}"
            )
        contexts[nome] = ContextDefinition(
            aliases=aliases,
            descriptions=descriptions,
            hints=hints,
        )
    return contexts


CONTEXT_DEFINITIONS: dict[str, ContextDefinition] = _parse_context_definitions(
    "contexts"
)
CONTEXT_ALIAS_GROUPS: dict[str, list[str]] = {
    chave: definicao["aliases"] for chave, definicao in CONTEXT_DEFINITIONS.items()
}
CONTEXT_HINTS: dict[str, dict[str, list[str]]] = {
    chave: definicao["hints"] for chave, definicao in CONTEXT_DEFINITIONS.items()
}
CONTEXT_DESCRIPTIONS: dict[str, list[str]] = {
    chave: definicao["descriptions"] for chave, definicao in CONTEXT_DEFINITIONS.items()
}
def _load_system_prompt_blocks(mapping: dict[str, str]) -> dict[str, str]:
    blocos: dict[str, str] = {}
    for chave, arquivo in mapping.items():
        caminho = Path(arquivo)
        if not caminho.is_absolute():
            caminho = (BASE_DIR / caminho).resolve()
        if not caminho.is_file():
            raise RuntimeError(
                f"Arquivo '{arquivo}' definido em 'systemPromptBlockFiles' não foi encontrado."
            )
        blocos[chave] = caminho.read_text(encoding="utf-8").strip()
    return blocos


SYSTEM_PROMPT_BLOCKS: dict[str, str] = _load_system_prompt_blocks(
    _require_str_mapping("systemPromptBlockFiles")
)

_AGENT_LIMITS = _require_config_section("agentLimits")


def _require_positive_int(config_section: dict[str, Any], field: str) -> int:
    value = config_section.get(field)
    if not isinstance(value, int) or value <= 0:
        raise RuntimeError(
            f"O campo '{field}' em 'agentLimits' deve ser um inteiro positivo em '{CONFIG_PATH}'."
        )
    return value

DB_DIR = BASE_DIR / ".rag_db"
DOCS_DIR = BASE_DIR / "docs"
TASKS_FILE = DOCS_DIR / "todo.md"
EXECUCOES_DIR = DOCS_DIR / "execucoes"
ARQUIVOS_ALTERADOS_FILE = DOCS_DIR / "arquivos_alterados.md"
SYSTEM_PROMPT_FILE = DOCS_DIR / "system_prompt.md"
PROJECT_DOCS_DIR = DOCS_DIR / "projetos"

MAX_ARQUIVO_CARACTERES = 15000
ALTERACOES_ATUAIS: set[str] = set()

AGENT_MAX_ITERATIONS = _require_positive_int(_AGENT_LIMITS, "maxIterations")
AGENT_MAX_EXECUTION_TIME = _require_positive_int(
    _AGENT_LIMITS, "maxExecutionTime"
)


def format_context_descriptions() -> str:
    linhas: list[str] = []
    for contexto in sorted(CONTEXT_DESCRIPTIONS.keys()):
        descricoes = CONTEXT_DESCRIPTIONS[contexto]
        linhas.append(f"- **{contexto.upper()}**")
        if descricoes:
            for item in descricoes:
                linhas.append(f"  - {item}")
        else:
            linhas.append("  - (sem descrição configurada)")
    return "\n".join(linhas)
