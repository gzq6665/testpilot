# -*- coding: utf-8 -*-
"""用例生成 Agent：基于 RAG 检索的接口文档上下文，生成结构化测试用例。

业务相关的约定（响应风格、预置账号、数据隔离规则）不写死在 Prompt 里，
而是从当前激活的被测系统 Profile 动态注入，支持任意系统接入。
"""
from langchain_core.prompts import ChatPromptTemplate

from profiles import STATUS_HINTS, get_active_profile
from rag.vectorstore import retrieve_context

from .llm import get_llm, parse_json

_GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一名资深接口测试工程师，擅长根据接口文档设计高质量测试用例。\n"
     "要求：\n"
     "1. 用例必须覆盖三类场景：正常流程、异常流程（必填项缺失、参数非法、未登录等）、边界值。\n"
     "2. 严格依据文档中的接口路径、参数名、状态码设计，不要编造文档中不存在的接口或参数。\n"
     "3. 被测系统响应约定：{biz_conventions}。\n"
     "4. 测试环境与数据约定：{seed_notes}。需要登录态的用例在 precondition 中写明\"需要登录\"。\n"
     "5. {status_hint}。\n"
     "6. expected_keyword 必须严格取自文档中列出的状态码描述原文，"
     "严禁发明文档中不存在的提示语；文档未定义预期提示的场景，expected_keyword 留空字符串，只校验状态码。\n\n"
     "只输出 JSON 对象，结构如下：\n"
     '{{"cases": [{{"case_id": "TC_LOGIN_001", "title": "用例标题", '
     '"module": "所属模块", "case_type": "正常|异常|边界", "priority": "P0|P1|P2", '
     '"precondition": "前置条件，无则填空字符串", "api_path": "/member/public/login", '
     '"method": "POST", "params": {{"参数名": "参数值"}}, '
     '"expected_biz_status": 200, "expected_keyword": "登录成功"}}]}}'),
    ("human",
     "接口文档片段：\n{context}\n\n"
     "请为【{module}】设计 {num_cases} 条左右的接口测试用例。{feedback_part}"),
])


def generate_cases(module: str, num_cases: int = 8, feedback: str = "") -> dict:
    """返回 {cases: [...], context: str}。feedback 为评审 Agent 的改进意见（迭代时传入）。"""
    profile = get_active_profile()
    context = retrieve_context(f"{module} 接口 参数 状态码")
    feedback_part = (
        f"\n注意：上一轮用例未通过评审，请按以下意见改进后重新输出全部用例：\n{feedback}"
        if feedback else ""
    )
    chain = _GEN_PROMPT | get_llm(json_mode=True)
    inputs = {
        "context": context, "module": module,
        "num_cases": num_cases, "feedback_part": feedback_part,
        "biz_conventions": profile.get("biz_conventions") or "以接口文档说明为准",
        "seed_notes": profile.get("seed_notes") or "无特殊约定",
        "status_hint": STATUS_HINTS.get(profile.get("assert_style", "biz_status")),
    }
    cases = []
    for attempt in range(2):  # 解析失败或空结果时重试一次
        resp = chain.invoke(inputs)
        try:
            cases = parse_json(resp.content).get("cases", [])
        except ValueError:
            cases = []
        if cases:
            break
    # 兜底规范化，避免缺字段导致下游执行报错
    for i, c in enumerate(cases, 1):
        c.setdefault("case_id", f"TC_{i:03d}")
        c.setdefault("method", "POST")
        c.setdefault("params", {})
        c.setdefault("precondition", "")
        c.setdefault("case_type", "正常")
        c.setdefault("priority", "P1")
        c.setdefault("expected_biz_status", 200)
        c.setdefault("expected_keyword", "")
    return {"cases": cases, "context": context}
