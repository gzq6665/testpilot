# -*- coding: utf-8 -*-
"""HTTP 请求工具：供执行 Agent（Function Calling）和确定性执行器共用。

模块级维护一个 requests.Session，自动保持 Cookie（JSESSIONID）会话，
支持登录后续接口的鉴权连贯性。
"""
import json

import requests
from langchain_core.tools import tool

_session = requests.Session()


def _default_base_url() -> str:
    from profiles import get_active_profile
    return get_active_profile()["base_url"]


def reset_session() -> None:
    """清空会话 Cookie，回到未登录状态。"""
    global _session
    _session = requests.Session()


def do_request(method: str, path: str, data: dict | None = None,
               params: dict | None = None, base_url: str | None = None,
               body_format: str | None = None) -> dict:
    """发送 HTTP 请求并返回结构化结果。path 传完整 URL 时直接使用。

    body_format: "form"=表单编码, "json"=JSON 请求体；不传时取当前 Profile 配置。
    """
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    else:
        url = (base_url or _default_base_url()).rstrip("/") + "/" + path.lstrip("/")
    if body_format is None:
        from profiles import get_active_profile
        body_format = get_active_profile().get("body_format", "form")
    body_kwargs = {"json": data} if body_format == "json" else {"data": data}
    try:
        resp = _session.request(method=method.upper(), url=url,
                                params=params, timeout=15, **body_kwargs)
        try:
            body = resp.json()
        except ValueError:
            body = resp.text[:500]
        return {"ok": True, "http_status": resp.status_code, "body": body, "url": url}
    except requests.RequestException as e:
        return {"ok": False, "http_status": None, "error": f"{type(e).__name__}: {e}", "url": url}


def login_seed_user() -> dict:
    """按当前 Profile 的登录配置执行登录，建立会话。"""
    from profiles import get_active_profile

    login = (get_active_profile().get("login") or {})
    if not login.get("path"):
        return {"ok": False, "error": "当前项目未配置登录接口"}
    return do_request(login.get("method", "POST"), login["path"],
                      data=login.get("params") or {})


# ---------- LangChain Tools（供执行 Agent Function Calling 使用） ----------

def _coerce_form(form_data) -> dict:
    """容错处理模型传参：支持 dict、JSON 字符串、被转义的 JSON 字符串。"""
    if form_data is None:
        return {}
    if isinstance(form_data, dict):
        return form_data
    s = str(form_data).strip()
    for candidate in (s, s.replace('\\"', '"')):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return {}


@tool
def http_request(method: str, path: str, form_data: dict | str | None = None) -> str:
    """向被测系统发送 HTTP 请求并返回响应。

    Args:
        method: HTTP 方法，GET 或 POST（本系统业务接口均为 POST）。
        path: 接口路径，例如 /member/public/login。
        form_data: 表单参数对象，例如 {"keywords": "13800000001", "password": "Test@123"}。
    """
    result = do_request(method, path, data=_coerce_form(form_data))
    return json.dumps(result, ensure_ascii=False)


@tool
def reset_http_session() -> str:
    """清除当前 HTTP 会话的 Cookie，使后续请求处于未登录状态。用于测试未登录场景。"""
    reset_session()
    return "会话已重置（未登录状态）"
