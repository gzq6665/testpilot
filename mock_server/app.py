# -*- coding: utf-8 -*-
"""理财系统本地 Mock 服务。

按接口文档实现注册/登录/实名认证/开户/充值/投资等接口的业务规则，
使整套 Agent 测试链路可以离线闭环演示。

约定（与接口文档"测试环境约定"一致）：
- 图片验证码固定 8888，短信验证码固定 123456
- 预置用户 13800000001 / Test@123（已实名）
- 密码连续错 3 次锁定 60 秒
"""
import io
import time
import uuid

from flask import Flask, jsonify, make_response, request, session

app = Flask(__name__)
app.secret_key = "testpilot-mock-secret"
app.json.ensure_ascii = False  # 响应 JSON 直接输出中文

IMG_CODE = "8888"
SMS_CODE = "123456"

# 内存用户表：phone -> {password, realname, card_id, is_trust, fail_count, lock_until}
def _seed_users() -> dict:
    return {
        "13800000001": {
            "password": "Test@123",
            "realname": "对接焊",
            "card_id": "513436200001132880",
            "is_trust": "1",
            "fail_count": 0,
            "lock_until": 0,
        }
    }


USERS = _seed_users()

PRODUCTS = {1: {"name": "新手理财计划", "rate": "9.0%"}, 2: {"name": "稳健30天", "rate": "6.5%"}}


def biz(status, description, **extra):
    payload = {"status": status, "description": description}
    payload.update(extra)
    return jsonify(payload)


def mask(s, head, tail):
    if not s or len(s) <= head + tail:
        return s
    return s[:head] + "*" * (len(s) - head - tail) + s[-tail:]


@app.get("/")
def index():
    """服务首页：列出所有可用接口，方便确认 Mock 服务运行状态。"""
    return jsonify({
        "service": "理财系统 Mock（TestPilot 被测系统）",
        "status": "running",
        "tips": "业务接口均为 POST，请使用 Postman/JMeter 或 TestPilot 平台调用",
        "preset": {"user": "13800000001 / Test@123", "img_code": IMG_CODE, "sms_code": SMS_CODE},
        "endpoints": {
            "GET  /common/public/verifycode1/{r}": "获取图片验证码",
            "POST /member/public/sendSms": "获取短信验证码",
            "POST /member/public/reg": "注册",
            "POST /member/public/login": "登录",
            "POST /member/public/islogin": "是否登录",
            "POST /member/realname/approverealname": "实名认证（需登录）",
            "POST /member/member/getapprove": "获取认证信息（需登录）",
            "POST /trust/trust/register": "开户（需登录）",
            "POST /trust/trust/recharge": "充值（需登录）",
            "POST /trust/trust/tender": "投资（需登录）",
        },
    })


@app.post("/__reset__")
def test_reset():
    """测试辅助接口（仅 Mock 环境）：重置内存数据到初始状态，保证回归测试数据干净。"""
    global USERS
    USERS = _seed_users()
    session.clear()
    return biz(200, "测试数据已重置")


# ---------- 一、登录注册 ----------

@app.get("/common/public/verifycode1/<r>")
@app.get("/common/public/verifycode/<r>")
def verifycode(r):
    # 返回一张假的"图片"（演示用，验证码固定 8888）
    resp = make_response(io.BytesIO(b"\x89PNG-fake-captcha-8888").getvalue())
    resp.headers["Content-Type"] = "image/png"
    return resp


@app.post("/member/public/sendSms")
def send_sms():
    img_code = request.form.get("imgVerifyCode", "")
    phone = request.form.get("phone", "")
    if img_code != IMG_CODE:
        return biz(100, "图片验证码错误")
    if not phone:
        return biz(100, "手机号不能为空")
    return biz(200, "短信发送成功")


@app.post("/member/public/reg")
def reg():
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    verifycode_ = request.form.get("verifycode", "")
    phone_code = request.form.get("phone_code", "")
    dy_server = request.form.get("dy_server", "")

    if verifycode_ != IMG_CODE:
        return biz(100, "验证码错误!")
    if phone_code != SMS_CODE:
        return biz(100, "验证码错误")
    if phone in USERS:
        return biz(100, "手机已存在!")
    if not password:
        return biz(100, "密码不能为空")
    if dy_server != "on":
        return biz(100, "请同意我们的条款")
    if not phone:
        return biz(100, "手机号不能为空")
    if len(phone) != 11 or not phone.isdigit() or not phone.startswith("1"):
        return biz(100, "手机号格式错误")
    USERS[phone] = {
        "password": password, "realname": "", "card_id": "",
        "is_trust": "-1", "fail_count": 0, "lock_until": 0,
    }
    return biz(200, "注册成功")


@app.post("/member/public/login")
def login():
    keywords = request.form.get("keywords", "").strip()
    password = request.form.get("password", "")

    user = USERS.get(keywords)
    if user is None:
        return biz(100, "用户不存在")
    if not password:
        return biz(100, "密码不能为空")
    now = time.time()
    if user["lock_until"] > now:
        return biz(100, "由于连续输入错误密码达到上限，账号已被锁定，请于1.0分钟后重新登录")
    if password != user["password"]:
        user["fail_count"] += 1
        if user["fail_count"] >= 3:
            user["lock_until"] = now + 60
            user["fail_count"] = 0
            return biz(100, "由于连续输入错误密码达到上限，账号已被锁定，请于1.0分钟后重新登录")
        return biz(100, f"密码错误{user['fail_count']}次,达到3次将锁定账户")
    user["fail_count"] = 0
    session["phone"] = keywords
    return biz(200, "登录成功")


@app.post("/member/public/islogin")
def islogin():
    if session.get("phone"):
        return biz(200, "OK")
    return biz(250, "您未登陆！")


def _require_login():
    phone = session.get("phone")
    if not phone:
        return None, biz(250, "您未登陆！")
    return USERS[phone], None


# ---------- 二、开通账户 ----------

@app.post("/member/realname/approverealname")
def approve_realname():
    user, err = _require_login()
    if err:
        return err
    realname = request.form.get("realname", "").strip()
    card_id = request.form.get("card_id", "").strip()
    if not realname:
        return biz(100, "姓名不能为空")
    if not card_id:
        return biz(100, "身份证号不能为空")
    if len(card_id) != 18:
        return biz(100, "身份证号格式错误")
    user["realname"], user["card_id"] = realname, card_id
    return biz(200, "提交成功!", data={"card_id": mask(card_id, 3, 1), "realname": realname[0] + "**"})


@app.post("/member/member/getapprove")
def getapprove():
    user, err = _require_login()
    if err:
        return err
    return jsonify({
        "is_realname_open": "2" if user["realname"] else "-1",
        "card_id": mask(user["card_id"], 3, 3),
        "realname": (user["realname"][0] + "**") if user["realname"] else "",
        "phone": mask(session["phone"], 3, 4),
        "realname_status": "1" if user["realname"] else "0",
        "trustType": "chinapnr",
        "is_trust": user["is_trust"],
        "pay_pwd": "", "email": "", "isCert": "2",
    })


THIRD_PARTY_FORM = (
    "<form name='easypaysubmit' id='easypaysubmit' method='post' "
    "action='http://mertest.chinapnr.com/muser/publicRequests'>"
    "<input name='Version' type='hidden' value='10'/>"
    "<input name='CmdId' type='hidden' value='{cmd}'/>"
    "<input name='MerCustId' type='hidden' value='6000060007313892'/>"
    "<input name='OrdId' type='hidden' value='{ord_id}'/>"
    "<input name='ChkValue' type='hidden' value='MOCKCHKVALUE'/>"
    "</form>"
)


@app.post("/trust/trust/register")
def trust_register():
    user, err = _require_login()
    if err:
        return err
    if not user["realname"]:
        return biz(100, "请先完成实名认证")
    user["is_trust"] = "1"
    return jsonify({"status": 200, "description": {
        "form": THIRD_PARTY_FORM.format(cmd="UserRegister", ord_id=uuid.uuid4().hex[:20])}})


# ---------- 三、充值 ----------

@app.post("/trust/trust/recharge")
def recharge():
    user, err = _require_login()
    if err:
        return err
    valicode = request.form.get("valicode", "")
    amount = request.form.get("amount", "").strip()
    if valicode != IMG_CODE:
        return biz(100, "验证码错误")
    try:
        amt = float(amount)
    except ValueError:
        amt = -1
    if not amount or amt <= 0:
        return biz(100, "充值金额不能为空")
    return jsonify({"status": 200, "description": {
        "form": THIRD_PARTY_FORM.format(cmd="UserRecharge", ord_id=uuid.uuid4().hex[:20])}})


# ---------- 四、投资 ----------

@app.post("/trust/trust/tender")
def tender():
    user, err = _require_login()
    if err:
        return err
    pid = request.form.get("id", "").strip()
    amount = request.form.get("amount", "").strip()
    try:
        amt = float(amount)
    except ValueError:
        amt = -1
    if not amount or amt <= 0:
        return biz(100, "投资金额不能为空")
    if not pid or not pid.isdigit() or int(pid) not in PRODUCTS:
        return biz(100, "产品不存在")
    return jsonify({"status": 200, "description": {
        "form": THIRD_PARTY_FORM.format(cmd="InitiativeTender", ord_id=uuid.uuid4().hex[:20])}})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9999)
