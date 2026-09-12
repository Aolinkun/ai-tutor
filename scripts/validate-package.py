#!/usr/bin/env python3
"""校验真实资源和执行回归测试；不把场景清单数量冒充行为测试。"""

import json
from pathlib import Path
import re
import subprocess
import sys

from tutorlib import VERSION, TutorError, fail, read_json, validate_sources, validate_state

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = ["SKILL.md", "agents/openai.yaml", "scripts/tutor.py", "scripts/tutorlib.py",
                "references/资料与来源_sources.md",
                "assets/templates/source.json", "tests/test_runtime.py", "tests/行为场景_eval-cases.json"]
    for relative in required:
        if not (ROOT / relative).is_file():
            raise TutorError(f"缺少资源：{relative}")
    fail(validate_state(read_json(ROOT / "assets/templates/state.json"), []))
    fail(validate_sources([read_json(ROOT / "assets/templates/source.json")], "new-course"))
    for path in [ROOT / "SKILL.md", *sorted((ROOT / "references").glob("*.md"))]:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            if not (path.parent / target.split("#")[0]).is_file():
                raise TutorError(f"引用失效：{path.name} → {target}")
    run = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-p", "test_*.py", "-v"],
                         cwd=ROOT, text=True, capture_output=True)
    print(run.stderr, end="")
    if run.returncode:
        raise TutorError("运行时回归未通过")
    scenarios = read_json(ROOT / "tests/行为场景_eval-cases.json")
    print(json.dumps({"status": "valid", "version": VERSION, "scenario_specs": len(scenarios),
                      "note": "上方 unittest 是本次已执行检查；行为场景清单需另行实际执行，不能据数量宣称全通过"}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (TutorError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        sys.exit(1)
