# -*- coding: utf-8 -*-
"""大模型实例工厂与 JSON 容错解析工具。

按 data/models.json 中当前激活的模型配置构建实例：
- provider=ollama  → ChatOllama（本地推理，num_ctx/num_predict 控制内存占用）
- provider=openai  → ChatOpenAI（任何 OpenAI 兼容 API：DeepSeek/通义/Kimi/GLM 等）
"""
import json
import re

from config import NUM_CTX, NUM_PREDICT


def get_llm(json_mode: bool = False, temperature: float = 0.2):
    from models import get_active_model

    m = get_active_model()
    if m.get("provider") == "openai":
        from langchain_openai import ChatOpenAI

        kwargs = dict(model=m["model"], api_key=m.get("api_key") or "EMPTY",
                      base_url=m.get("base_url") or None,
                      temperature=temperature, max_tokens=NUM_PREDICT, timeout=120)
        if json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
        return ChatOpenAI(**kwargs)

    from langchain_ollama import ChatOllama

    kwargs = dict(model=m["model"], base_url=m.get("base_url") or "http://localhost:11434",
                  temperature=temperature, num_ctx=NUM_CTX, num_predict=NUM_PREDICT)
    if json_mode:
        kwargs["format"] = "json"  # Ollama 强制输出合法 JSON
    return ChatOllama(**kwargs)


def _close_truncated(candidate: str) -> str | None:
    """扫描 JSON 前缀，若括号未闭合则补全；前缀非法返回 None。"""
    stack = []
    in_str = False
    escape = False
    for ch in candidate:
        if escape:
            escape = False
            continue
        if ch == "\\":
            if in_str:
                escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                return None
            opener = stack.pop()
            if (opener, ch) not in (("{", "}"), ("[", "]")):
                return None
    if in_str:
        return None
    return candidate + "".join("}" if o == "{" else "]" for o in reversed(stack))


def parse_json(text: str) -> dict:
    """容错解析 LLM 输出中的 JSON：markdown 代码块、截断输出均可处理。"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    # 兜底：输出可能被截断 —— 从后往前找 '}'，截到该处并补全未闭合括号
    start = text.find("{")
    if start >= 0:
        body = text[start:]
        for pos in [m.start() for m in re.finditer(r"\}", body)][::-1][:80]:
            repaired = _close_truncated(body[: pos + 1])
            if repaired is None:
                continue
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                continue
    raise ValueError(f"无法从模型输出中解析 JSON: {text[:200]}")
