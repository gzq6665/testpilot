# Restful-Booker 接口 API 文档

> 一个免费、可公开访问的酒店预订 REST API，专为 API 测试 / 接口测试练习而设计。
> 包含完整的「认证 + 增删改查（CRUD）」业务流程，并**故意埋了一些 bug** 供测试者发现。

---

## 系统信息

| 项目 | 内容 |
|---|---|
| 系统名称 | Restful-Booker（酒店预订系统） |
| 系统路径（Base URL） | `https://restful-booker.herokuapp.com` |
| 官方文档 | `https://restful-booker.herokuapp.com/apidoc/index.html` |
| 源码地址 | `https://github.com/mwinteringham/restful-booker` |
| 是否需要 API Key | **否**，免费、无需注册即可直接调用 |
| 数据说明 | 预置 10 条预订记录；**每 10 分钟自动重置**回默认状态 |
| 作者 | Mark Winteringham |

> 说明：`PUT`、`PATCH`、`DELETE` 这类写操作需要先通过认证接口获取 **Token**，再通过 Cookie 或 Authorization 头携带。`POST /booking`（创建）和所有 `GET` 查询接口**无需 Token**。

---

## 接口总览

| 序号 | 接口名称 | Method | Path | 是否需 Token |
|---|---|---|---|---|
| 1 | 健康检查 | GET | `/ping` | 否 |
| 2 | 创建 Token（认证） | POST | `/auth` | 否 |
| 3 | 获取所有预订 ID | GET | `/booking` | 否 |
| 4 | 获取单条预订详情 | GET | `/booking/{id}` | 否 |
| 5 | 创建预订 | POST | `/booking` | 否 |
| 6 | 更新预订（全量） | PUT | `/booking/{id}` | **是** |
| 7 | 更新预订（部分） | PATCH | `/booking/{id}` | **是** |
| 8 | 删除预订 | DELETE | `/booking/{id}` | **是** |

---

## 一、健康检查（HealthCheck）

### 基本信息
- **Path**：`/ping`
- **Method**：`GET`
- **接口描述**：检查服务是否在线（常用于冷启动唤醒，Heroku 免费实例首次访问可能有几秒延迟）。

### 请求参数
无

### 返回数据
- 响应状态码：`201 Created`
- 响应内容：`Created`

### 请求示例
```bash
curl -i https://restful-booker.herokuapp.com/ping
```

---

## 二、创建 Token / 认证（CreateToken）

### 基本信息
- **Path**：`/auth`
- **Method**：`POST`
- **接口描述**：用合法的用户名密码换取 Token，更新和删除接口需要它。

### 请求参数

**headers**

| 参数名称 | 参数值 | 是否必填 | 备注 |
|---|---|---|---|
| Content-Type | application/json | 是 | |

**body**

| 参数名称 | 类型 | 是否必填 | 示例 | 备注 |
|---|---|---|---|---|
| username | string | 是 | admin | 固定测试账号 |
| password | string | 是 | password123 | 固定测试密码 |

### 返回数据
- 响应状态码：`200`
- 认证成功：`{"token":"abc123def456ghi"}`
- 认证失败（账号或密码错误）：`{"reason":"Bad credentials"}`

### 请求示例
```bash
curl -X POST https://restful-booker.herokuapp.com/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'
```

---

## 三、获取所有预订 ID（GetBookingIds）

### 基本信息
- **Path**：`/booking`
- **Method**：`GET`
- **接口描述**：返回所有预订的 ID 列表，可用查询参数过滤。

### 请求参数

**URL 查询参数（均为可选）**

| 参数名称 | 类型 | 是否必填 | 示例 | 备注 |
|---|---|---|---|---|
| firstname | string | 否 | Jim | 按名字过滤 |
| lastname | string | 否 | Brown | 按姓氏过滤 |
| checkin | string | 否 | 2014-03-13 | 入住日期，返回该日期及之后的预订 |
| checkout | string | 否 | 2014-05-21 | 退房日期，返回该日期及之前的预订 |

### 返回数据
- 响应状态码：`200`
- 返回示例：
```json
[
  {"bookingid": 1},
  {"bookingid": 2},
  {"bookingid": 3},
  {"bookingid": 4}
]
```

### 请求示例
```bash
# 全部
curl https://restful-booker.herokuapp.com/booking

# 按姓名过滤
curl "https://restful-booker.herokuapp.com/booking?firstname=Jim&lastname=Brown"

# 按日期范围过滤
curl "https://restful-booker.herokuapp.com/booking?checkin=2014-03-13&checkout=2014-05-21"
```

---

## 四、获取单条预订详情（GetBooking）

### 基本信息
- **Path**：`/booking/{id}`
- **Method**：`GET`
- **接口描述**：根据预订 ID 返回预订详情。

### 请求参数

**headers**

| 参数名称 | 参数值 | 是否必填 | 备注 |
|---|---|---|---|
| Accept | application/json | 否 | 默认返回 JSON，可设为 `application/xml` 返回 XML |

**URL 参数**

| 参数名称 | 类型 | 是否必填 | 备注 |
|---|---|---|---|
| id | int | 是 | 预订 ID |

### 返回数据
- 响应状态码：`200`（找到）/ `404 Not Found`（不存在）
- 返回示例：
```json
{
  "firstname": "Sally",
  "lastname": "Brown",
  "totalprice": 111,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2013-02-23",
    "checkout": "2014-10-23"
  },
  "additionalneeds": "Breakfast"
}
```

### 请求示例
```bash
curl https://restful-booker.herokuapp.com/booking/1 \
  -H "Accept: application/json"
```

---

## 五、创建预订（CreateBooking）

### 基本信息
- **Path**：`/booking`
- **Method**：`POST`
- **接口描述**：创建一条新的预订记录（无需 Token）。

### 请求参数

**headers**

| 参数名称 | 参数值 | 是否必填 | 备注 |
|---|---|---|---|
| Content-Type | application/json | 是 | |
| Accept | application/json | 是 | 否则可能返回 XML/418 |

**body**

| 参数名称 | 类型 | 是否必填 | 示例 | 备注 |
|---|---|---|---|---|
| firstname | string | 是 | Jim | 名字 |
| lastname | string | 是 | Brown | 姓氏 |
| totalprice | int | 是 | 111 | 总价 |
| depositpaid | boolean | 是 | true | 是否已付定金 |
| bookingdates.checkin | string | 是 | 2018-01-01 | 入住日期 |
| bookingdates.checkout | string | 是 | 2019-01-01 | 退房日期 |
| additionalneeds | string | 否 | Breakfast | 额外需求 |

### 返回数据
- 响应状态码：`200`
- 返回示例（会返回新生成的 bookingid 和完整对象）：
```json
{
  "bookingid": 11,
  "booking": {
    "firstname": "Jim",
    "lastname": "Brown",
    "totalprice": 111,
    "depositpaid": true,
    "bookingdates": {
      "checkin": "2018-01-01",
      "checkout": "2019-01-01"
    },
    "additionalneeds": "Breakfast"
  }
}
```

### 请求示例
```bash
curl -X POST https://restful-booker.herokuapp.com/booking \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "firstname": "Jim",
    "lastname": "Brown",
    "totalprice": 111,
    "depositpaid": true,
    "bookingdates": {
      "checkin": "2018-01-01",
      "checkout": "2019-01-01"
    },
    "additionalneeds": "Breakfast"
  }'
```

---

## 六、更新预订 - 全量（UpdateBooking）

### 基本信息
- **Path**：`/booking/{id}`
- **Method**：`PUT`
- **接口描述**：全量更新一条已存在的预订，**需要 Token**。请求体必须包含所有字段。

### 请求参数

**headers**

| 参数名称 | 参数值 | 是否必填 | 备注 |
|---|---|---|---|
| Content-Type | application/json | 是 | |
| Accept | application/json | 是 | |
| Cookie | token=`<你的token>` | 是（二选一） | 方式一：Cookie 携带 Token |
| Authorization | Basic YWRtaW46cGFzc3dvcmQxMjM= | 是（二选一） | 方式二：Basic Auth（admin:password123 的 base64） |

**URL 参数**

| 参数名称 | 类型 | 是否必填 | 备注 |
|---|---|---|---|
| id | int | 是 | 要更新的预订 ID |

**body**：字段同「创建预订」，需全部提供。

### 返回数据
- 响应状态码：`200`（成功）/ `403 Forbidden`（Token 缺失或无效）
- 返回更新后的完整预订对象。

### 请求示例
```bash
curl -X PUT https://restful-booker.herokuapp.com/booking/1 \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Cookie: token=abc123def456ghi" \
  -d '{
    "firstname": "James",
    "lastname": "Brown",
    "totalprice": 111,
    "depositpaid": true,
    "bookingdates": {
      "checkin": "2018-01-01",
      "checkout": "2019-01-01"
    },
    "additionalneeds": "Breakfast"
  }'
```

---

## 七、更新预订 - 部分（PartialUpdateBooking）

### 基本信息
- **Path**：`/booking/{id}`
- **Method**：`PATCH`
- **接口描述**：部分更新一条已存在的预订，**需要 Token**。只需提交要修改的字段。

### 请求参数
headers 同「全量更新」（需携带 Token）。

**body（按需提交部分字段）**

| 参数名称 | 类型 | 是否必填 | 示例 |
|---|---|---|---|
| firstname | string | 否 | James |
| totalprice | int | 否 | 222 |

### 返回数据
- 响应状态码：`200` / `403 Forbidden`
- 返回更新后的完整预订对象。

### 请求示例
```bash
curl -X PATCH https://restful-booker.herokuapp.com/booking/1 \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Cookie: token=abc123def456ghi" \
  -d '{"firstname":"James","totalprice":222}'
```

---

## 八、删除预订（DeleteBooking）

### 基本信息
- **Path**：`/booking/{id}`
- **Method**：`DELETE`
- **接口描述**：删除一条预订，**需要 Token**。

### 请求参数

**headers**

| 参数名称 | 参数值 | 是否必填 | 备注 |
|---|---|---|---|
| Content-Type | application/json | 是 | |
| Cookie | token=`<你的token>` | 是（二选一） | 或用 Basic Auth |

**URL 参数**

| 参数名称 | 类型 | 是否必填 | 备注 |
|---|---|---|---|
| id | int | 是 | 要删除的预订 ID |

### 返回数据
- 响应状态码：`201 Created`（删除成功）/ `403 Forbidden`（无 Token）/ `405 Method Not Allowed`（重复删除）

### 请求示例
```bash
curl -X DELETE https://restful-booker.herokuapp.com/booking/1 \
  -H "Content-Type: application/json" \
  -H "Cookie: token=abc123def456ghi"
```

---

## 完整业务流程示例（认证 → 创建 → 更新 → 删除）

```bash
# 1. 获取 Token
TOKEN=$(curl -s -X POST https://restful-booker.herokuapp.com/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
echo "Token = $TOKEN"

# 2. 创建预订，拿到 bookingid
curl -s -X POST https://restful-booker.herokuapp.com/booking \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -d '{"firstname":"Tom","lastname":"Lee","totalprice":300,"depositpaid":true,"bookingdates":{"checkin":"2025-01-01","checkout":"2025-01-05"},"additionalneeds":"Lunch"}'

# 3. 用 Token 更新 id=1 的预订
curl -s -X PUT https://restful-booker.herokuapp.com/booking/1 \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -H "Cookie: token=$TOKEN" \
  -d '{"firstname":"Updated","lastname":"User","totalprice":999,"depositpaid":false,"bookingdates":{"checkin":"2025-02-01","checkout":"2025-02-10"},"additionalneeds":"Dinner"}'

# 4. 删除 id=1
curl -s -X DELETE https://restful-booker.herokuapp.com/booking/1 \
  -H "Content-Type: application/json" -H "Cookie: token=$TOKEN"
```

---

## 测试要点 / 练习建议

1. **认证测试**：正确账号 `admin / password123` 应返回 Token；错误密码应返回 `Bad credentials`；不带 Token 调用 PUT/DELETE 应返回 `403`。
2. **CRUD 测试**：创建后用返回的 `bookingid` 查询、更新、删除，验证状态码与数据一致性。
3. **参数校验**：`GET /booking` 测试无参数、单参数、多参数组合及非法值（如不存在的姓名）。
4. **边界 / 异常**：查询不存在的 id（应 `404`）、重复删除（应 `405`）、缺字段创建、错误日期格式。
5. **找 bug**：该 API 故意保留了一些缺陷，适合作为「缺陷发现」练习，观察哪些响应不符合 RESTful 规范。
6. **数据重置**：每 10 分钟自动恢复初始 10 条记录，可放心增删，不怕弄乱环境。

## 注意事项

- 部署在 Heroku 免费实例上，**首次访问可能有几秒冷启动延迟**，可先调 `/ping` 唤醒。
- 写操作支持两种鉴权方式：① Cookie 携带 `token=<token>`；② Basic Auth（`admin:password123`）。
- 若担心公网实例不稳定，可按官方源码 `github.com/mwinteringham/restful-booker` 本地自部署。
