# -*- coding: utf-8 -*-
"""将结构化测试用例渲染为可直接运行的 pytest + requests 回归脚本。

被测系统地址、登录配置、断言风格在生成时从当前 Profile 固化进脚本，
脚本可脱离平台独立运行。
"""
import json
import re
import time

from config import GENERATED_TESTS_DIR
from profiles import get_active_profile

_TEMPLATE_HEADER = '''# -*- coding: utf-8 -*-
"""由 TestPilot 自动生成的接口回归脚本（pytest + requests）。

生成时间: {ts}
被测项目: {project_name}
被测系统: {base_url}
断言风格: {assert_style}
运行方式: pytest {filename} -v
"""
import pytest
import requests

BASE_URL = "{base_url}"
ASSERT_HTTP_STATUS = {assert_http}  # True=断言HTTP状态码; False=断言响应JSON的status字段
BODY_AS_JSON = {body_json}          # True=JSON请求体; False=表单编码
LOGIN = {login_json}

CASES = {cases_json}


@pytest.fixture(scope="session", autouse=True)
def reset_test_data():
    """回归开始前重置 Mock 测试数据，保证注册类用例可重复执行（真实环境无此接口，忽略失败）。"""
    try:
        requests.post(BASE_URL + "/__reset__", timeout=5)
    except requests.RequestException:
        pass


@pytest.fixture()
def session():
    s = requests.Session()
    yield s
    s.close()


def _body_kwargs(params):
    return {{"json": params}} if BODY_AS_JSON else {{"data": params}}


def _login(s):
    if LOGIN.get("path"):
        s.request(LOGIN.get("method", "POST"), BASE_URL + LOGIN["path"],
                  timeout=10, **_body_kwargs(LOGIN.get("params") or {{}}))


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_api(session, case):
    if "登录" in (case.get("precondition") or ""):
        _login(session)
    resp = session.request(
        method=case["method"],
        url=BASE_URL + case["api_path"],
        timeout=15,
        **_body_kwargs(case.get("params") or {{}}),
    )
    expected = case.get("expected_biz_status")
    if ASSERT_HTTP_STATUS:
        if expected is not None:
            assert resp.status_code == expected, \\
                f"HTTP状态码不符: 期望 {{expected}}, 实际 {{resp.status_code}}, 响应 {{resp.text[:200]}}"
        body_text = resp.text
    else:
        assert resp.status_code == 200, f"HTTP状态码异常: {{resp.status_code}}"
        body = resp.json()
        if expected is not None:
            assert body.get("status") == expected, \\
                f"业务状态码不符: 期望 {{expected}}, 实际 {{body.get('status')}}, 响应 {{body}}"
        body_text = str(body)
    if case.get("expected_keyword"):
        assert case["expected_keyword"] in body_text, \\
            f"响应中未包含关键字 [{{case['expected_keyword']}}]: {{body_text[:200]}}"
'''


def generate_pytest_file(cases: list[dict], module_name: str = "module") -> str:
    """渲染 pytest 文件并写入 tests_generated/，返回文件路径。"""
    profile = get_active_profile()
    safe = re.sub(r"[^\w一-龥]+", "_", module_name)[:30] or "module"
    filename = f"test_{safe}_{time.strftime('%Y%m%d_%H%M%S')}.py"
    content = _TEMPLATE_HEADER.format(
        ts=time.strftime("%Y-%m-%d %H:%M:%S"),
        project_name=profile["name"],
        base_url=profile["base_url"],
        assert_style=profile.get("assert_style", "biz_status"),
        assert_http=profile.get("assert_style") == "http_status",
        body_json=profile.get("body_format") == "json",
        login_json=json.dumps(profile.get("login") or {}, ensure_ascii=False),
        cases_json=json.dumps(cases, ensure_ascii=False, indent=4),
        filename=filename,
    )
    path = GENERATED_TESTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return str(path)
