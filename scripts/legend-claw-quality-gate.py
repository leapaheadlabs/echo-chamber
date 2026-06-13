#!/usr/bin/env python3
"""Shared local and CI quality gate for target repos.

Pure-Python logic only — no subprocess imports.
External scanner execution is handled by legend-claw-gate.sh.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
from pathlib import Path

TEXT_EXTENSIONS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".cpp",
    ".cc",
    ".cxx",
    ".c",
    ".h",
    ".hpp",
    ".dart",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".env",
    ".sql",
}
IAC_PATTERNS = ("*.tf", "*.tfvars", "*.hcl", "*.yaml", "*.yml")
TYPE_ESCAPE_RE = re.compile(r"as any|@ts-ignore|@ts-nocheck|@ts-expect-error")
TODO_RE = re.compile(r"TODO|FIXME|HACK|XXX")
SECRET_RE = re.compile(
    r"(password|secret|token|api_key|apikey|credential|private_key|client_secret)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
    re.IGNORECASE,
)

SECRET_FALSE_POSITIVES = {
    "echo_test_password",
    "plain_txt",
    "tst_pw",
    "db_key",
    "sec_val",
    "k3y",
    "test_secret_key_do_not_use_in_prod",
}

LANGUAGE_PATTERNS = {
    ".ts": [re.compile(r"console\.(log|debug|warn|info)|debugger")],
    ".tsx": [re.compile(r"console\.(log|debug|warn|info)|debugger")],
    ".js": [re.compile(r"console\.(log|debug|warn|info)|debugger")],
    ".jsx": [re.compile(r"console\.(log|debug|warn|info)|debugger")],
    ".py": [
        re.compile(r"^\s*print\(", re.MULTILINE),
        re.compile(r"import pdb|breakpoint\(\)|pdb\.set_trace"),
    ],
    ".go": [re.compile(r"fmt\.Print|log\.Print|runtime\.Breakpoint")],
    ".rs": [re.compile(r"println!\(|dbg!\(|eprintln!\(")],
    ".java": [re.compile(r"System\.out\.print|System\.err\.print|\.printStackTrace\(\)")],
    ".kt": [re.compile(r"println\(|System\.out\.print|System\.err\.print")],
    ".cpp": [re.compile(r"std::cout\s*<<|printf\s*\(|std::cerr\s*<<")],
    ".cc": [re.compile(r"std::cout\s*<<|printf\s*\(|std::cerr\s*<<")],
    ".cxx": [re.compile(r"std::cout\s*<<|printf\s*\(|std::cerr\s*<<")],
    ".c": [re.compile(r"printf\s*\(")],
    ".dart": [re.compile(r"print\(|debugPrint\(|developer\.log")],
}

COVERAGE_THRESHOLD = float(os.getenv("LEGEND_CLAW_COVERAGE_THRESHOLD", "80"))
ENFORCE_COVERAGE = os.getenv("LEGEND_CLAW_ENFORCE_COVERAGE", "1") != "0"
ONLY_COVERAGE = os.getenv("LEGEND_CLAW_ONLY_COVERAGE", "0") == "1"
TEST_SURFACE_MARKERS = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "pubspec.yaml",
)
TEST_DIRECTORY_MARKERS = ("tests", "test", "__tests__")
IGNORED_COVERAGE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
}
DIRECT_COVERAGE_FILES = (
    "coverage/coverage-summary.json",
    "coverage/lcov.info",
    "coverage.xml",
    "lcov.info",
    "coverage.out",
    "target/site/jacoco/jacoco.xml",
)
RECURSIVE_COVERAGE_PATTERNS = (
    "**/coverage-summary.json",
    "**/lcov.info",
    "**/coverage.xml",
    "**/coverage.out",
    "**/jacoco.xml",
)


def has_test_surface(root: Path) -> bool:
    if any((root / marker).exists() for marker in TEST_SURFACE_MARKERS):
        return True
    return any((root / marker).exists() for marker in TEST_DIRECTORY_MARKERS)


def is_ignored_coverage_path(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in IGNORED_COVERAGE_DIRS for part in relative.parts)


def discover_coverage_reports(root: Path) -> list[Path]:
    reports: list[Path] = []
    seen: set[Path] = set()

    for relative in DIRECT_COVERAGE_FILES:
        path = root / relative
        if path.is_file() and not is_ignored_coverage_path(root, path):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                reports.append(path)

    for pattern in RECURSIVE_COVERAGE_PATTERNS:
        for path in root.glob(pattern):
            if not path.is_file() or is_ignored_coverage_path(root, path):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            reports.append(path)

    return reports


def parse_json_coverage(path: Path) -> float | None:
    with path.open() as handle:
        data = json.load(handle)
    total = data.get("total", {})
    for key in ("lines", "statements"):
        value = total.get(key, {}).get("pct")
        if isinstance(value, (int, float)):
            return float(value)
    return None


def parse_lcov_coverage(path: Path) -> float | None:
    lines_found = 0
    lines_hit = 0
    with path.open() as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line.startswith("LF:"):
                lines_found += int(line[3:])
            elif line.startswith("LH:"):
                lines_hit += int(line[3:])
    if lines_found == 0:
        return None
    return (lines_hit / lines_found) * 100.0


def parse_go_coverage(path: Path) -> float | None:
    total_statements = 0
    covered_statements = 0
    with path.open() as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("mode:"):
                continue
            parts = line.split()
            if len(parts) != 3:
                continue
            statement_count = int(parts[1])
            hit_count = int(parts[2])
            total_statements += statement_count
            if hit_count > 0:
                covered_statements += statement_count
    if total_statements == 0:
        return None
    return (covered_statements / total_statements) * 100.0


def parse_xml_coverage(path: Path) -> float | None:
    content = path.read_text(errors="ignore")

    line_rate_match = re.search(r'line-rate="([0-9.]+)"', content)
    if line_rate_match:
        return float(line_rate_match.group(1)) * 100.0

    counters = re.findall(
        r'<counter[^>]*type="LINE"[^>]*covered="(\d+)"[^>]*missed="(\d+)"',
        content,
    )
    if not counters:
        counters = re.findall(
            r'<counter[^>]*type="LINE"[^>]*missed="(\d+)"[^>]*covered="(\d+)"',
            content,
        )
        if counters:
            covered = sum(int(c[1]) for c in counters)
            missed = sum(int(c[0]) for c in counters)
            total = covered + missed
            if total == 0:
                return None
            return (covered / total) * 100.0

    if counters:
        covered = sum(int(c[0]) for c in counters)
        missed = sum(int(c[1]) for c in counters)
        total = covered + missed
        if total == 0:
            return None
        return (covered / total) * 100.0

    return None


def parse_coverage_percentage(path: Path) -> float | None:
    if path.name.endswith("coverage-summary.json"):
        return parse_json_coverage(path)
    if path.name == "lcov.info":
        return parse_lcov_coverage(path)
    if path.name == "coverage.out":
        return parse_go_coverage(path)
    if path.suffix == ".xml":
        return parse_xml_coverage(path)
    return None


def evaluate_coverage(root: Path) -> list[str]:
    if not ENFORCE_COVERAGE or not has_test_surface(root):
        return []

    reports = discover_coverage_reports(root)
    if not reports:
        return [
            "coverage gate failed: no coverage report found; expected coverage-summary.json, lcov.info, coverage.xml, coverage.out, or jacoco.xml"
        ]

    measured: list[tuple[str, float]] = []
    unparseable: list[str] = []
    for report in reports:
        percentage = parse_coverage_percentage(report)
        relative = report.relative_to(root).as_posix()
        if percentage is None:
            unparseable.append(relative)
            continue
        measured.append((relative, percentage))

    if not measured:
        return [
            "coverage gate failed: found coverage artifacts but could not parse any percentage from "
            + ", ".join(unparseable[:10])
        ]

    return [
        f"coverage below threshold: {name} at {value:.2f}% (required {COVERAGE_THRESHOLD:.2f}%)"
        for name, value in measured
        if value < COVERAGE_THRESHOLD
    ]


def repo_root() -> Path:
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError("Not inside a git repo")


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {
        "Dockerfile",
        ".env",
        ".env.example",
    }


def scan_changed_files(root: Path, changed_files: list[str]) -> list[str]:
    failures: list[str] = []
    for rel_path in changed_files:
        path = root / rel_path
        if not path.exists() or not path.is_file() or not is_text_file(path):
            continue

        try:
            content = path.read_text(errors="ignore")
        except OSError as exc:
            failures.append(f"{rel_path}: failed to read file: {exc}")
            continue

        for pattern in LANGUAGE_PATTERNS.get(path.suffix.lower(), []):
            if pattern.search(content):
                failures.append(f"{rel_path}: debug artifact matched {pattern.pattern}")

        if TYPE_ESCAPE_RE.search(content):
            failures.append(f"{rel_path}: type safety escape found")

        if path.suffix.lower() == ".py" and re.search(r"except\s*:", content):
            failures.append(f"{rel_path}: bare except clause found")

        if TODO_RE.search(content):
            for match in TODO_RE.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                line_text = content.splitlines()[line - 1]
                if "(#" not in line_text:
                    failures.append(f"{rel_path}:{line}: TODO/FIXME/HACK/XXX without linked issue")

        if SECRET_RE.search(content):
            match = SECRET_RE.search(content)
            if match:
                value = match.group(0)
                if not any(fp in value for fp in SECRET_FALSE_POSITIVES):
                    failures.append(f"{rel_path}: potential hardcoded secret found")
    return failures


def path_matches(patterns: list[str], path: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def require_tools(stage: str, changed_files: list[str]) -> list[str]:
    if stage not in {"pre-push", "pre-pr"}:
        return []

    required = ["semgrep", "gitleaks", "trunk"]
    if any(fnmatch.fnmatch(path, pattern) for path in changed_files for pattern in IAC_PATTERNS):
        required.append("checkov")

    missing = [tool for tool in required if shutil.which(tool) is None]
    return [f"missing required tool: {tool}" for tool in missing]


def main() -> int:
    parser = argparse.ArgumentParser(description="Legend Claw shared local and CI gate")
    parser.add_argument("--stage", choices=["pre-commit", "pre-push", "pre-pr"], default="pre-pr")
    parser.add_argument("--base-ref", default="origin/main")
    args = parser.parse_args()

    root = repo_root()

    if ONLY_COVERAGE:
        failures = evaluate_coverage(root)
        if failures:
            print("Legend Claw coverage gate: FAIL")
            for failure in failures:
                print(f"- {failure}")
            return 1
        print("Legend Claw coverage gate: PASS")
        return 0

    changed_files: list[str] = []
    gate_script = Path(__file__).resolve().relative_to(root).as_posix()
    for rel_path in sorted(root.rglob("*")):
        if not rel_path.is_file():
            continue
        rel = rel_path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        rel_str = rel.as_posix()
        if rel_str == gate_script:
            continue
        changed_files.append(rel_str)

    if not changed_files:
        print("Legend Claw gate: no changed files")
        return 0

    failures: list[str] = []
    failures.extend(scan_changed_files(root, changed_files))
    failures.extend(evaluate_coverage(root))
    failures.extend(require_tools(args.stage, changed_files))

    if failures:
        print("Legend Claw gate: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Legend Claw gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
