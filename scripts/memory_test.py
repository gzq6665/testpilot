# -*- coding: utf-8 -*-
"""记忆功能验证：
1. 同一 thread_id 两轮对话，第二轮提问依赖第一轮信息（短期记忆）；
2. 重新构建 Agent（模拟重启）后读取历史，验证 SQLite 持久化（跨会话记忆）。

运行: python scripts/memory_test.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from agents.executor import get_react_agent
from agents.memory import create_thread, get_thread_messages

thread_id = create_thread()
config = {"configurable": {"thread_id": thread_id}}
print(f"会话: {thread_id}")

agent = get_react_agent()

print("\n=== 第1轮：告知信息 ===")
out1 = agent.invoke({"messages": [("user", "我叫小郭，我负责测试登录模块。请记住这一点，并回复收到。")]}, config=config)
print("AI:", out1["messages"][-1].content)

print("\n=== 第2轮：考察记忆（只发新消息，不带历史） ===")
out2 = agent.invoke({"messages": [("user", "我叫什么名字？我负责测试哪个模块？")]}, config=config)
reply = out2["messages"][-1].content
print("AI:", reply)
assert ("小郭" in reply) and ("登录" in reply), "Agent 没有记住第一轮的信息！"
print("短期记忆验证通过 ✔")

print("\n=== 第3轮：模拟重启（重建 Agent 实例）后读取历史 ===")
agent2 = get_react_agent()
history = get_thread_messages(agent2, thread_id)
print(f"从 SQLite 恢复到 {len(history)} 条历史消息")
assert len(history) >= 4, "历史消息未持久化！"
out3 = agent2.invoke({"messages": [("user", "再说一次我的名字。")]}, config=config)
reply3 = out3["messages"][-1].content
print("AI:", reply3)
assert "小郭" in reply3, "重启后 Agent 丢失记忆！"
print("跨会话持久化验证通过 ✔")
