# -*- coding: utf-8 -*-
"""执行 Agent。

两种执行方式：
1. execute_cases —— 确定性执行器：逐条执行结构化用例并断言（工作流主链路用，结果可复现）；
2. get_react_agent —— ReAct 工具调用 Agent：LLM 通过 Function Calling 自主决定
   调用 http_request / db_query / reset_http_session 等工具，完成多步探索式测试。

被测系统地址、登录方式、断言风格均从当前激活的 Profile 读取。
"""
import json
import time

from langgraph.prebuilt import create_react_agent

from profiles import get_active_profile
from tools.db_tool import db_query
from tools.http_tool import do_request, http_request, reset_http_session, reset_session

from .llm import get_llm


def _do_login(profile: dict) -> dict | None:
    """按 Profile 配置执行登录，建立会话（处理"需要登录"前置条件）。"""
    login = profile.get("login") or {}
    if not login.get("path"):
        return None
    return do_request(login.get("method", "POST"), login["path"],
                      data=login.get("params") or {}, base_url=profile["base_url"],
                      body_format=profile.get("body_format", "form"))


def execute_cases(cases: list[dict], profile: dict | None = None) -> list[dict]:
    """逐条执行用例并断言，返回结果列表。"""
    profile = profile or get_active_profile()
    http_style = profile.get("assert_style") == "http_status"
    results = []
    for case in cases:
        start = time.time()
        reset_session()  # 每条用例从干净会话开始，避免登录态串扰
        if "登录" in (case.get("precondition") or ""):
            _do_login(profile)

        resp = do_request(case.get("method", "POST"), case.get("api_path", "/"),
                          data=case.get("params") or {}, base_url=profile["base_url"],
                          body_format=profile.get("body_format", "form"))
        elapsed = round((time.time() - start) * 1000)

        passed, reason = True, "断言通过"
        if not resp["ok"]:
            passed, reason = False, f"请求失败: {resp.get('error')}"
        else:
            body = resp["body"]
            expected = case.get("expected_biz_status")
            if http_style:
                actual = resp["http_status"]
            else:
                actual = body.get("status") if isinstance(body, dict) else None
            if expected is not None and actual != expected:
                kind = "HTTP状态码" if http_style else "业务状态码"
                passed, reason = False, f"{kind}不符: 期望 {expected}, 实际 {actual}"
            kw = case.get("expected_keyword") or ""
            if passed and kw and kw not in str(body):
                passed, reason = False, f"响应未包含关键字 [{kw}]"

        results.append({
            "case_id": case.get("case_id"),
            "title": case.get("title"),
            "case_type": case.get("case_type"),
            "api_path": case.get("api_path"),
            "method": case.get("method"),
            "params": case.get("params"),
            "expected_biz_status": case.get("expected_biz_status"),
            "expected_keyword": case.get("expected_keyword"),
            "passed": passed,
            "reason": reason,
            "response": resp.get("body") if resp["ok"] else resp.get("error"),
            "elapsed_ms": elapsed,
        })
    return results


def _react_system(profile: dict) -> str:
    login = profile.get("login") or {}
    login_desc = (
        f"{login.get('method', 'POST')} {login.get('path')}，"
        f"参数 {json.dumps(login.get('params') or {}, ensure_ascii=False)}"
        if login.get("path") else "（该项目未配置登录接口）"
    )
    return (
        f"你是一名接口测试执行 Agent，可以调用工具对被测系统【{profile['name']}】"
        f"（{profile['base_url']}）发起真实请求。\n"
        f"响应约定：{profile.get('biz_conventions') or '以接口文档为准'}\n"
        f"测试环境信息：{profile.get('seed_notes') or '无'}\n"
        f"登录方式：{login_desc}，会话 Cookie 自动保持。\n"
        "工作要求：\n"
        "0. 严格串行执行：一次只调用一个工具，等拿到结果后再决定下一步，禁止在同一轮并行调用多个工具；\n"
        "1. 需要登录态的接口，先调用 http_request 执行登录；\n"
        "2. 测试未登录场景前，先调用 reset_http_session 清除会话；\n"
        "3. 每次请求后检查响应是否符合上述响应约定；\n"
        "4. 必要时调用 db_query 核对数据库数据；\n"
        "5. 完成后用中文总结：执行了哪些步骤、每步的实际结果、结论（通过/发现的问题）。"
    )


def get_react_agent(with_memory: bool = True):
    """创建带工具的 ReAct 执行 Agent（LangGraph prebuilt + Ollama Function Calling）。

    with_memory=True 时挂载 SQLite Checkpointer：按 thread_id 持久化对话状态，
    Agent 每轮自动携带完整历史（短期记忆），且应用重启后会话可恢复（跨会话记忆）。
    调用时需传 config={"configurable": {"thread_id": "..."}}。
    """
    checkpointer = None
    if with_memory:
        from .memory import get_checkpointer
        checkpointer = get_checkpointer()
    return create_react_agent(
        model=get_llm(temperature=0),
        tools=[http_request, reset_http_session, db_query],
        prompt=_react_system(get_active_profile()),
        checkpointer=checkpointer,
    )
