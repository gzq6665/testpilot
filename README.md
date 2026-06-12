# 🚀 TestPilot —— 基于 LLM Agent 的智能接口测试平台

针对接口测试中**用例编写耗时、文档查阅低效、失败排查依赖人工**的痛点，基于
**LangChain + LangGraph** 构建的智能测试 Agent 平台，覆盖
「文档问答 → 用例生成 → 用例评审 → 接口执行 → 失败归因分析 → 回归脚本沉淀」全链路。

- **多模型**：本地 Ollama（qwen2.5:7b）与 OpenAI 兼容 API（DeepSeek/通义/Kimi/GLM 等）统一管理、随时切换；
- **多项目**：被测系统以配置档案（Profile）接入，知识库按项目隔离，零代码接入新系统；
- **有记忆**：Agent 多轮对话记忆 + SQLite 跨会话持久化，支持会话管理。

## ✨ 核心功能

| 模块 | 说明 | 关键技术 |
|---|---|---|
| 📚 接口文档问答 | 接口文档切分入库，对话式检索问答 | RAG / FAISS / bge-m3 |
| 📝 测试用例生成 | 基于文档上下文生成结构化用例（正常/异常/边界），导出 Excel / pytest 脚本 | RAG + 结构化 Prompt + JSON Mode |
| 🤖 多 Agent 工作流 | 生成 Agent → 评审 Agent →（不通过自动带意见重生成≤2轮）→ 执行 → 分析 Agent，自动沉淀 pytest 回归脚本 | LangGraph StateGraph / 条件路由 / Checkpointer |
| 🛠️ Agent 执行助手 | 自然语言下达指令，Agent 自主多步调用工具完成接口测试；多轮对话记忆 + 会话管理（新建/切换/删除），重启后可恢复 | Function Calling / ReAct / SQLite Checkpointer |
| 📊 执行结果看板 | 通过率指标、失败用例下钻 | Streamlit |
| ⚙️ 多项目接入 | 被测系统配置档案（Profile）：地址/登录方式/断言风格/预置数据可配置，知识库与向量索引按项目隔离 | 配置与逻辑分离 |
| 🧠 多模型切换 | 本地 Ollama 与 OpenAI 兼容 API 统一注册/切换/删除，全平台即时生效，API Key 不入库 | 模型工厂 / LangChain 模型抽象 |
| 🔌 MCP Server | 测试工具封装为 MCP 协议服务，任意 MCP 客户端（Claude Code 等）可调用 | MCP (FastMCP) |

## 🏗️ 架构

```
                ┌──────────────────────────────────────────────────┐
                │                 Streamlit 前端（6 页面）            │
                │  问答 / 用例生成 / 工作流 / Agent助手 / 看板 / 配置  │
                └───┬───────────┬────────────────┬─────────────────┘
                    │           │                │
      ┌─────────────▼──┐  ┌─────▼─────────────────────────────┐  ┌──▼─────────────┐
      │   RAG 问答链    │  │  LangGraph 多 Agent 工作流          │  │ ReAct 执行Agent │
      │ FAISS + bge-m3 │  │  生成 → 评审 ⟲ → 执行 → 分析        │  │ (Function Call)│
      └───────┬────────┘  │  └→ pytest 回归脚本沉淀             │  └──┬─────────────┘
              │           └─────┬─────────────────────────────┘     │
   ┌──────────▼─────────┐       │            ┌───────────────────────▼──────────┐
   │ 知识库（按项目隔离） │       │            │ SQLite Checkpointer（对话记忆/    │
   │ data/docs/<项目id>/ │       │            │ 会话管理，重启可恢复）             │
   └────────────────────┘       │            └──────────────────────────────────┘
                                │
   ┌────────────────────┐  ┌────▼───────────────────────┐   ┌────────────────────┐
   │ 模型工厂 get_llm()  │  │ 工具层: http_request /      │◄──│   MCP Server       │
   │ ChatOllama (本地)   │  │ db_query / pytest_gen      │   │  (标准协议暴露工具)  │
   │ ChatOpenAI (API)   │  └────┬───────────────────────┘   └────────────────────┘
   └────────────────────┘       │ HTTP（按 Profile 的 base_url/登录配置/断言风格）
                           ┌────▼───────────────────────┐
                           │ 被测系统（Profile 可配置）    │
                           │ 默认项目: 黑马理财本地 Mock   │
                           └────────────────────────────┘
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装 Ollama 并拉取模型（Embedding 必需；对话模型可改用 API）
ollama pull qwen2.5:7b      # 本地对话/Agent 模型（支持 Function Calling）
ollama pull bge-m3          # 中文 Embedding 模型（RAG 必需，始终本地）

# 安装依赖
pip install -r requirements.txt
```

> 内存提示：16G 内存机器跑 7B 模型较紧，建议设置环境变量 `OLLAMA_NUM_PARALLEL=1`，
> 上下文/输出长度可在 `config.py` 的 `NUM_CTX` / `NUM_PREDICT` 调整。
> 嫌本地推理慢可在「项目配置 → 模型管理」接入 DeepSeek 等 API 模型。

### 2. 一键启动

```powershell
.\start_all.ps1    # 同时启动 Mock 被测系统(9999) 与 Streamlit 平台(8501)
```

或分别启动：

```bash
python mock_server/app.py    # 默认演示项目的被测系统（含 /__reset__ 数据重置接口）
streamlit run app.py
```

### 3. 验证脚本

```bash
python scripts/smoke_test.py            # 冒烟：知识库构建+RAG检索+接口执行+pytest生成（快）
python scripts/smoke_test.py --full     # 额外验证 LLM 问答与用例生成（慢）
python scripts/workflow_test.py         # 多Agent工作流 + ReAct Agent 端到端
python scripts/memory_test.py           # Agent 记忆：多轮对话 + 跨进程持久化
python scripts/profile_test.py          # 多项目：创建/切换/知识库隔离/模板装配
python scripts/model_switch_test.py     # 多模型：Ollama/OpenAI API 工厂切换
python scripts/report_to_pytest.py      # 把历史工作流报告转为 pytest 回归脚本
pytest tests_generated/ -v              # 运行沉淀下来的回归脚本
```

### 4. （可选）MCP Server

```bash
python mcp_server/server.py
```

在 Claude Code / Claude Desktop 等客户端的 `mcp.json` 中配置后，可直接对话调用
`http_request`、`login_test_user`、`list_api_docs`、`get_sut_info` 等测试工具。

## 🔄 接入一个新的被测系统（零代码）

1. 「⚙️ 项目配置」页新建项目：被测地址、断言风格（`biz_status`：HTTP恒200业务码在JSON
   / `http_status`：直接用HTTP状态码）、请求体格式（`form` 表单 / `json`，RESTful
   接口或参数含嵌套对象时选 json）、登录接口配置、响应约定、预置数据约定；
2. 「📚 接口文档问答」页上传该系统的接口文档（md/txt/pdf）→ 重建索引；
3. 侧边栏切换项目，全部功能即可使用。用例生成 Prompt、执行器断言、Agent 提示词、
   pytest 模板均按当前 Profile 动态装配。


## 📁 目录结构

```
testpilot/
├── app.py                  # Streamlit 入口（6 个功能页面）
├── config.py               # 模型推理参数 / 路径 / MySQL 配置
├── profiles.py             # 被测系统 Profile：注册/切换/删除，知识库按项目隔离
├── models.py               # 大模型注册表：Ollama 与 OpenAI 兼容 API 统一管理
├── rag/                    # RAG：文档加载切分、按项目隔离的 FAISS 索引、问答链
├── agents/
│   ├── llm.py              #   模型工厂（ChatOllama/ChatOpenAI）+ JSON 容错解析
│   ├── case_generator.py   #   用例生成 Agent（Profile 约定动态注入 Prompt）
│   ├── case_reviewer.py    #   用例评审 Agent
│   ├── executor.py         #   确定性执行器 + ReAct 工具调用 Agent
│   ├── analyzer.py         #   失败归因分析 Agent（枚举归因防编造）
│   ├── memory.py           #   会话记忆：SQLite Checkpointer + 会话注册表（增删查）
│   └── workflow.py         #   LangGraph 工作流编排（条件路由+迭代重生成+脚本沉淀）
├── tools/                  # 工具层：http_request / db_query / pytest 脚本生成
├── mcp_server/             # MCP Server（FastMCP，stdio）
├── mock_server/            # 默认演示项目的被测系统 Mock（Flask，含 /__reset__）
├── data/
│   ├── docs/<项目id>/       # 各项目独立的接口文档知识库
│   ├── vector_store/       # 各项目独立的 FAISS 索引
│   ├── profiles/           # 被测系统配置档案
│   ├── models.json         # 模型注册表（含 API Key，已 gitignore）
│   └── agent_memory.sqlite # Agent 对话记忆（已 gitignore）
├── examples/               # 精选示例：真实运行报告（含公网系统发现7处缺陷）与沉淀的回归脚本
├── tests_generated/        # 自动沉淀的 pytest 回归脚本（gitignore，本地生成）
├── reports/                # 工作流执行报告（gitignore，本地生成）
└── scripts/                # 冒烟/端到端/记忆/多项目/多模型 验证脚本
```


