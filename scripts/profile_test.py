# -*- coding: utf-8 -*-
"""Profile 机制验证：多项目创建/切换/独立知识库/模板随配置变化。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from profiles import (get_active_profile, get_active_id, list_profiles,
                      profile_docs_dir, save_profile, set_active)

print("=== 1. 当前项目 ===")
print(get_active_id(), get_active_profile()["name"])
assert get_active_id() == "heima_p2p"

print("\n=== 2. 创建第二个项目（http_status 断言风格） ===")
demo = save_profile({
    "name": "演示商城系统",
    "base_url": "http://127.0.0.1:8080",
    "assert_style": "http_status",
    "biz_conventions": "RESTful 风格，业务结果用 HTTP 状态码表达（200成功/400参数错误/401未认证）",
    "login": {"path": "/api/auth/login", "method": "POST",
              "params": {"username": "admin", "password": "admin123"}},
    "seed_notes": "预置管理员 admin/admin123",
})
set_active(demo["id"])
print("已创建并切换:", get_active_profile()["name"])

# 独立知识库目录
docs = profile_docs_dir(demo["id"])
(docs / "demo_api.md").write_text(
    "# 演示商城接口\n\n## 登录\n- Path: /api/auth/login\n- Method: POST\n"
    "- 参数: username, password\n- 成功: HTTP 200\n- 密码错误: HTTP 401\n",
    encoding="utf-8")
from rag.vectorstore import build_vector_store, retrieve_context
vs = build_vector_store()
print("演示项目独立索引 chunks:", vs.index.ntotal)
ctx = retrieve_context("登录接口")
assert "/api/auth/login" in ctx and "理财" not in ctx, "知识库隔离失败！"
print("OK 知识库按项目隔离（检索不到黑马理财内容）")

# pytest 模板随 Profile 变化
from tools.pytest_gen import generate_pytest_file
path = generate_pytest_file([{
    "case_id": "TC_DEMO_001", "title": "登录成功", "case_type": "正常",
    "precondition": "", "api_path": "/api/auth/login", "method": "POST",
    "params": {"username": "admin", "password": "admin123"},
    "expected_biz_status": 200, "expected_keyword": ""}], "演示登录")
content = Path(path).read_text(encoding="utf-8")
assert 'BASE_URL = "http://127.0.0.1:8080"' in content
assert "ASSERT_HTTP_STATUS = True" in content
assert '/api/auth/login' in content
print("OK pytest 模板已按 Profile 固化:", Path(path).name)
Path(path).unlink()  # 演示文件不保留

# 生成 Agent 的 Prompt 输入随 Profile 变化（不调用 LLM，只验证装配）
from profiles import STATUS_HINTS
p = get_active_profile()
assert "HTTP 状态码" in STATUS_HINTS[p["assert_style"]]
print("OK 用例生成 Prompt 将注入:", p["biz_conventions"][:30], "...")

print("\n=== 3. 切回黑马理财 ===")
set_active("heima_p2p")
ctx = retrieve_context("注册接口")
assert "/member/public/reg" in ctx
print("OK 切回后检索命中黑马理财文档")

print("\nProfile 机制验证全部通过 ✔")
