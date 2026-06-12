# -*- coding: utf-8 -*-
"""删除项目功能验证：创建→删除→文件清理→激活回退→最后一个不可删。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from config import DOCS_DIR, VECTOR_STORE_DIR
from profiles import (PROFILES_DIR, delete_profile, get_active_id,
                      list_profiles, profile_docs_dir, save_profile, set_active)

print("当前项目列表:", [p["id"] for p in list_profiles()])

# 1. 创建临时项目并切换激活
tmp = save_profile({"name": "临时待删项目", "base_url": "http://127.0.0.1:1234"})
(profile_docs_dir(tmp["id"]) / "tmp.md").write_text("# 临时文档", encoding="utf-8")
(VECTOR_STORE_DIR / f"{tmp['id']}.pkl").write_bytes(b"fake-index")
set_active(tmp["id"])
assert get_active_id() == tmp["id"]
print(f"已创建并激活临时项目: {tmp['id']}")

# 2. 删除它，验证文件清理与激活回退
delete_profile(tmp["id"])
assert not (PROFILES_DIR / f"{tmp['id']}.json").exists(), "配置未删除"
assert not (DOCS_DIR / tmp["id"]).exists(), "文档目录未删除"
assert not (VECTOR_STORE_DIR / f"{tmp['id']}.pkl").exists(), "向量索引未删除"
assert get_active_id() != tmp["id"], "激活项目未回退"
print(f"删除成功，配置/文档/索引均已清理，激活项目回退为: {get_active_id()}")

# 3. 删到只剩一个时应拒绝
remaining = [p["id"] for p in list_profiles()]
print("剩余项目:", remaining)
if len(remaining) == 1:
    try:
        delete_profile(remaining[0])
        raise AssertionError("最后一个项目竟然被删除了！")
    except ValueError as e:
        print(f"最后一个项目删除被正确拒绝: {e}")
else:
    print("（剩余多于一个项目，跳过最后一个的保护测试）")

print("\n删除功能验证全部通过 ✔")
