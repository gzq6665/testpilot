# -*- coding: utf-8 -*-
"""冒烟测试：逐项验证 RAG / Mock服务 / 执行器 / 用例生成是否正常。

运行: python scripts/smoke_test.py [--full]
    默认跑：知识库构建、RAG检索、Mock接口执行（不依赖大模型推理）
    --full 额外跑：RAG问答、用例生成（需要本地模型推理，较慢）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

FULL = "--full" in sys.argv


def step(name):
    print(f"\n{'=' * 20} {name} {'=' * 20}")


step("1. 构建向量知识库")
from rag.vectorstore import build_vector_store, retrieve_context

vs = build_vector_store()
print(f"OK 向量库构建完成，chunk 数: {vs.index.ntotal}")

step("2. RAG 检索")
ctx = retrieve_context("注册接口有哪些必填参数")
assert "/member/public/reg" in ctx, "检索结果未命中注册接口"
print("OK 检索命中注册接口文档片段")
print(ctx[:300])

step("3. Mock 服务接口执行（确定性执行器）")
from agents.executor import execute_cases

demo_cases = [
    {"case_id": "TC_LOGIN_001", "title": "正确账号密码登录成功", "case_type": "正常",
     "precondition": "", "api_path": "/member/public/login", "method": "POST",
     "params": {"keywords": "13800000001", "password": "Test@123"},
     "expected_biz_status": 200, "expected_keyword": "登录成功"},
    {"case_id": "TC_LOGIN_002", "title": "用户不存在", "case_type": "异常",
     "precondition": "", "api_path": "/member/public/login", "method": "POST",
     "params": {"keywords": "13999999999", "password": "xxx"},
     "expected_biz_status": 100, "expected_keyword": "用户不存在"},
    {"case_id": "TC_ISLOGIN_001", "title": "未登录访问islogin返回250", "case_type": "异常",
     "precondition": "", "api_path": "/member/public/islogin", "method": "POST",
     "params": {}, "expected_biz_status": 250, "expected_keyword": "未登陆"},
    {"case_id": "TC_REAL_001", "title": "登录后实名认证提交成功", "case_type": "正常",
     "precondition": "需要登录", "api_path": "/member/realname/approverealname", "method": "POST",
     "params": {"realname": "张三", "card_id": "110101200001011234"},
     "expected_biz_status": 200, "expected_keyword": "提交成功"},
]
results = execute_cases(demo_cases)
for r in results:
    print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {r['case_id']} {r['title']} - {r['reason']}")
failed = [r for r in results if not r["passed"]]
assert not failed, f"{len(failed)} 条用例执行失败（请确认 Mock 服务已启动: python mock_server/app.py）"
print("OK 4/4 用例全部通过")

step("4. pytest 脚本生成")
from tools.pytest_gen import generate_pytest_file

path = generate_pytest_file(demo_cases, "登录冒烟")
print(f"OK 已生成: {path}")

if FULL:
    step("5. RAG 问答（LLM 推理）")
    from rag.qa_chain import answer

    out = answer("登录接口密码连续输错3次会怎样？")
    print(out["answer"])

    step("6. 用例生成 Agent（LLM 推理）")
    from agents.case_generator import generate_cases

    gen = generate_cases("登录接口", num_cases=5)
    print(f"OK 生成 {len(gen['cases'])} 条用例:")
    for c in gen["cases"]:
        print(f"  - [{c['case_type']}] {c['case_id']} {c['title']}")

print("\n冒烟测试全部通过 ✔")
