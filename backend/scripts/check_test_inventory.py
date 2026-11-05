from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USECASES = ROOT / "src" / "pentest_platform" / "usecases"
CONTROLLERS = ROOT / "src" / "pentest_platform" / "controllers"
USECASE_TESTS = ROOT / "tests" / "unit" / "usecases"
CONTROLLER_TESTS = ROOT / "tests" / "unit" / "controllers"

SKIP = {"__init__.py", "base.py", "common.py", "deps.py", "schemas.py"}


def expected_mappings() -> dict[Path, Path]:
    mapping: dict[Path, Path] = {}
    overrides = {
        "agent_runtime.py": "test_agents.py",
        "agent_scheduler.py": "test_agents.py",
    }
    for source in sorted(USECASES.glob("*.py")):
        if source.name in SKIP:
            continue
        mapping[source] = USECASE_TESTS / overrides.get(source.name, f"test_{source.stem}.py")
    for source in sorted(CONTROLLERS.glob("*.py")):
        if source.name in SKIP:
            continue
        mapping[source] = CONTROLLER_TESTS / f"test_{source.stem}_controller.py"
    return mapping


def main() -> int:
    mapping = expected_mappings()
    failures = []
    for source, test_file in mapping.items():
        if not test_file.exists():
            failures.append(f"Missing test file for {source.relative_to(ROOT)}: {test_file.relative_to(ROOT)}")
            continue
        if not re.search(r"\bdef test_", test_file.read_text()):
            failures.append(f"No test functions found in {test_file.relative_to(ROOT)}")

    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", str(ROOT / "tests" / "unit")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if collected.returncode not in {0, 5}:
        failures.append("pytest could not collect the backend unit tests")
    collected_text = collected.stdout
    for source, test_file in mapping.items():
        relative = str(test_file.relative_to(ROOT))
        if relative not in collected_text:
            failures.append(f"Test file is not collected by pytest: {relative} (for {source.relative_to(ROOT)})")

    if failures:
        print("\n".join(failures))
        return 1
    print(f"Backend test inventory OK: {len(mapping)} usecases/controllers mapped to collected tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
