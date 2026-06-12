# -*- coding: utf-8 -*-
"""文档加载与切分：支持 md / txt / pdf。按 Profile 独立的文档目录加载。"""
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE


def load_documents(docs_dir: Path) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(docs_dir.glob("*")):
        if path.suffix.lower() in (".md", ".txt"):
            text = path.read_text(encoding="utf-8")
        elif path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            if reader.is_encrypted:
                reader.decrypt("")
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        else:
            continue
        docs.append(Document(page_content=text, metadata={"source": path.name}))
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", "；", " ", ""],
    )
    return splitter.split_documents(docs)
