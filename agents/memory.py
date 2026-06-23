# -*- coding: utf-8 -*-
"""Agent 记忆模块。

- 短期记忆：LangGraph Checkpointer 按 thread_id 持久化对话状态（messages），
  Agent 每轮自动看到完整历史；
- 跨会话持久化：SqliteSaver 落盘 data/agent_memory.sqlite，应用重启后会话可恢复；
- 会话注册表：data/chat_threads.json 记录会话 ID/标题/创建时间，供前端会话列表展示。
"""
import json
import sqlite3
import time
import uuid

from langgraph.checkpoint.sqlite import SqliteSaver

from config import PROJECT_ROOT

_DB_PATH = PROJECT_ROOT / "data" / "agent_memory.sqlite"
_THREADS_FILE = PROJECT_ROOT / "data" / "chat_threads.json"

_checkpointer: SqliteSaver | None = None


def get_checkpointer() -> SqliteSaver:
    """进程内单例的 SQLite Checkpointer（check_same_thread=False 兼容 Streamlit 多线程）。"""
    global _checkpointer
    if _checkpointer is None:
        conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _checkpointer = SqliteSaver(conn)
    return _checkpointer


# ---------- 会话注册表 ----------

def _load_threads() -> list[dict]:
    if _THREADS_FILE.exists():
        return json.loads(_THREADS_FILE.read_text(encoding="utf-8"))
    return []


def _save_threads(threads: list[dict]) -> None:
    _THREADS_FILE.write_text(json.dumps(threads, ensure_ascii=False, indent=2),
                             encoding="utf-8")


def list_threads() -> list[dict]:
    """返回全部会话，最新创建的在前。每项: {id, title, created}。"""
    return sorted(_load_threads(), key=lambda t: t["created"], reverse=True)


def create_thread() -> str:
    """新建会话并注册，返回 thread_id。"""
    thread_id = f"chat_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
    threads = _load_threads()
    threads.append({"id": thread_id, "title": "新会话",
                    "created": time.strftime("%Y-%m-%d %H:%M:%S")})
    _save_threads(threads)
    return thread_id


def set_thread_title(thread_id: str, title: str) -> None:
    """用首条用户消息为会话命名（仅在仍是默认标题时）。"""
    threads = _load_threads()
    for t in threads:
        if t["id"] == thread_id and t["title"] == "新会话":
            t["title"] = title[:20] + ("…" if len(title) > 20 else "")
            _save_threads(threads)
            return


def get_thread_messages(graph, thread_id: str) -> list:
    """从 Checkpointer 读取某会话的完整消息历史（LangChain Message 对象列表）。"""
    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", []) if state and state.values else []


def delete_thread(thread_id: str) -> None:
    """删除会话：清除 SQLite 中该会话的全部对话状态，并从注册表移除。"""
    cp = get_checkpointer()
    try:
        cp.delete_thread(thread_id)
    except AttributeError:
        # 旧版 checkpointer 没有 delete_thread，直接清理底层表
        with cp.lock:
            cp.conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            cp.conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            cp.conn.commit()
    _save_threads([t for t in _load_threads() if t["id"] != thread_id])
