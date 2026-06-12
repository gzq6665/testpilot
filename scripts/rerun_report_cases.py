# -*- coding: utf-8 -*-
"""用当前 Profile 配置重新执行历史报告中的用例（用于配置修复后的复测）。

用法: python scripts/rerun_report_cases.py <报告json路径>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from agents.executor import execute_cases
from profiles import get_active_profile

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
profile = get_active_profile()
print(f"被测项目: {profile['name']} | body_format={profile.get('body_format')} "
      f"| assert_style={profile.get('assert_style')}")
print(f"复测用例: {len(report['cases'])} 条（模块: {report['module']}）\n")

results = execute_cases(report["cases"])
ok = sum(1 for r in results if r["passed"])
for r in results:
    mark = "PASS" if r["passed"] else "FAIL"
    print(f"  [{mark}] {r['case_id']} {r['title']} - {r['reason']}")
    if not r["passed"]:
        print(f"         响应: {json.dumps(r.get('response'), ensure_ascii=False)[:150]}")
print(f"\n复测结果: {ok}/{len(results)} 通过")
