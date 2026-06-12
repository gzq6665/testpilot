# -*- coding: utf-8 -*-
"""由 TestPilot 自动生成的接口回归脚本（pytest + requests）。

生成时间: 2026-06-12 10:17:02
被测项目: Restful-Booker 
被测系统: https://restful-booker.herokuapp.com
断言风格: biz_status
运行方式: pytest test_创建预订_20260612_101702.py -v
"""
import pytest
import requests

BASE_URL = "https://restful-booker.herokuapp.com"
ASSERT_HTTP_STATUS = False  # True=断言HTTP状态码; False=断言响应JSON的status字段
LOGIN = {"path": "/auth", "method": "POST", "params": {"username": "admin", "password": "password123"}}

CASES = [
    {
        "case_id": "TC_CREATE_BOOK_001",
        "title": "正常创建预订-提供所有字段",
        "module": "创建预订",
        "case_type": "正常",
        "priority": "P0",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 111,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 200,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_002",
        "title": "缺少必填字段-firstname",
        "module": "创建预订",
        "case_type": "异常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "lastname": "Brown",
            "totalprice": 111,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 400,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_003",
        "title": "缺少必填字段-lastname",
        "module": "创建预订",
        "case_type": "异常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "totalprice": 111,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 400,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_004",
        "title": "totalprice为负数",
        "module": "创建预订",
        "case_type": "异常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": -100,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 400,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_005",
        "title": "bookingdates中checkout早于checkin",
        "module": "创建预订",
        "case_type": "异常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 111,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2019-01-01",
                "checkout": "2018-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 400,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_006",
        "title": "bookingdates日期格式错误",
        "module": "创建预订",
        "case_type": "异常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 111,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-13-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 400,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_007",
        "title": "depositpaid为非布尔值",
        "module": "创建预订",
        "case_type": "异常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 111,
            "depositpaid": "yes",
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 400,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_008",
        "title": "totalprice为字符串类型",
        "module": "创建预订",
        "case_type": "异常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": "high",
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 400,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_009",
        "title": "边界值-firstname为空字符串",
        "module": "创建预订",
        "case_type": "边界",
        "priority": "P2",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "",
            "lastname": "Brown",
            "totalprice": 111,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 200,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_010",
        "title": "边界值-totalprice为0",
        "module": "创建预订",
        "case_type": "边界",
        "priority": "P2",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 0,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 200,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_011",
        "title": "边界值-totalprice为极大值",
        "module": "创建预订",
        "case_type": "边界",
        "priority": "P2",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 999999999,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            },
            "additionalneeds": "Breakfast"
        },
        "expected_biz_status": 200,
        "expected_keyword": ""
    },
    {
        "case_id": "TC_CREATE_BOOK_012",
        "title": "缺少非必填字段-additionalneeds",
        "module": "创建预订",
        "case_type": "正常",
        "priority": "P1",
        "precondition": "",
        "api_path": "/booking",
        "method": "POST",
        "params": {
            "firstname": "Jim",
            "lastname": "Brown",
            "totalprice": 111,
            "depositpaid": true,
            "bookingdates": {
                "checkin": "2018-01-01",
                "checkout": "2019-01-01"
            }
        },
        "expected_biz_status": 200,
        "expected_keyword": ""
    }
]


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


def _login(s):
    if LOGIN.get("path"):
        s.request(LOGIN.get("method", "POST"), BASE_URL + LOGIN["path"],
                  data=LOGIN.get("params") or {}, timeout=10)


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_api(session, case):
    if "登录" in (case.get("precondition") or ""):
        _login(session)
    resp = session.request(
        method=case["method"],
        url=BASE_URL + case["api_path"],
        data=case.get("params") or {},
        timeout=10,
    )
    expected = case.get("expected_biz_status")
    if ASSERT_HTTP_STATUS:
        if expected is not None:
            assert resp.status_code == expected, \
                f"HTTP状态码不符: 期望 {expected}, 实际 {resp.status_code}, 响应 {resp.text[:200]}"
        body_text = resp.text
    else:
        assert resp.status_code == 200, f"HTTP状态码异常: {resp.status_code}"
        body = resp.json()
        if expected is not None:
            assert body.get("status") == expected, \
                f"业务状态码不符: 期望 {expected}, 实际 {body.get('status')}, 响应 {body}"
        body_text = str(body)
    if case.get("expected_keyword"):
        assert case["expected_keyword"] in body_text, \
            f"响应中未包含关键字 [{case['expected_keyword']}]: {body_text[:200]}"
