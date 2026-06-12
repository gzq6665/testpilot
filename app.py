# -*- coding: utf-8 -*-
"""TestPilot —— 基于 LLM Agent 的智能接口测试平台（Streamlit 入口）。

运行: streamlit run app.py
依赖: Ollama 已启动且已拉取 qwen2.5:7b 与 bge-m3；Mock 服务已启动（python mock_server/app.py）
"""
import json

import pandas as pd
import streamlit as st

from config import EMBED_MODEL
from models import get_active_model, list_models, set_active_model
from profiles import get_active_profile, list_profiles, set_active

st.set_page_config(page_title="TestPilot 智能测试平台", page_icon="🚀", layout="wide")

st.sidebar.title("🚀 TestPilot")
st.sidebar.caption("基于 LLM Agent 的智能接口测试平台")

# ---- 被测系统切换（Profile） ----
_profiles = list_profiles()
_active = get_active_profile()
_names = [p["name"] for p in _profiles]
_chosen = st.sidebar.selectbox("被测系统", _names, index=_names.index(_active["name"]))
if _chosen != _active["name"]:
    set_active(next(p["id"] for p in _profiles if p["name"] == _chosen))
    st.rerun()
active_profile = get_active_profile()

# ---- 大模型切换 ----
_models = list_models()
_active_model = get_active_model()
_model_names = [m["name"] for m in _models]
_chosen_model = st.sidebar.selectbox("对话模型", _model_names,
                                     index=_model_names.index(_active_model["name"]))
if _chosen_model != _active_model["name"]:
    set_active_model(next(m["id"] for m in _models if m["name"] == _chosen_model))
    st.rerun()
active_model = get_active_model()

page = st.sidebar.radio("功能导航", [
    "📚 接口文档问答 (RAG)",
    "📝 测试用例生成",
    "🤖 多Agent工作流 (LangGraph)",
    "🛠️ Agent执行助手 (Function Calling)",
    "📊 执行结果看板",
    "⚙️ 项目配置",
])
st.sidebar.divider()
_provider_label = "本地 Ollama" if active_model.get("provider") == "ollama" else "API 调用"
st.sidebar.markdown(
    f"**对话模型**: `{active_model['model']}`（{_provider_label}）\n\n"
    f"**Embedding**: `{EMBED_MODEL}`（本地）\n\n"
    f"**被测系统**: `{active_profile['base_url']}`"
)


def cases_to_df(cases: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(cases)
    if "params" in df.columns:
        df["params"] = df["params"].apply(lambda x: json.dumps(x, ensure_ascii=False))
    return df


# ---------------- 页面1：RAG 文档问答 ----------------
if page.startswith("📚"):
    st.title("📚 接口文档问答")
    st.caption("基于 RAG（FAISS + bge-m3）检索接口文档，回答测试相关问题")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 重建知识库索引", use_container_width=True):
            with st.spinner("正在切分文档并构建向量索引..."):
                from rag.vectorstore import build_vector_store
                build_vector_store()
            st.success("知识库索引重建完成")

    uploaded = st.file_uploader(
        f"上传文档到【{active_profile['name']}】知识库（md/txt/pdf）", type=["md", "txt", "pdf"])
    if uploaded:
        from profiles import profile_docs_dir
        (profile_docs_dir(active_profile["id"]) / uploaded.name).write_bytes(uploaded.getvalue())
        st.success(f"已保存 {uploaded.name} 到项目独立知识库，请点击右上角重建索引")

    question = st.text_input("提问", placeholder="例如：注册接口有哪些必填参数？登录失败有哪些业务状态码？")
    if st.button("提问", type="primary") and question:
        with st.spinner("检索文档并生成回答中..."):
            from rag.qa_chain import answer
            result = answer(question)
        st.markdown("### 回答")
        st.markdown(result["answer"])
        with st.expander("🔍 查看检索到的文档片段"):
            st.text(result["context"])

# ---------------- 页面2：用例生成 ----------------
elif page.startswith("📝"):
    st.title("📝 测试用例生成")
    st.caption("RAG 检索接口文档 → LLM 生成结构化用例 → 导出 Excel / pytest 脚本")

    col1, col2 = st.columns([3, 1])
    module = col1.text_input("待测模块/接口", value="登录接口")
    num_cases = col2.number_input("用例数量", 3, 20, 8)

    if st.button("生成用例", type="primary"):
        with st.spinner(f"正在为【{module}】生成测试用例（本地模型推理，请稍候）..."):
            from agents.case_generator import generate_cases
            out = generate_cases(module, int(num_cases))
        st.session_state["gen_cases"] = out["cases"]
        st.session_state["gen_module"] = module

    if st.session_state.get("gen_cases"):
        cases = st.session_state["gen_cases"]
        st.success(f"已生成 {len(cases)} 条用例")
        st.dataframe(cases_to_df(cases), use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            df = cases_to_df(cases)
            import io
            buf = io.BytesIO()
            df.to_excel(buf, index=False)
            st.download_button("⬇️ 导出 Excel", buf.getvalue(),
                               file_name="test_cases.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c2:
            if st.button("🐍 生成 pytest 脚本"):
                from tools.pytest_gen import generate_pytest_file
                path = generate_pytest_file(cases, st.session_state.get("gen_module", "module"))
                st.success(f"已生成: {path}")
        with c3:
            if st.button("▶️ 立即执行用例"):
                with st.spinner("执行中..."):
                    from agents.executor import execute_cases
                    results = execute_cases(cases)
                st.session_state["last_results"] = results
                passed = sum(1 for r in results if r["passed"])
                st.info(f"执行完成：{passed}/{len(results)} 通过（详见执行结果看板）")

# ---------------- 页面3：多Agent工作流 ----------------
elif page.startswith("🤖"):
    st.title("🤖 多 Agent 工作流")
    st.caption("LangGraph 编排：用例生成 Agent → 评审 Agent →（评审不通过自动带意见重生成）→ 执行 → 失败分析 Agent")

    st.graphviz_chart("""
    digraph {
        rankdir=LR; node [shape=box, style=rounded];
        生成Agent -> 评审Agent;
        评审Agent -> 生成Agent [label="不通过(≤2轮)", style=dashed];
        评审Agent -> 执行器 [label="通过"];
        执行器 -> 分析Agent; 分析Agent -> 报告;
    }
    """)

    col1, col2 = st.columns([3, 1])
    module = col1.text_input("待测模块", value="注册接口")
    num_cases = col2.number_input("用例数量", 3, 15, 6)

    if st.button("🚀 启动工作流", type="primary"):
        from agents.workflow import run_workflow
        progress = st.container()
        final_state = {}
        with st.spinner("多 Agent 工作流运行中（本地模型推理较慢，请耐心等待）..."):
            for node, update in run_workflow(module, int(num_cases)):
                final_state.update(update)
                with progress:
                    if node == "generate":
                        st.info(f"✏️ 生成 Agent（第 {update['iteration']} 轮）：产出 {len(update['cases'])} 条用例")
                    elif node == "review":
                        r = update["review"]
                        icon = "✅" if r.get("passed") else "❌"
                        st.info(f"{icon} 评审 Agent：得分 {r.get('score')}，{r.get('summary','')}")
                        if r.get("issues"):
                            st.caption("问题：" + "；".join(map(str, r["issues"])))
                    elif node == "execute":
                        rs = update["results"]
                        p = sum(1 for x in rs if x["passed"])
                        st.info(f"▶️ 执行器：{p}/{len(rs)} 条通过")
                    elif node == "analyze":
                        st.info(f"📋 分析 Agent：报告已生成 → {update.get('report_path','')}")
                        st.info(f"🐍 pytest 回归脚本已生成 → {update.get('pytest_path','')}，"
                                f"可用 `pytest 脚本路径 -v` 重复执行")

        if final_state.get("cases"):
            st.subheader("最终用例")
            st.dataframe(cases_to_df(final_state["cases"]), use_container_width=True)
        if final_state.get("results"):
            st.session_state["last_results"] = final_state["results"]
        if final_state.get("report"):
            st.subheader("失败分析报告")
            st.markdown(final_state["report"])

# ---------------- 页面4：Agent执行助手 ----------------
elif page.startswith("🛠️"):
    st.title("🛠️ Agent 执行助手")
    st.caption("基于 Function Calling 的 ReAct Agent，带多轮对话记忆（LangGraph SQLite Checkpointer）："
               "历史会话持久化，重启后可继续；支持\"再测一次\"\"刚才那个接口\"等上下文指代")

    from agents.executor import get_react_agent
    from agents.memory import (create_thread, delete_thread, get_thread_messages,
                               list_threads, set_thread_title)

    agent = get_react_agent()

    # ---- 会话管理 ----
    threads = list_threads()
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        if st.button("➕ 新建会话", use_container_width=True):
            st.session_state["chat_thread_id"] = create_thread()
            st.rerun()
    with col1:
        if threads:
            options = {f"{t['title']}（{t['created']}）": t["id"] for t in threads}
            current_id = st.session_state.get("chat_thread_id", threads[0]["id"])
            labels = list(options.keys())
            ids = list(options.values())
            idx = ids.index(current_id) if current_id in ids else 0
            chosen = st.selectbox("会话记录", labels, index=idx)
            st.session_state["chat_thread_id"] = options[chosen]
    with col3:
        if threads and st.button("🗑️ 删除会话", use_container_width=True,
                                 help="删除当前选中的会话及其全部对话记忆（不可恢复）"):
            delete_thread(st.session_state.get("chat_thread_id", threads[0]["id"]))
            st.session_state.pop("chat_thread_id", None)
            st.rerun()

    if "chat_thread_id" not in st.session_state:
        st.session_state["chat_thread_id"] = create_thread()
    thread_id = st.session_state["chat_thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    # ---- 从 Checkpointer 回显该会话的完整历史 ----
    history = get_thread_messages(agent, thread_id)
    if not history:
        st.markdown("示例指令：")
        st.code("用预置账号登录系统，然后调用是否登录接口验证登录态", language=None)
        st.code("再测一次未登录场景：先清除会话，再调用是否登录接口", language=None)
    for msg in history:
        if msg.type == "human":
            st.chat_message("user").markdown(msg.content)
        elif msg.type == "ai":
            with st.chat_message("assistant"):
                if getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        st.caption(f"🔧 调用工具 `{tc['name']}` 参数 `{json.dumps(tc['args'], ensure_ascii=False)}`")
                if msg.content:
                    st.markdown(msg.content)
        elif msg.type == "tool":
            with st.chat_message("assistant"):
                st.caption(f"↩️ 工具返回: `{str(msg.content)[:300]}`")

    # ---- 对话输入：只发新消息，历史由 Checkpointer 自动携带 ----
    instr = st.chat_input("输入测试指令...")
    if instr:
        set_thread_title(thread_id, instr)
        st.chat_message("user").markdown(instr)
        with st.chat_message("assistant"):
            try:
                with st.spinner("Agent 思考并调用工具中..."):
                    seen = len(history) + 1
                    for chunk in agent.stream({"messages": [("user", instr)]},
                                              config=config, stream_mode="values"):
                        msgs = chunk["messages"]
                        for msg in msgs[seen:]:
                            if msg.type == "ai" and getattr(msg, "tool_calls", None):
                                for tc in msg.tool_calls:
                                    st.caption(f"🔧 调用工具 `{tc['name']}` 参数 `{json.dumps(tc['args'], ensure_ascii=False)}`")
                            elif msg.type == "tool":
                                st.caption(f"↩️ 工具返回: `{str(msg.content)[:300]}`")
                            elif msg.type == "ai" and msg.content:
                                st.markdown(msg.content)
                        seen = len(msgs)
            except Exception as e:
                emsg = str(e)
                if "more system memory" in emsg:
                    st.error("⚠️ 内存不足，模型加载失败。请关闭一些占内存的程序（浏览器多余标签页、"
                             "微信等）后重试；若仍失败，可在 config.py 中将 CHAT_MODEL 换成 qwen2.5:3b。")
                elif "status code: 500" in emsg or "ResponseError" in type(e).__name__:
                    st.error(f"⚠️ Ollama 服务异常：{emsg[:200]}。请确认 Ollama 正在运行（ollama list）后重试。")
                else:
                    st.error(f"⚠️ 执行出错：{emsg[:300]}")

# ---------------- 页面5：执行结果看板 ----------------
elif page.startswith("📊"):
    st.title("📊 执行结果看板")
    results = st.session_state.get("last_results")
    if not results:
        st.info("暂无执行结果。请先在「用例生成」或「多Agent工作流」页面执行用例。")
    else:
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("用例总数", total)
        c2.metric("通过", passed)
        c3.metric("失败", total - passed)
        c4.metric("通过率", f"{passed / total * 100:.1f}%")

        df = pd.DataFrame(results)
        df["params"] = df["params"].apply(lambda x: json.dumps(x, ensure_ascii=False))
        df["response"] = df["response"].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else str(x))
        st.dataframe(
            df.style.map(lambda v: "background-color: #ffcccc" if v is False else
                         ("background-color: #ccffcc" if v is True else ""), subset=["passed"]),
            use_container_width=True)

        fail_df = df[~df["passed"]]
        if not fail_df.empty:
            st.subheader("失败用例详情")
            for _, row in fail_df.iterrows():
                with st.expander(f"❌ {row['case_id']} {row['title']}"):
                    st.write(f"**失败原因**: {row['reason']}")
                    st.write(f"**请求**: {row['method']} {row['api_path']} 参数 {row['params']}")
                    st.write(f"**响应**: {row['response']}")

# ---------------- 页面6：项目配置 ----------------
elif page.startswith("⚙️"):
    st.title("⚙️ 项目配置（被测系统 Profile）")
    st.caption("每个被测系统一份配置档案：地址、登录方式、响应约定、预置数据。"
               "用例生成 Prompt、执行器、pytest 模板、知识库均按当前项目动态加载，互不干扰。")

    st.subheader(f"当前项目：{active_profile['name']}")
    st.json(active_profile)

    st.divider()
    st.subheader("➕ 新建 / 更新项目")
    st.caption("提示：填写已存在的项目名称将覆盖更新该项目")
    with st.form("profile_form"):
        name = st.text_input("项目名称*", placeholder="例如：litemall 商城系统")
        base_url = st.text_input("被测系统地址*", placeholder="http://127.0.0.1:8080")
        assert_style = st.selectbox(
            "断言风格*", ["biz_status", "http_status"],
            help="biz_status: HTTP恒200，业务结果在响应JSON的status字段；"
                 "http_status: 直接用HTTP状态码(200/400/401)表达业务结果")
        body_format = st.selectbox(
            "请求体格式*", ["form", "json"],
            help="form: application/x-www-form-urlencoded 表单编码；"
                 "json: application/json（RESTful 接口、参数含嵌套对象时必选）")
        biz_conventions = st.text_area(
            "响应/调用约定", placeholder="例如：业务接口均为 POST JSON；成功返回 errno=0，失败返回非0 errno 和 errmsg")
        login_path = st.text_input("登录接口路径", placeholder="/admin/auth/login（无登录态可留空）")
        login_method = st.selectbox("登录请求方法", ["POST", "GET"])
        login_params = st.text_area(
            "登录参数（JSON）", placeholder='{"username": "admin", "password": "admin123"}')
        seed_notes = st.text_area(
            "测试环境预置数据约定", placeholder="例如：预置管理员 admin/admin123；测试商品ID为 1001；注册用户名需每条用例唯一")
        submitted = st.form_submit_button("保存项目", type="primary")

    if submitted:
        if not name or not base_url:
            st.error("项目名称和被测系统地址为必填项")
        else:
            login = {}
            if login_path.strip():
                try:
                    params = json.loads(login_params) if login_params.strip() else {}
                except json.JSONDecodeError:
                    st.error("登录参数不是合法 JSON")
                    st.stop()
                login = {"path": login_path.strip(), "method": login_method, "params": params}
            from profiles import save_profile
            existing = next((p for p in _profiles if p["name"] == name), None)
            profile = save_profile({
                "id": existing["id"] if existing else "",
                "name": name, "base_url": base_url.rstrip("/"),
                "assert_style": assert_style,
                "body_format": body_format,
                "biz_conventions": biz_conventions.strip(),
                "login": login, "seed_notes": seed_notes.strip(),
            })
            set_active(profile["id"])
            st.success(f"项目【{name}】已保存并切换为当前项目。"
                       f"下一步：到「接口文档问答」页面上传该系统的接口文档并重建索引。")
            st.rerun()

    st.divider()
    st.subheader("🗑️ 删除项目")
    if len(_profiles) <= 1:
        st.caption("当前只有一个项目，不能删除（平台至少保留一个项目）。")
    else:
        del_name = st.selectbox("选择要删除的项目", _names, key="del_select")
        del_id = next(p["id"] for p in _profiles if p["name"] == del_name)
        confirm = st.checkbox(
            f"我确认删除【{del_name}】，该项目的配置、知识库文档和向量索引将一并删除（不可恢复）")
        if st.button("删除项目", disabled=not confirm):
            from profiles import delete_profile
            try:
                delete_profile(del_id)
                st.success(f"项目【{del_name}】已删除")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # ================= 模型管理 =================
    st.divider()
    st.header("🧠 模型管理")
    st.caption("本地 Ollama 模型与 OpenAI 兼容 API（DeepSeek/通义千问/Kimi/GLM/OpenAI 等）统一管理，"
               "侧边栏随时切换，全平台即时生效。注意：RAG 的 Embedding 固定使用本地 bge-m3，与对话模型无关。")

    st.subheader(f"当前模型：{active_model['name']}")
    _safe_model = {k: ("******" if k == "api_key" and v else v) for k, v in active_model.items()}
    st.json(_safe_model)

    st.subheader("➕ 新增 / 更新模型")
    st.caption("提示：填写已存在的模型名称将覆盖更新")
    with st.form("model_form"):
        m_name = st.text_input("显示名称*", placeholder="例如：DeepSeek-V3（API）")
        m_provider = st.selectbox("类型*", ["openai", "ollama"],
                                  help="openai: 任何 OpenAI 兼容 API；ollama: 本地 Ollama 模型")
        m_model = st.text_input("模型名*", placeholder="API 填模型ID（如 deepseek-chat）；本地填 ollama 模型名（如 qwen2.5:3b）")
        m_base_url = st.text_input("Base URL",
                                   placeholder="API 示例: https://api.deepseek.com/v1；本地默认 http://localhost:11434")
        m_api_key = st.text_input("API Key（本地模型留空）", type="password")
        m_submitted = st.form_submit_button("保存模型", type="primary")

    if m_submitted:
        if not m_name or not m_model:
            st.error("显示名称和模型名为必填项")
        elif m_provider == "openai" and not m_api_key and not any(
                m["name"] == m_name and m.get("api_key") for m in _models):
            st.error("API 模型需要填写 API Key")
        else:
            from models import save_model
            saved = save_model({
                "name": m_name, "provider": m_provider, "model": m_model.strip(),
                "base_url": m_base_url.strip(), "api_key": m_api_key.strip(),
            })
            set_active_model(saved["id"])
            st.success(f"模型【{m_name}】已保存并切换为当前模型")
            st.rerun()

    st.subheader("🗑️ 删除模型")
    if len(_models) <= 1:
        st.caption("当前只有一个模型，不能删除。")
    else:
        dm_name = st.selectbox("选择要删除的模型", _model_names, key="del_model_select")
        dm_id = next(m["id"] for m in _models if m["name"] == dm_name)
        dm_confirm = st.checkbox(f"我确认删除模型【{dm_name}】")
        if st.button("删除模型", disabled=not dm_confirm):
            from models import delete_model
            try:
                delete_model(dm_id)
                st.success(f"模型【{dm_name}】已删除")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
