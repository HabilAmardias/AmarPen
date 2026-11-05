from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "codeql-results")
    files = list(root.rglob("*.sarif"))
    if not files:
        print(f"No SARIF files found under {root}")
        return 1
    blocking = []
    for path in files:
        try:
            sarif = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"Invalid SARIF file {path}: {exc}")
            return 1
        for run in sarif.get("runs", []):
            for result in run.get("results", []):
                rule_id = result.get("ruleId", "unknown-rule")
                message = result.get("message", {}).get("text", "")
                properties = result.get("properties", {})
                raw = properties.get("security-severity", "0")
                try:
                    severity = float(raw)
                except (TypeError, ValueError):
                    severity = 0.0
                if severity >= 7.0:
                    blocking.append((severity, rule_id, message, str(path)))
    if blocking:
        print("CodeQL HIGH/CRITICAL findings found:")
        for severity, rule_id, message, path in blocking:
            print(f"  [{severity:.1f}] {rule_id}: {message} ({path})")
        return 1
    print(f"CodeQL gate passed: no HIGH/CRITICAL findings in {len(files)} SARIF file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
