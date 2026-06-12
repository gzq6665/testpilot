# -*- coding: utf-8 -*-
"""被测系统配置档案（Profile）管理。

每个被测系统一份 JSON 配置（data/profiles/<id>.json），核心字段：
- base_url        被测系统地址
- assert_style    断言风格：biz_status（HTTP恒200，业务码在JSON status字段）
                  或 http_status（直接用 HTTP 状态码表达业务结果）
- biz_conventions 响应/调用约定（注入生成与执行 Agent 的 Prompt）
- login           登录接口配置 {path, method, params}，用于"需要登录"前置条件
- seed_notes      测试环境预置数据约定（账号、固定验证码、数据隔离规则等）

平台所有业务相关组件（用例生成 Prompt、执行器、ReAct Agent、pytest 模板、
RAG 知识库目录与索引）均从"当前激活的 Profile"动态读取，
实现一套平台可配置接入任意被测系统。每个 Profile 拥有独立的文档目录
data/docs/<id>/ 与向量索引，互不污染。
"""
import json
import re
import shutil

from config import DOCS_DIR, PROJECT_ROOT, VECTOR_STORE_DIR

PROFILES_DIR = PROJECT_ROOT / "data" / "profiles"
_ACTIVE_FILE = PROFILES_DIR / "_active.txt"

DEFAULT_PROFILE = {
    "id": "heima_p2p",
    "name": "黑马理财系统",
    "base_url": "http://127.0.0.1:9999",
    "assert_style": "biz_status",
    "body_format": "form",
    "biz_conventions": (
        "除验证码图片接口为 GET 外，业务接口均为 POST（Content-Type: "
        "application/x-www-form-urlencoded）；HTTP 状态码恒为 200，"
        "业务结果在响应 JSON 的 status 字段（200=成功，100=业务校验失败，250=未登录）"
    ),
    "login": {
        "path": "/member/public/login",
        "method": "POST",
        "params": {"keywords": "13800000001", "password": "Test@123"},
    },
    "seed_notes": (
        "预置用户 13800000001/Test@123（已实名认证）；图片验证码固定 8888，"
        "短信验证码固定 123456；注册类用例必须使用 13899990001 起依次递增的新手机号"
        "（每条用例不同，防止前面注册成功导致后面\"手机已存在\"），"
        "仅\"手机已存在\"场景使用预置手机号 13800000001"
    ),
}

STATUS_HINTS = {
    "biz_status": "expected_biz_status 填预期的业务状态码（响应 JSON 中 status 字段的值）",
    "http_status": "expected_biz_status 填预期的 HTTP 状态码（如 200、400、401、404）",
}


def profile_docs_dir(pid: str):
    d = DOCS_DIR / pid
    d.mkdir(parents=True, exist_ok=True)
    return d


def _migrate_loose_docs() -> None:
    """把 data/docs 根目录下的散落文档归入默认 Profile 的子目录（一次性迁移）。"""
    target = profile_docs_dir(DEFAULT_PROFILE["id"])
    for p in DOCS_DIR.iterdir():
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ".pdf"):
            p.rename(target / p.name)


def ensure_init() -> None:
    """首次使用时创建默认 Profile 并迁移文档。"""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    if not list(PROFILES_DIR.glob("*.json")):
        save_profile(DEFAULT_PROFILE)
        set_active(DEFAULT_PROFILE["id"])
    _migrate_loose_docs()


def save_profile(profile: dict) -> dict:
    """保存（新建或更新）Profile，自动生成 id 与文档目录。"""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    if not profile.get("id"):
        slug = re.sub(r"[^\w]+", "_", profile.get("name", "project")).strip("_").lower()
        profile["id"] = slug or "project"
    profile.setdefault("assert_style", "biz_status")
    profile.setdefault("body_format", "form")
    profile.setdefault("biz_conventions", "")
    profile.setdefault("seed_notes", "")
    (PROFILES_DIR / f"{profile['id']}.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    profile_docs_dir(profile["id"])
    return profile


def list_profiles() -> list[dict]:
    ensure_init()
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(PROFILES_DIR.glob("*.json"))]


def get_profile(pid: str) -> dict | None:
    path = PROFILES_DIR / f"{pid}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def get_active_id() -> str:
    ensure_init()
    if _ACTIVE_FILE.exists():
        # utf-8-sig: 兼容带 BOM 的文件（如被外部编辑器/PowerShell 写入过）
        pid = _ACTIVE_FILE.read_text(encoding="utf-8-sig").strip()
        if (PROFILES_DIR / f"{pid}.json").exists():
            return pid
    return list_profiles()[0]["id"]


def get_active_profile() -> dict:
    return get_profile(get_active_id())


def set_active(pid: str) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    _ACTIVE_FILE.write_text(pid, encoding="utf-8")


def delete_profile(pid: str) -> None:
    """删除项目及其知识库文档、向量索引。至少保留一个项目；
    删除的是当前激活项目时，自动切换到剩余的第一个项目。"""
    profiles = list_profiles()
    if len(profiles) <= 1:
        raise ValueError("平台至少需要保留一个项目，不能删除最后一个")
    if not (PROFILES_DIR / f"{pid}.json").exists():
        raise ValueError(f"项目 [{pid}] 不存在")

    (PROFILES_DIR / f"{pid}.json").unlink()
    shutil.rmtree(DOCS_DIR / pid, ignore_errors=True)          # 该项目的知识库文档
    (VECTOR_STORE_DIR / f"{pid}.pkl").unlink(missing_ok=True)  # 该项目的向量索引

    # 清理运行中的索引内存缓存，防止同名项目重建后读到旧索引
    from rag import vectorstore
    vectorstore._cache.pop(pid, None)

    # 归一化激活标记：若删除的是当前激活项目，get_active_id 会自动回退到剩余的第一个
    set_active(get_active_id())
