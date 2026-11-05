from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "artifacts" / "backend-coverage.json"
STATEMENT_FLOOR = 80.0
BRANCH_FLOOR = 60.0


def main() -> int:
    report_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REPORT
    if not report_path.exists():
        print(f"Coverage report not found: {report_path}")
        return 1
    report = json.loads(report_path.read_text())
    totals = report["totals"]
    statements = totals["num_statements"]
    covered_lines = totals["covered_lines"]
    branches = totals["num_branches"]
    covered_branches = totals["covered_branches"]
    statement_percent = (covered_lines / statements * 100) if statements else 100.0
    branch_percent = (covered_branches / branches * 100) if branches else 100.0
    print(f"Backend statements: {statement_percent:.2f}% ({covered_lines}/{statements})")
    print(f"Backend branches:   {branch_percent:.2f}% ({covered_branches}/{branches})")
    failures = []
    if statement_percent < STATEMENT_FLOOR:
        failures.append(f"Statement coverage below {STATEMENT_FLOOR:.0f}%")
    if branch_percent < BRANCH_FLOOR:
        failures.append(f"Branch coverage below {BRANCH_FLOOR:.0f}%")
    if failures:
        print("\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
