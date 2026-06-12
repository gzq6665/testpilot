# -*- coding: utf-8 -*-
"""会话删除功能验证：写入真实checkpoint→删除→注册表与SQLite均清理。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import HumanMessage

from agents.executor import get_react_agent
from agents.memory import create_thread, delete_thread, get_thread_messages, list_threads

agent = get_react_agent()

# 1. 创建会话并不经 LLM 直接写入一条消息（update_state 会落 checkpoint 到 SQLite）
tid = create_thread()
config = {"configurable": {"thread_id": tid}}
agent.update_state(config, {"messages": [HumanMessage("删除功能测试消息")]})
assert any(t["id"] == tid for t in list_threads()), "会话未注册"
assert len(get_thread_messages(agent, tid)) == 1, "checkpoint 未写入"
print(f"已创建会话 {tid} 并写入 1 条消息")

# 2. 删除并验证两处均清理
delete_thread(tid)
assert not any(t["id"] == tid for t in list_threads()), "注册表未清理"
assert get_thread_messages(agent, tid) == [], "SQLite 对话状态未清理"
print("删除后：注册表已移除，SQLite 对话状态已清空")

print("\n会话删除功能验证通过 ✔")
