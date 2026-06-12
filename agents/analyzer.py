# -*- coding: utf-8 -*-
"""失败分析 Agent：对执行结果做归因分类，生成测试报告与缺陷草稿。"""
import json

from langchain_core.prompts import ChatPromptTemplate

from .llm import get_llm

_ANALYZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一名资深测试开发工程师，负责分析接口自动化执行结果并输出测试报告。\n"
     "对每条失败用例进行归因，归因类别限定为：\n"
     "- 环境问题（连接失败、超时、服务未启动）\n"
     "- 疑似缺陷（接口返回与文档约定不符）\n"
     "- 用例问题（用例本身的参数或预期结果设计错误）\n"
     "- 数据问题（测试数据冲突，如手机号已被注册）\n\n"
     "输出 Markdown 格式报告，结构：\n"
     "## 执行概览（总数/通过/失败/通过率）\n"
     "## 失败归因分析（逐条：用例ID、现象、归因类别、分析依据）\n"
     "## 缺陷报告草稿（仅对\"疑似缺陷\"类，给出：标题、严重级别、复现步骤、预期结果、实际结果）\n"
     "## 改进建议\n"
     "要求客观、具体，基于给出的数据，不要编造。"),
    ("human", "接口自动化执行结果如下：\n{results_json}"),
])


def analyze_results(results: list[dict]) -> str:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    summary = {
        "total": total, "passed": passed, "failed": total - passed,
        "pass_rate": f"{passed / total * 100:.1f}%" if total else "N/A",
        "results": results,
    }
    chain = _ANALYZE_PROMPT | get_llm()
    resp = chain.invoke({"results_json": json.dumps(summary, ensure_ascii=False, indent=1)})
    return resp.content
