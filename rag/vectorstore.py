# -*- coding: utf-8 -*-
"""FAISS 向量库的构建与加载（按 Profile 独立索引）。

注意：faiss 的 C++ 文件 IO 在 Windows 上无法处理含中文的路径，
因此这里使用 serialize_to_bytes / deserialize_from_bytes 配合
Python 原生文件读写完成持久化。
"""
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

from config import EMBED_MODEL, OLLAMA_BASE_URL, RETRIEVE_TOP_K, VECTOR_STORE_DIR
from profiles import get_active_id, profile_docs_dir

from .loader import load_documents, split_documents

_cache: dict[str, FAISS] = {}


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)


def _index_file(pid: str):
    return VECTOR_STORE_DIR / f"{pid}.pkl"


def build_vector_store(pid: str | None = None) -> FAISS:
    """从当前 Profile 的文档目录全量重建向量库并持久化。"""
    pid = pid or get_active_id()
    chunks = split_documents(load_documents(profile_docs_dir(pid)))
    if not chunks:
        raise RuntimeError(f"项目 [{pid}] 的文档目录为空，请先在「接口文档问答」页面上传接口文档")
    vs = FAISS.from_documents(chunks, get_embeddings())
    _index_file(pid).write_bytes(vs.serialize_to_bytes())
    _cache[pid] = vs
    return vs


def load_vector_store(pid: str | None = None) -> FAISS:
    """加载当前 Profile 的向量库（带内存缓存），不存在则自动构建。"""
    pid = pid or get_active_id()
    if pid in _cache:
        return _cache[pid]
    f = _index_file(pid)
    if f.exists():
        _cache[pid] = FAISS.deserialize_from_bytes(
            f.read_bytes(), get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        return _cache[pid]
    return build_vector_store(pid)


def retrieve_context(query: str, k: int = RETRIEVE_TOP_K, pid: str | None = None) -> str:
    """在当前 Profile 的知识库中检索相关文档片段，拼接为上下文字符串。"""
    vs = load_vector_store(pid)
    docs = vs.similarity_search(query, k=k)
    return "\n\n---\n\n".join(
        f"[来源: {d.metadata.get('source', '?')}]\n{d.page_content}" for d in docs
    )
