"""Script de ingestão de documentos para o agente RAG."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / ".rag_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def load_documents() -> list[Document]:
    documents: list[Document] = []
    for file_path in DOCS_DIR.rglob("*"):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        metadata = {"source": str(file_path.relative_to(BASE_DIR))}
        enriched_text = f"Fonte: {metadata['source']}\n\n{text}"
        documents.append(Document(page_content=enriched_text, metadata=metadata))
    return documents


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    if not DOCS_DIR.exists():
        raise FileNotFoundError("Pasta docs/ não encontrada. Crie-a antes de executar a ingestão.")

    raw_documents = load_documents()
    if not raw_documents:
        raise RuntimeError("Nenhum documento encontrado na pasta docs/. Adicione arquivos e tente novamente.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(raw_documents)

    embeddings = OpenAIEmbeddings()
    DB_DIR.mkdir(exist_ok=True)
    Chroma.from_documents(chunks, embedding=embeddings, persist_directory=str(DB_DIR))

    print(f"Ingestão concluída. Documentos processados: {len(chunks)}")


if __name__ == "__main__":
    main()
