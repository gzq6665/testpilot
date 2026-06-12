# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
print("模块:", d["module"])
print("用例数:", len(d["cases"]))
print("评审:", d["review"].get("score"), "passed=", d["review"].get("passed"))
for c in d["cases"]:
    print(f"  [{c.get('case_type')}] {c['case_id']} {c['title']} -> {c.get('method')} {c['api_path']}")
    print(f"      参数: {json.dumps(c.get('params'), ensure_ascii=False)}")
    print(f"      期望: status={c.get('expected_biz_status')} 关键字={c.get('expected_keyword')!r} 前置={c.get('precondition')!r}")
ok = sum(1 for r in d["results"] if r["passed"])
print(f"执行: {ok}/{len(d['results'])} 通过")
for r in d["results"]:
    if not r["passed"]:
        print(f"  [FAIL] {r['case_id']} {r['reason']} 响应={json.dumps(r.get('response'), ensure_ascii=False)[:120]}")
