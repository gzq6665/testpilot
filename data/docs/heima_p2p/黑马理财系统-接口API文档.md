# 黑马理财系统 接口API文档

## 系统信息

- 系统路径（测试环境1）：http://user-p2p-test.itheima.net
- 系统路径（测试环境2）：http://121.43.169.97:8081
- 本地 Mock 环境：http://127.0.0.1:9999
- 业务说明：P2P 理财/借贷业务平台，覆盖注册、登录、实名认证、开户、充值、投资等核心流程。
- 通用约定：除特殊说明外，接口 HTTP 响应状态码均为 200，业务结果通过返回 JSON 中的 `status` 字段表示（200=成功，100=业务校验失败，250=未登录）。

## 测试环境约定（重要）

- 本地 Mock 环境中，图片验证码固定为 `8888`，短信验证码固定为 `123456`。
- 测试环境预置已注册用户：手机号 `13800000001`，密码 `Test@123`（已完成实名认证）。
- 需要登录态的接口必须先调用登录接口获取会话 Cookie（JSESSIONID）。
- 密码连续输错 3 次会锁定账户 1 分钟。

---

## 一、登录注册模块

### 1.1 获取图片验证码

- Path: `/common/public/verifycode1/{r}`
- Method: GET
- URL参数: `r` 随机数，示例 `0.1426580900762553`
- 返回数据: 响应状态码 200，返回图片（验证码图片）。

### 1.2 获取短信验证码

- Path: `/member/public/sendSms`
- Method: POST
- Headers: `Content-Type: application/x-www-form-urlencoded`，需携带 Cookie JSESSIONID

请求参数（body）：

| 参数名称 | 类型 | 是否必填 | 示例 | 备注 |
|---|---|---|---|---|
| phone | string | 是 | 13800000002 | 手机号 |
| imgVerifyCode | string | 是 | 8888 | 图片验证码 |
| type | string | 是 | reg | 类型[reg:注册] |

返回数据（HTTP 200）：

- 发送成功：`{"status":200,"description":"短信发送成功"}`
- 发送失败（图片验证码错误）：`{"status":100,"description":"图片验证码错误"}`

### 1.3 注册

- Path: `/member/public/reg`
- Method: POST
- Headers: `Content-Type: application/x-www-form-urlencoded`

请求参数（body）：

| 参数名称 | 类型 | 是否必填 | 默认值 | 备注 |
|---|---|---|---|---|
| phone | string | 是 |  | 手机号 |
| password | string | 是 |  | 密码 |
| verifycode | string | 是 |  | 图片验证码 |
| phone_code | string | 是 |  | 手机验证码（短信验证码） |
| dy_server | string | 是 | on | 是否同意协议[on/off] |
| invite_phone | string | 否 |  | 邀请人手机号 |

返回数据（HTTP 200），业务状态码说明：

- 200 注册成功：`{"status":200,"description":"注册成功"}`
- 100 图片验证码错误：`{"status":100,"description":"验证码错误!"}`
- 100 短信验证码错误：`{"status":100,"description":"验证码错误"}`
- 100 手机已存在：`{"status":100,"description":"手机已存在!"}`
- 100 密码不能为空：`{"status":100,"description":"密码不能为空"}`
- 100 未同意协议：`{"status":100,"description":"请同意我们的条款"}`
- 100 手机号格式错误（非 11 位数字或不以 1 开头）：`{"status":100,"description":"手机号格式错误"}`

### 1.4 登录

- Path: `/member/public/login`
- Method: POST
- Headers: `Content-Type: application/x-www-form-urlencoded`

请求参数（body）：

| 参数名称 | 类型 | 是否必填 | 示例 | 备注 |
|---|---|---|---|---|
| keywords | string | 是 | 13800000001 | 手机号 |
| password | string | 是 | Test@123 | 密码 |

返回数据（HTTP 200），业务状态码说明：

- 200 登录成功：`{"status":200,"description":"登录成功"}`
- 100 用户不存在：`{"status":100,"description":"用户不存在"}`
- 100 密码不能为空：`{"status":100,"description":"密码不能为空"}`
- 100 密码错误1次：`{"status":100,"description":"密码错误1次,达到3次将锁定账户"}`
- 100 密码错误2次：`{"status":100,"description":"密码错误2次,达到3次将锁定账户"}`
- 100 密码错误3次锁定：`{"status":100,"description":"由于连续输入错误密码达到上限，账号已被锁定，请于1.0分钟后重新登录"}`

### 1.5 是否登录

- Path: `/member/public/islogin`
- Method: POST
- 接口描述: 判断当前会话是否处于登录状态

返回数据（HTTP 200）：

- 200 已登录：`{"status":200,"description":"OK"}`
- 250 未登录：`{"status":250,"description":"您未登陆！"}`

---

## 二、开通账户模块

### 2.1 实名认证

- Path: `/member/realname/approverealname`
- Method: POST
- Headers: `Content-Type: multipart/form-data`，需携带登录态 Cookie JSESSIONID

请求参数（body）：

| 参数名称 | 类型 | 是否必填 | 备注 |
|---|---|---|---|
| realname | string | 是 | 真实姓名 |
| card_id | string | 是 | 身份证号 |

返回数据（HTTP 200）：

- 200 提交成功：`{"status":200,"data":{"card_id":"110****21X","realname":"李**"},"description":"提交成功!"}`
- 100 姓名不能为空：`{"status":100,"description":"姓名不能为空"}`
- 100 身份证号不能为空：`{"status":100,"description":"身份证号不能为空"}`

### 2.2 获取认证信息

- Path: `/member/member/getapprove`
- Method: POST
- 请求参数: 无（需登录态）
- 返回数据（HTTP 200）: 返回用户认证信息 JSON，关键字段包括 `is_realname_open`、`card_id`（脱敏）、`realname`（脱敏）、`phone`（脱敏）、`realname_status`、`trustType`、`is_trust` 等。

### 2.3 开户

- Path: `/trust/trust/register`
- Method: POST
- Headers: `Content-Type: application/x-www-form-urlencoded`（需登录态）
- 请求参数: 无
- 返回数据（HTTP 200）: `{"status":200,"description":{"form":"<form ... action='http://mertest.chinapnr.com/muser/publicRequests'>...</form>"}}`
  - description.form 为第三方存管（汇付天下 chinapnr）自动提交表单 HTML。

### 2.4 第三方开户接口

- Path: `http://mertest.chinapnr.com/muser/publicRequests`（外部第三方）
- Method: POST
- 请求参数: 取开户接口返回 form 表单中所有 input 标签的 name/value（如 Version=10、CmdId=UserRegister、MerCustId、ChkValue 等）。
- 请求 URL 为 form 表单的 action 值。

---

## 三、充值模块

### 3.1 获取充值验证码

- Path: `/common/public/verifycode/{r}`
- Method: GET
- URL参数: `r` 随机数
- 返回数据: 响应状态码 200，返回图片。

### 3.2 充值

- Path: `/trust/trust/recharge`
- Method: POST
- Headers: `Content-Type: application/x-www-form-urlencoded`，需登录态 Cookie

请求参数（body）：

| 参数名称 | 类型 | 是否必填 | 默认值 | 备注 |
|---|---|---|---|---|
| paymentType | string | 是 | chinapnrTrust | 充值类型 |
| amount | string | 是 |  | 充值金额 |
| formStr | string | 是 | reForm |  |
| valicode | string | 是 |  | 充值验证码 |

返回数据（HTTP 200）：

- 200 成功：返回第三方充值自动提交表单（description.form，action 指向 chinapnr）。
- 100 验证码错误：`{"status":100,"description":"验证码错误"}`
- 100 金额非法（为空/非正数）：`{"status":100,"description":"充值金额不能为空"}`

---

## 四、投资模块

### 4.1 投资

- Path: `/trust/trust/tender`
- Method: POST
- Headers: `Content-Type: application/x-www-form-urlencoded`，需登录态 Cookie

请求参数（body）：

| 参数名称 | 类型 | 是否必填 | 备注 |
|---|---|---|---|
| id | int | 是 | 产品id |
| depositCertificate | int | 是 | 默认 -1 |
| amount | int | 是 | 投资金额 |

返回数据（HTTP 200）：

- 200 成功：返回第三方投资自动提交表单（description.form，CmdId=InitiativeTender，含 OrdId、TransAmt、BorrowerDetails 等字段）。
- 100 投资金额不能为空
- 100 投资密码不能为空
- 100 产品不存在

### 4.2 三方投资

- 请求 URL: 投资接口返回 form 表单的 action 值（chinapnr）。
- 请求参数: form 表单中所有 input 标签的 name/value。
