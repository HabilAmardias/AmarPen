from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "pentest_platform"

FORBIDDEN = {
    "domain": {
        "pentest_platform.db",
        "pentest_platform.repositories",
        "pentest_platform.usecases",
        "pentest_platform.controllers",
        "pentest_platform.adapters",
        "pentest_platform.bootstrap",
        "pentest_platform.workers",
        "fastapi",
        "sqlalchemy",
    },
    "ports": {
        "pentest_platform.db",
        "pentest_platform.repositories",
        "pentest_platform.usecases",
        "pentest_platform.controllers",
        "pentest_platform.adapters",
        "pentest_platform.bootstrap",
        "pentest_platform.workers",
        "fastapi",
        "sqlalchemy",
    },
    "usecases": {
        "pentest_platform.db",
        "pentest_platform.repositories",
        "pentest_platform.controllers",
        "pentest_platform.adapters",
        "pentest_platform.bootstrap",
        "pentest_platform.workers",
        "fastapi",
        "sqlalchemy",
    },
    "controllers": {
        "pentest_platform.db",
        "pentest_platform.repositories",
        "pentest_platform.adapters",
        "pentest_platform.workers",
        "sqlalchemy",
    },
    "repositories": {
        "pentest_platform.usecases",
        "pentest_platform.controllers",
        "pentest_platform.adapters",
        "pentest_platform.bootstrap",
        "pentest_platform.workers",
        "fastapi",
    },
    "adapters": {
        "pentest_platform.usecases",
        "pentest_platform.controllers",
        "pentest_platform.bootstrap",
        "pentest_platform.workers",
    },
}

ALLOWED_CONTROLLER_DEPS = {"deps.py"}


def imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def main() -> int:
    violations = []
    for path in sorted(ROOT.rglob("*.py")):
        layer = path.relative_to(ROOT).parts[0]
        if layer not in FORBIDDEN:
            continue
        if layer == "controllers" and path.name in ALLOWED_CONTROLLER_DEPS:
            continue
        for imported in imports_of(path):
            for forbidden in FORBIDDEN[layer]:
                if imported == forbidden or imported.startswith(f"{forbidden}."):
                    violations.append(f"{path.relative_to(ROOT)} imports {imported} (forbidden for {layer})")
    if violations:
        print("\n".join(violations))
        return 1
    print("Architecture check OK: layer boundaries are respected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
