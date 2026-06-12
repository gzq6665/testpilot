# -*- coding: utf-8 -*-
"""全局配置：模型、路径、被测系统地址。"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# ---------- Ollama ----------
OLLAMA_BASE_URL = "http://localhost:11434"
CHAT_MODEL = "qwen2.5:7b"        # 对话/Agent 主力模型（支持 Function Calling）
EMBED_MODEL = "bge-m3"           # 中文 Embedding 模型

# 16G 内存机器跑 7B 模型较紧：上下文窗口过大时 KV 缓存会导致加载失败
# （"model requires more system memory"）。如仍报内存不足，可换 CHAT_MODEL="qwen2.5:3b"
NUM_CTX = 4096        # 上下文窗口（token）
NUM_PREDICT = 2560    # 单次最大输出（token），需小于 NUM_CTX

# ---------- RAG ----------
DOCS_DIR = PROJECT_ROOT / "data" / "docs"
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
RETRIEVE_TOP_K = 5

# ---------- 被测系统 ----------
# 被测系统地址、登录方式、预置数据等已迁移到 Profile 配置档案（profiles.py），
# 通过平台「项目配置」页面管理，存放于 data/profiles/*.json

# ---------- MySQL（可选，未配置时 db_query 工具返回提示） ----------
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "",
}

# ---------- 输出 ----------
REPORTS_DIR = PROJECT_ROOT / "reports"
GENERATED_TESTS_DIR = PROJECT_ROOT / "tests_generated"

for _d in (DOCS_DIR, VECTOR_STORE_DIR, REPORTS_DIR, GENERATED_TESTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
