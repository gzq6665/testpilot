# -*- coding: utf-8 -*-
"""LangGraph 多 Agent 工作流：用例生成 → 评审 →（不通过则带意见重新生成，最多2轮）→ 执行 → 失败分析。

    ┌──────────┐     ┌──────────┐  不通过且未超迭代  ┌──────────┐
    │ generate │ ──> │  review  │ ─────────────────> │ generate │
    └──────────┘     └────┬─────┘                    └──────────┘
                          │ 通过或达到最大迭代
                          v
                    ┌──────────┐     ┌──────────┐
                    │ execute  │ ──> │ analyze  │ ──> END
                    └──────────┘     └──────────┘
"""
import json
import time
from typing import TypedDict

from langgraph.graph import END, StateGraph

from config import REPORTS_DIR

from .analyzer import analyze_results
from .case_generator import generate_cases
from .case_reviewer import review_cases
from .executor import execute_cases

MAX_REVIEW_ITERATIONS = 2


class TestState(TypedDict, total=False):
    module: str          # 待测模块，如 "登录接口"
    num_cases: int       # 期望用例数
    context: str         # RAG 检索到的文档上下文
    cases: list          # 生成的结构化用例
    review: dict         # 评审结果 {passed, score, issues, ...}
    iteration: int       # 已生成轮次
    results: list        # 执行结果
    report: str          # 分析报告 Markdown
    report_path: str     # 报告落盘路径
    pytest_path: str     # 自动生成的 pytest 回归脚本路径


def node_generate(state: TestState) -> TestState:
    feedback = ""
    if state.get("review") and not state["review"].get("passed", True):
        feedback = json.dumps(
            {"issues": state["review"].get("issues", []),
             "missing_scenarios": state["review"].get("missing_scenarios", [])},
            ensure_ascii=False)
    out = generate_cases(state["module"], state.get("num_cases", 8), feedback)
    return {"cases": out["cases"], "context": out["context"],
            "iteration": state.get("iteration", 0) + 1}


def node_review(state: TestState) -> TestState:
    return {"review": review_cases(state["cases"], state["context"])}


def route_after_review(state: TestState) -> str:
    if state["review"].get("passed", True) or state["iteration"] >= MAX_REVIEW_ITERATIONS:
        return "execute"
    return "generate"


def node_execute(state: TestState) -> TestState:
    return {"results": execute_cases(state["cases"])}


def node_analyze(state: TestState) -> TestState:
    report = analyze_results(state["results"])
    path = REPORTS_DIR / f"report_{time.strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(report, encoding="utf-8")
    # 同时落盘原始执行结果，便于追溯
    (path.with_suffix(".json")).write_text(
        json.dumps({"module": state["module"], "cases": state["cases"],
                    "review": state.get("review"), "results": state["results"]},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    # 将评审通过的最终用例导出为可复用的 pytest 回归脚本
    from tools.pytest_gen import generate_pytest_file
    pytest_path = generate_pytest_file(state["cases"], state["module"])
    return {"report": report, "report_path": str(path), "pytest_path": pytest_path}


def build_graph(with_memory: bool = True):
    g = StateGraph(TestState)
    g.add_node("generate", node_generate)
    g.add_node("review", node_review)
    g.add_node("execute", node_execute)
    g.add_node("analyze", node_analyze)

    g.set_entry_point("generate")
    g.add_edge("generate", "review")
    g.add_conditional_edges("review", route_after_review,
                            {"execute": "execute", "generate": "generate"})
    g.add_edge("execute", "analyze")
    g.add_edge("analyze", END)

    checkpointer = None
    if with_memory:
        from .memory import get_checkpointer
        checkpointer = get_checkpointer()  # 每个节点完成后状态落盘，支持断点追溯
    return g.compile(checkpointer=checkpointer)


def run_workflow(module: str, num_cases: int = 8):
    """以流式方式运行工作流，逐节点 yield (node_name, state_update)，便于前端展示进度。

    每次运行使用独立 thread_id（wf_时间戳），节点级状态由 Checkpointer 持久化，
    可用于运行追溯或断点恢复。
    """
    graph = build_graph()
    config = {"configurable": {"thread_id": f"wf_{time.strftime('%Y%m%d_%H%M%S')}"}}
    for chunk in graph.stream({"module": module, "num_cases": num_cases},
                              config=config, stream_mode="updates"):
        for node_name, update in chunk.items():
            yield node_name, update
