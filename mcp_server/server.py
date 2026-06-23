# -*- coding: utf-8 -*-
"""TestPilot MCP Server：将测试工具封装为 MCP 标准协议服务。

任何支持 MCP 的客户端（Claude Desktop、Claude Code、Cherry Studio 等）
都可以直接调用这些测试工具，实现"对话即测试"。

运行方式（stdio）：
    python mcp_server/server.py

Claude Desktop / Claude Code 配置示例（mcp.json）：
{
  "mcpServers": {
    "testpilot": {
      "command": "python",
      "args": ["D:/code/20260611_agent测试/testpilot/mcp_server/server.py"]
    }
  }
}
"""
import json
import sys
from pathlib import Path

# 保证可以 import 项目根目录下的模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from profiles import get_active_profile, profile_docs_dir
from tools.http_tool import do_request, login_seed_user, reset_session

mcp = FastMCP("testpilot-tools")


@mcp.tool()
def list_api_docs() -> str:
    """列出当前被测项目知识库中的接口文档内容，供查阅接口定义。"""
    profile = get_active_profile()
    parts = []
    for p in sorted(profile_docs_dir(profile["id"]).glob("*.md")):
        parts.append(f"# 文档: {p.name}\n\n{p.read_text(encoding='utf-8')}")
    return "\n\n".join(parts) or "知识库为空"


@mcp.tool()
def http_request(method: str, path: str, form_data: str = "{}") -> str:
    """向被测系统发送 HTTP 请求（自动保持会话 Cookie）。

    Args:
        method: GET 或 POST
        path: 接口路径，如 /member/public/login
        form_data: 表单参数 JSON 字符串，如 '{"keywords":"13800000001","password":"Test@123"}'
    """
    try:
        data = json.loads(form_data) if form_data else {}
    except json.JSONDecodeError:
        return "form_data 不是合法 JSON"
    return json.dumps(do_request(method, path, data=data), ensure_ascii=False)


@mcp.tool()
def login_test_user() -> str:
    """按当前项目配置的登录方式登录被测系统，建立会话。"""
    return json.dumps(login_seed_user(), ensure_ascii=False)


@mcp.tool()
def reset_http_session() -> str:
    """清除 HTTP 会话 Cookie，回到未登录状态（用于测试未登录场景）。"""
    reset_session()
    return "会话已重置"


@mcp.tool()
def get_sut_info() -> str:
    """获取当前被测项目信息：名称、地址、响应约定、登录方式、预置数据约定。"""
    profile = get_active_profile()
    return json.dumps({
        "name": profile["name"],
        "base_url": profile["base_url"],
        "assert_style": profile.get("assert_style"),
        "biz_conventions": profile.get("biz_conventions"),
        "login": profile.get("login"),
        "seed_notes": profile.get("seed_notes"),
    }, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()  # 默认 stdio 传输
