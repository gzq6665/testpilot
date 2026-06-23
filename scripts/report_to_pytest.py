# -*- coding: utf-8 -*-
"""把历史工作流报告（reports/report_*.json）中的用例转换为 pytest 回归脚本。

用法:
    python scripts/report_to_pytest.py                 # 转换最新一份报告
    python scripts/report_to_pytest.py <报告json路径>   # 转换指定报告
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from config import REPORTS_DIR
from tools.pytest_gen import generate_pytest_file

if len(sys.argv) > 1:
    report_path = Path(sys.argv[1])
else:
    candidates = sorted(REPORTS_DIR.glob("report_*.json"))
    if not candidates:
        sys.exit("reports/ 下没有报告文件，请先运行多Agent工作流")
    report_path = candidates[-1]

data = json.loads(report_path.read_text(encoding="utf-8"))
cases = data.get("cases", [])
if not cases:
    sys.exit(f"{report_path.name} 中没有用例")

path = generate_pytest_file(cases, data.get("module", "module"))
print(f"已从 {report_path.name} 导出 {len(cases)} 条用例")
print(f"pytest 脚本: {path}")
print(f"运行: pytest \"{path}\" -v")
