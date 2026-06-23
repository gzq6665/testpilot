# -*- coding: utf-8 -*-
"""端到端验证：LangGraph 多 Agent 工作流 + ReAct 工具调用 Agent。

运行: python scripts/workflow_test.py [--react-only|--flow-only]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

if "--react-only" not in sys.argv:
    print("=" * 20, "LangGraph 多 Agent 工作流", "=" * 20)
    from agents.workflow import run_workflow

    final = {}
    for node, update in run_workflow("登录接口", num_cases=5):
        final.update(update)
        if node == "generate":
            print(f"[generate] 第{update['iteration']}轮，生成 {len(update['cases'])} 条用例")
        elif node == "review":
            r = update["review"]
            print(f"[review] passed={r.get('passed')} score={r.get('score')} {r.get('summary','')[:80]}")
        elif node == "execute":
            p = sum(1 for x in update["results"] if x["passed"])
            print(f"[execute] {p}/{len(update['results'])} 通过")
            for x in update["results"]:
                print(f"   [{'PASS' if x['passed'] else 'FAIL'}] {x['case_id']} {x['title']} - {x['reason']}")
        elif node == "analyze":
            print(f"[analyze] 报告: {update['report_path']}")
            print(update["report"][:800])
    assert final.get("report"), "工作流未产出分析报告"
    print("\n工作流端到端通过 ✔")

if "--flow-only" not in sys.argv:
    print("\n" + "=" * 20, "ReAct 工具调用 Agent", "=" * 20)
    from agents.executor import get_react_agent

    agent = get_react_agent()
    instr = "用预置账号登录系统，然后调用 /member/public/islogin 验证登录态，告诉我结果"
    out = agent.invoke({"messages": [("user", instr)]})
    tool_called = any(getattr(m, "tool_calls", None) for m in out["messages"])
    print("是否发生了工具调用:", tool_called)
    print("Agent 最终回复:\n", out["messages"][-1].content)
    assert tool_called, "Agent 未调用任何工具（Function Calling 未生效）"
    print("\nReAct Agent 验证通过 ✔")
