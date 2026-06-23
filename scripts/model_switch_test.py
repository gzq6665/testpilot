# -*- coding: utf-8 -*-
"""模型切换功能验证：注册API模型→工厂返回ChatOpenAI→切回Ollama→真实推理。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from agents.llm import get_llm
from models import (delete_model, get_active_model, list_models,
                    save_model, set_active_model)

print("=== 1. 默认模型 ===")
m = get_active_model()
print(f"{m['name']} provider={m['provider']}")
assert m["provider"] == "ollama"
llm = get_llm()
print("实例类型:", type(llm).__name__)
assert type(llm).__name__ == "ChatOllama"

print("\n=== 2. 注册并切换到 OpenAI 兼容 API 模型 ===")
api_m = save_model({"name": "DeepSeek测试", "provider": "openai",
                    "model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1",
                    "api_key": "sk-fake-for-test"})
set_active_model(api_m["id"])
llm2 = get_llm(json_mode=True)
print("实例类型:", type(llm2).__name__, "| 模型:", llm2.model_name)
assert type(llm2).__name__ == "ChatOpenAI"
assert llm2.model_name == "deepseek-chat"

print("\n=== 3. 切回本地 Ollama 并真实推理 ===")
ollama_id = next(m["id"] for m in list_models() if m["provider"] == "ollama")
set_active_model(ollama_id)
delete_model(api_m["id"])  # 清理测试模型
resp = get_llm().invoke("用一句话回复：你好")
print("模型回复:", resp.content)
assert resp.content

print("\n模型切换功能验证全部通过 ✔")
