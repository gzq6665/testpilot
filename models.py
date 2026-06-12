# -*- coding: utf-8 -*-
"""大模型配置管理：本地 Ollama 与 OpenAI 兼容 API 的注册、切换、删除。

模型注册表存于 data/models.json（含 API Key，已加入 .gitignore，勿提交仓库）。
- provider = "ollama"：本地 Ollama 模型（无需 API Key）
- provider = "openai"：任何 OpenAI 兼容 API（DeepSeek、通义千问、Kimi、GLM、OpenAI 等）

所有 Agent / 链通过 agents.llm.get_llm() 取模型，切换后全平台即时生效。
注意：RAG 的 Embedding 始终使用本地 Ollama 的 bge-m3，与对话模型互相独立。
"""
import json
import re
import time

from config import CHAT_MODEL, OLLAMA_BASE_URL, PROJECT_ROOT

_FILE = PROJECT_ROOT / "data" / "models.json"

_DEFAULT = {
    "active": "ollama_default",
    "models": [
        {
            "id": "ollama_default",
            "name": f"{CHAT_MODEL}（本地Ollama）",
            "provider": "ollama",
            "model": CHAT_MODEL,
            "base_url": OLLAMA_BASE_URL,
            "api_key": "",
        }
    ],
}


def _load() -> dict:
    if not _FILE.exists():
        _save(_DEFAULT)
    return json.loads(_FILE.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_models() -> list[dict]:
    return _load()["models"]


def get_active_model() -> dict:
    data = _load()
    for m in data["models"]:
        if m["id"] == data["active"]:
            return m
    return data["models"][0]


def set_active_model(mid: str) -> None:
    data = _load()
    if any(m["id"] == mid for m in data["models"]):
        data["active"] = mid
        _save(data)


def save_model(cfg: dict) -> dict:
    """新增或更新（同名覆盖）模型配置。"""
    data = _load()
    existing = next((m for m in data["models"] if m["name"] == cfg.get("name")), None)
    if existing:
        cfg["id"] = existing["id"]
        data["models"] = [cfg if m["id"] == existing["id"] else m for m in data["models"]]
    else:
        slug = re.sub(r"[^\w]+", "_", cfg.get("name", "model")).strip("_").lower()
        cfg["id"] = f"{slug or 'model'}_{int(time.time()) % 100000}"
        data["models"].append(cfg)
    _save(data)
    return cfg


def delete_model(mid: str) -> None:
    data = _load()
    if len(data["models"]) <= 1:
        raise ValueError("至少需要保留一个模型，不能删除最后一个")
    data["models"] = [m for m in data["models"] if m["id"] != mid]
    if data["active"] == mid:
        data["active"] = data["models"][0]["id"]
    _save(data)
