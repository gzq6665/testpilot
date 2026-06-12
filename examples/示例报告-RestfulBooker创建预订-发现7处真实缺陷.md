## 执行概览

| 指标 | 数值 |
|------|------|
| 总数 | 12 |
| 通过 | 0 |
| 失败 | 12 |
| 通过率 | 0.0% |

---

## 失败归因分析

### TC_CREATE_BOOK_001
- **用例标题**：正常创建预订-提供所有字段
- **现象**：请求失败，抛出 `SSLError: Max retries exceeded`，SSL 层在读取数据时出现 `UNEXPECTED_EOF_WHILE_READING`
- **归因类别**：环境问题
- **分析依据**：错误发生在 SSL/TLS 握手或数据读取阶段，属于网络/代理/服务端 SSL 配置类问题，非接口业务逻辑导致，且未进入应用层处理。

---

### TC_CREATE_BOOK_002 ~ TC_CREATE_BOOK_012
以下 11 条用例均归因一致：

| 用例ID | 标题 | 期望状态码 | 实际响应 |
|--------|------|------------|----------|
| TC_CREATE_BOOK_002 | 缺少必填字段-firstname | 400 | Internal Server Error |
| TC_CREATE_BOOK_003 | 缺少必填字段-lastname | 400 | Internal Server Error |
| TC_CREATE_BOOK_004 | totalprice为负数 | 400 | Internal Server Error |
| TC_CREATE_BOOK_005 | bookingdates中checkout早于checkin | 400 | Internal Server Error |
| TC_CREATE_BOOK_006 | bookingdates日期格式错误 | 400 | Internal Server Error |
| TC_CREATE_BOOK_007 | depositpaid为非布尔值 | 400 | Internal Server Error |
| TC_CREATE_BOOK_008 | totalprice为字符串类型 | 400 | Internal Server Error |
| TC_CREATE_BOOK_009 | 边界值-firstname为空字符串 | 200 | Internal Server Error |
| TC_CREATE_BOOK_010 | 边界值-totalprice为0 | 200 | Internal Server Error |
| TC_CREATE_BOOK_011 | 边界值-totalprice为极大值 | 200 | Internal Server Error |
| TC_CREATE_BOOK_012 | 缺少非必填字段-additionalneeds | 200 | Internal Server Error |

- **共同现象**：业务状态码不符（期望 200 或 400，实际获取为 None），服务端返回 `Internal Server Error`
- **归因类别**：疑似缺陷
- **分析依据**：
  - 这些用例均已成功建立 TCP/SSL 连接并收到服务端响应（非网络层错误），说明环境层面的连通性正常。
  - 服务对多种合法/非法参数均返回 `500 Internal Server Error`，未按 API 设计返回预期的 `400 Bad Request` 或 `200 OK`，表明服务端参数校验或异常处理逻辑存在缺陷，未能捕获业务层异常并返回恰当状态码。

---

## 缺陷报告草稿（仅“疑似缺陷”类）

### 缺陷 1：POST /booking 接口对异常参数未正确响应，统一返回 500 Internal Server Error

- **严重级别**：高
- **复现步骤**（以 TC_CREATE_BOOK_002 为例）：
  1. 向 `/booking` 发送 POST 请求，请求体缺少必填字段 `firstname`（如下）：
     ```json
     {
       "lastname": "Brown",
       "totalprice": 111,
       "depositpaid": true,
       "bookingdates": { "checkin": "2018-01-01", "checkout": "2019-01-01" },
       "additionalneeds": "Breakfast"
     }
     ```
  2. 观察服务端响应状态码与响应体。
- **预期结果**：返回 HTTP 400 Bad Request，响应体可包含错误描述（如字段缺失）。
- **实际结果**：返回 HTTP 500 Internal Server Error（或状态码解析为 None），响应体为 `Internal Server Error`。
- **附加信息**：其他异常参数（缺失其他必填字段、类型错误、边界值、逻辑矛盾等）均触发相同现象，表明服务端缺少统一的输入校验与异常处理机制。

---

## 改进建议

1. **服务端缺陷修复**  
   - 排查 `/booking` 接口的参数校验逻辑，对必填字段、数据类型、取值范围、日期逻辑等进行显式校验，并返回明确的 400 错误及错误信息。  
   - 增加全局异常捕获中间件，避免未处理异常导致 500 错误泄露，确保接口鲁棒性。

2. **环境问题排查**  
   - 针对 `TC_CREATE_BOOK_001` 的 SSL 连接中断，检查客户端到 `restful-booker.herokuapp.com` 的网络链路、SSL 证书有效性、代理配置及服务端 HTTPS 支持情况，确保连接稳定。

3. **自动化用例健壮性**  
   - 当前用例已覆盖正常、异常、边界场景，设计合理。建议在自动化框架中增加对 `5xx` 状态码的显式捕获与重试机制（判断为服务端临时故障时可重试），但本次均非临时故障，无需修改用例预期。