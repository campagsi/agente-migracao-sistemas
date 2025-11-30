import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
BASE_DIR = PACKAGE_DIR.parent
load_dotenv(BASE_DIR / ".env")

CONFIG_PATH = Path(os.getenv("AGENT_CONFIG_PATH") or Path("config/agent_config.json"))
if not CONFIG_PATH.is_absolute():
    CONFIG_PATH = (BASE_DIR / CONFIG_PATH).resolve()


def _load_agent_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[Aviso] Não foi possível decodificar {path}: {exc}")
        return {}


AGENT_CONFIG = _load_agent_config(CONFIG_PATH)

DEFAULT_PROJECT_DIRS: dict[str, str] = {
    "frontend_atual": "/home/rafael/Documentos/ProdabelProjects/certidao-imobiliaria-novo-frontend/",
    "backend_atual": "/home/rafael/Documentos/ProdabelProjects/certidao-imobiliaria-backend/",
    "frontend_legado": "/home/rafael/Documentos/ProdabelProjects/cadastro-imobiliario-frontend-fontes/",
    "backend_legado": "",
}

DEFAULT_PROJECT_FRAMEWORKS: dict[str, str] = {
    "frontend_atual": "Vue 3 (Composition + PiVue)",
    "backend_atual": "NestJS",
    "frontend_legado": "Vue 2 (Legacy)",
    "backend_legado": "NestJS Legacy",
}

DEFAULT_PROJECT_ALIAS_GROUPS: dict[str, list[str]] = {
    "frontend_legado": ["vue2", "frontend_legado", "legado_vue2"],
    "frontend_atual": ["vue3", "frontend_atual", "novo_vue3"],
    "backend_atual": ["backend", "backend_atual", "nestjs", "api", "backend_nestjs"],
    "backend_legado": ["backend_legado", "legacy_backend", "antigo_backend"],
}

DEFAULT_USE_CASE_ALIAS_GROUPS: dict[str, list[str]] = {
    "usc_04_142": [
        "usc_04_142",
        "usc04142",
        "usc.04.142",
        "pesquisa_de_protocolos",
        "pesquisa_protocolos",
        "pesquisa_de_certidoes",
    ],
    "usc_04_143": [
        "usc_04_143",
        "usc04143",
        "usc.04.143",
        "criar_certidao",
        "criacao_certidao",
    ],
    "usc_04_144": [
        "usc_04_144",
        "usc04144",
        "usc.04.144",
        "emissao_certidao",
        "emitir_certidao",
    ],
}

DEFAULT_USE_CASE_BACKEND_HINTS: dict[str, list[str]] = {
    "usc_04_142": [
        "consulta.controller.ts",
        "consulta.service.ts",
        "consulta.repository.ts",
        "consulta-emissao-certidao.dto.ts",
        "imobiliario-legacy.controller.ts",
        "imobiliario-legacy.service.ts",
        "imobiliario-legacy.repository.ts",
    ],
    "usc_04_143": [
        "cert-imobiliaria.controller.ts",
        "cert-imobiliaria.service.ts",
        "certidao.repository.ts",
        "create-certidao.dto.ts",
        "create-certidao-base.dto.ts",
        "numero-protocolo.dto.ts",
    ],
    "usc_04_144": [
        "cert-imobiliaria.controller.ts",
        "cert-imobiliaria.service.ts",
        "imobiliario-legacy.controller.ts",
        "imobiliario-legacy.service.ts",
        "imobiliario-legacy.repository.ts",
        "download-arquivo.dto.ts",
    ],
}

DEFAULT_USE_CASE_DESCRIPTIONS: dict[str, list[str]] = {
    "usc_04_142": [
        "Reproduzir todos os filtros, forma de exibição e comportamento do projeto antigo."
    ],
    "usc_04_143": ["Reproduzir abas e comportamento do projeto antigo."],
    "usc_04_144": [
        "Criar as abas: Dados Gerais, Dados Complementares, Arquivos, Histórico e Indeferimento.",
        "Reproduzir o botão “Carregar dados de outra certidão” com a mesma funcionalidade do legado.",
    ],
}

USE_CASE_DESCRIPTIONS: dict[str, list[str]] = AGENT_CONFIG.get(
    "useCaseDescriptions", DEFAULT_USE_CASE_DESCRIPTIONS
)

PROJECT_DIRS: dict[str, str] = AGENT_CONFIG.get("projectDirs", DEFAULT_PROJECT_DIRS)
PROJECT_FRAMEWORKS: dict[str, str] = AGENT_CONFIG.get(
    "projectFrameworks", DEFAULT_PROJECT_FRAMEWORKS
)


def _path_from_env(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser().resolve(strict=False)


PROJECT_PATHS: dict[str, Path | None] = {
    chave: _path_from_env(valor) for chave, valor in PROJECT_DIRS.items()
}
PROJECT_ALIAS_GROUPS: dict[str, list[str]] = AGENT_CONFIG.get(
    "projectAliasGroups", DEFAULT_PROJECT_ALIAS_GROUPS
)
USE_CASE_ALIAS_GROUPS: dict[str, list[str]] = AGENT_CONFIG.get(
    "useCaseAliasGroups", DEFAULT_USE_CASE_ALIAS_GROUPS
)
USE_CASE_BACKEND_HINTS: dict[str, list[str]] = AGENT_CONFIG.get(
    "useCaseBackendHints", DEFAULT_USE_CASE_BACKEND_HINTS
)
USE_CASE_DESCRIPTIONS: dict[str, list[str]] = AGENT_CONFIG.get(
    "useCaseDescriptions", DEFAULT_USE_CASE_DESCRIPTIONS
)

DB_DIR = BASE_DIR / ".rag_db"
DOCS_DIR = BASE_DIR / "docs"
TASKS_FILE = DOCS_DIR / "todo.md"
EXECUCOES_DIR = DOCS_DIR / "execucoes"
ARQUIVOS_ALTERADOS_FILE = DOCS_DIR / "arquivos_alterados.md"
SYSTEM_PROMPT_FILE = DOCS_DIR / "system_prompt.md"

MAX_ARQUIVO_CARACTERES = 15000
ALTERACOES_ATUAIS: set[str] = set()

DEFAULT_AGENT_MAX_ITERATIONS = 100
DEFAULT_AGENT_MAX_EXECUTION_TIME = 280


def format_use_case_descriptions() -> str:
    linhas: list[str] = []
    for caso in sorted(USE_CASE_DESCRIPTIONS.keys()):
        descricao = USE_CASE_DESCRIPTIONS[caso]
        linhas.append(f"- **{caso.upper()}**")
        for item in descricao:
            linhas.append(f"  - {item}")
    return "\n".join(linhas)
