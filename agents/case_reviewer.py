# -*- coding: utf-8 -*-
"""用例评审 Agent：对生成的用例做覆盖度与正确性评审，输出是否通过及改进意见。"""
import json

from langchain_core.prompts import ChatPromptTemplate

from .llm import get_llm, parse_json

_REVIEW_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一名测试组长，负责评审接口测试用例的质量。评审维度：\n"
     "1. 场景覆盖：是否同时覆盖正常、异常（必填项缺失/参数非法/未登录）、边界场景；\n"
     "2. 与文档一致性：接口路径、参数名、预期业务状态码是否与文档相符；\n"
     "3. 用例要素完整性：标题、前置条件、参数、预期结果是否明确可执行。\n"
     "评分 0-100，低于 75 分视为不通过。\n\n"
     "只输出 JSON 对象：\n"
     '{{"passed": true, "score": 85, "summary": "总体评价", '
     '"issues": ["问题1", "问题2"], "missing_scenarios": ["缺失的场景"]}}'),
    ("human",
     "接口文档片段：\n{context}\n\n待评审用例（共 {n} 条）：\n{cases_json}"),
])


def review_cases(cases: list[dict], context: str) -> dict:
    chain = _REVIEW_PROMPT | get_llm(json_mode=True)
    resp = chain.invoke({
        "context": context, "n": len(cases),
        "cases_json": json.dumps(cases, ensure_ascii=False, indent=1),
    })
    data = parse_json(resp.content)
    data.setdefault("passed", True)
    data.setdefault("score", 0)
    data.setdefault("summary", "")
    data.setdefault("issues", [])
    data.setdefault("missing_scenarios", [])
    return data
