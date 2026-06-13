#!/usr/bin/env python3
"""Shared local and CI quality gate for target repos."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path
from typing import Any


DEFAULT_CONTRACTS: dict[str, Any] = {
    "version": 1,
    "boundedChangeSet": {"maxFiles": 8, "maxLines": 400},
    "requiredCommands": [],
    "pathContracts": [],
}

TEXT_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".kt",
    ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".dart", ".json", ".yaml",
    ".yml", ".toml", ".sh", ".env", ".sql",
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
    ".py": [re.compile(r"^\s*print\(", re.MULTILINE), re.compile(r"import pdb|breakpoint\(\)|pdb\.set_trace")],
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
TRUNK_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / ".trunk" / "trunk.yaml"
TRUNK_FORMATTER_ONLY_CLASS = "ISSUE_CLASS_UNFORMATTED"


def run(
    cmd: list[str],
    cwd: Path,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def run_shell(
    command: str,
    cwd: Path,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", "-lc", command], cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


@contextmanager
def canonical_trunk_config(root: Path):
    trunk_cfg = root / ".trunk" / "trunk.yaml"
    if not TRUNK_TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"Bundled Trunk template is missing: {TRUNK_TEMPLATE_PATH}")
    canonical = TRUNK_TEMPLATE_PATH.read_bytes()
    trunk_dir = trunk_cfg.parent
    dir_existed = trunk_dir.exists()
    file_existed = trunk_cfg.exists()
    original = trunk_cfg.read_bytes() if file_existed else None
    wrote_config = original != canonical

    if wrote_config:
        trunk_dir.mkdir(parents=True, exist_ok=True)
        trunk_cfg.write_bytes(canonical)

    try:
        yield trunk_cfg
    finally:
        if not wrote_config:
            return
        if file_existed and original is not None:
            trunk_cfg.write_bytes(original)
        else:
            try:
                trunk_cfg.unlink()
            except FileNotFoundError:
                pass
            if not dir_existed:
                try:
                    trunk_dir.rmdir()
                except OSError:
                    pass


def load_trunk_payload(raw_output: str) -> dict[str, Any]:
    text = raw_output.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for line in reversed(text.splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"trunk produced non-JSON output: {text[:300]}")


def run_trunk_check(root: Path, trunk_files: list[str]) -> list[str]:
    if not trunk_files:
        return []

    env = {**os.environ, "CI": "true", "TRUNK_TOKEN": "", "NO_COLOR": "1"}

    with canonical_trunk_config(root):
        result = run(
            ["trunk", "check", "--no-fix", "--output", "json", "--no-progress", *trunk_files],
            cwd=root,
            timeout=300,
            env=env,
        )

    if result.returncode >= 2:
        details = (result.stdout + result.stderr).strip()[:2000]
        return [f"trunk check failed to execute\n{details}"]

    try:
        payload = load_trunk_payload(result.stdout)
    except ValueError as exc:
        return [f"trunk check failed\n{exc}"]

    issues = [
        item
        for item in payload.get("issues", [])
        if item.get("issueClass") != TRUNK_FORMATTER_ONLY_CLASS
    ]
    if not issues:
        return []

    summaries = []
    for item in issues[:20]:
        location = item.get("file", "?")
        line = int(item.get("line", 0) or 0)
        if line:
            location = f"{location}:{line}"
        summaries.append(f"{location} [{item.get('linter', '?')}] {item.get('message', '').strip()}")
    if len(issues) > 20:
        summaries.append(f"... {len(issues) - 20} more trunk issue(s)")

    return ["trunk check failed\n" + "\n".join(summaries)]


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
    root = ET.parse(path).getroot()

    line_rate = root.attrib.get("line-rate")
    if line_rate is not None:
        return float(line_rate) * 100.0

    counters = root.findall(".//counter[@type='LINE']")
    if counters:
        covered = 0
        missed = 0
        for counter in counters:
            covered += int(counter.attrib.get("covered", "0"))
            missed += int(counter.attrib.get("missed", "0"))
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

    failures = [
        f"coverage below threshold: {name} at {value:.2f}% (required {COVERAGE_THRESHOLD:.2f}%)"
        for name, value in measured
        if value < COVERAGE_THRESHOLD
    ]

    return failures


def repo_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"], cwd=Path.cwd())
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Not inside a git repo")
    return Path(result.stdout.strip())


def load_contracts(root: Path) -> dict[str, Any]:
    contract_path = root / ".legendclaw" / "contracts.json"
    if not contract_path.exists():
        return DEFAULT_CONTRACTS.copy()
    with contract_path.open() as handle:
        data = json.load(handle)
    merged = DEFAULT_CONTRACTS.copy()
    merged.update(data)
    return merged


def resolve_base_ref_for_git(root: Path, base_ref: str | None) -> str:
    resolved_base = (base_ref or "origin/main").strip() or "origin/main"
    if resolved_base.startswith(("origin/", "refs/")):
        branch_name = resolved_base.removeprefix("origin/")
        if branch_name != resolved_base:
            run(["git", "fetch", "origin", branch_name, "--depth=100"], cwd=root)
        return resolved_base
    if all(ch in "0123456789abcdef" for ch in resolved_base.lower()) and 7 <= len(resolved_base) <= 40:
        return resolved_base
    run(["git", "fetch", "origin", resolved_base, "--depth=100"], cwd=root)
    return f"origin/{resolved_base}"


def get_changed_files(root: Path, stage: str, base_ref: str | None, base_sha: str | None, head_sha: str | None) -> list[str]:
    if stage == "pre-commit":
        result = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"], cwd=root)
    elif base_sha and head_sha:
        result = run(["git", "diff", "--name-only", "--diff-filter=ACMRT", base_sha, head_sha], cwd=root)
    else:
        resolved_base = resolve_base_ref_for_git(root, base_ref)
        result = run(["git", "diff", "--name-only", "--diff-filter=ACMRT", f"{resolved_base}...HEAD"], cwd=root)
        if result.returncode not in (0, 1) and "no merge base" in result.stderr.lower():
            result = run(["git", "diff", "--name-only", "--diff-filter=ACMRT", resolved_base, "HEAD"], cwd=root)

    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "Failed to compute changed files")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_shortstat(root: Path, stage: str, base_ref: str | None, base_sha: str | None, head_sha: str | None) -> str:
    if stage == "pre-commit":
        result = run(["git", "diff", "--cached", "--shortstat"], cwd=root)
    elif base_sha and head_sha:
        result = run(["git", "diff", "--shortstat", base_sha, head_sha], cwd=root)
    else:
        resolved_base = resolve_base_ref_for_git(root, base_ref)
        result = run(["git", "diff", "--shortstat", f"{resolved_base}...HEAD"], cwd=root)
        if result.returncode not in (0, 1) and "no merge base" in result.stderr.lower():
            result = run(["git", "diff", "--shortstat", resolved_base, "HEAD"], cwd=root)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "Failed to compute diff stats")
    return result.stdout.strip()


def parse_shortstat(shortstat: str) -> tuple[int, int]:
    files = 0
    lines = 0
    file_match = re.search(r"(\d+) files? changed", shortstat)
    if file_match:
        files = int(file_match.group(1))
    insertions = re.search(r"(\d+) insertions?\(\+\)", shortstat)
    deletions = re.search(r"(\d+) deletions?\(-\)", shortstat)
    if insertions:
        lines += int(insertions.group(1))
    if deletions:
        lines += int(deletions.group(1))
    return files, lines


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"Dockerfile", ".env", ".env.example"}


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


def run_contract_commands(root: Path, contracts: dict[str, Any], changed_files: list[str]) -> list[str]:
    failures: list[str] = []

    for item in contracts.get("requiredCommands", []):
        name = item.get("name", "unnamed-command")
        command = (item.get("run") or "").strip()
        when_paths = item.get("whenPaths", [])
        if when_paths and not any(path_matches(when_paths, path) for path in changed_files):
            continue
        if not command:
            failures.append(f"{name}: required command is blank in .legendclaw/contracts.json")
            continue
        result = run_shell(command, cwd=root)
        if result.returncode != 0:
            failures.append(f"{name}: command failed\n{(result.stdout + result.stderr).strip()[:2000]}")

    for item in contracts.get("pathContracts", []):
        when_paths = item.get("whenPaths", [])
        if not when_paths or not any(path_matches(when_paths, path) for path in changed_files):
            continue
        name = item.get("name", "unnamed-path-contract")
        command = (item.get("run") or "").strip()
        if not command:
            failures.append(f"{name}: matching path requires an executable contract but run is blank")
            continue
        result = run_shell(command, cwd=root)
        if result.returncode != 0:
            failures.append(f"{name}: command failed\n{(result.stdout + result.stderr).strip()[:2000]}")

    return failures


def require_tools(stage: str, changed_files: list[str]) -> list[str]:
    if stage not in {"pre-push", "pre-pr"}:
        return []

    required = ["semgrep", "gitleaks", "trunk"]
    if any(fnmatch.fnmatch(path, pattern) for path in changed_files for pattern in IAC_PATTERNS):
        required.append("checkov")

    missing = [tool for tool in required if shutil.which(tool) is None]
    return [f"missing required tool: {tool}" for tool in missing]


def run_external_scanners(root: Path, stage: str, changed_files: list[str]) -> list[str]:
    if stage not in {"pre-push", "pre-pr"}:
        return []

    failures: list[str] = []

    semgrep = run(
        [
            "semgrep",
            "--config=auto",
            "--config=p/security-audit",
            "--config=p/secrets",
            "--config=p/owasp-top-ten",
            "--error",
            "--exclude=scripts",
            ".",
        ],
        cwd=root,
        timeout=300,
    )
    if semgrep.returncode != 0:
        failures.append(f"semgrep failed\n{(semgrep.stdout + semgrep.stderr).strip()[:2000]}")

    gitleaks = run(
        ["gitleaks", "detect", "--source", ".", "--no-banner", "--exit-code", "1"],
        cwd=root,
        timeout=180,
    )
    if gitleaks.returncode not in (0, 1):
        failures.append(f"gitleaks failed to execute\n{(gitleaks.stdout + gitleaks.stderr).strip()[:2000]}")
    elif gitleaks.returncode == 1:
        failures.append(f"gitleaks detected secrets\n{(gitleaks.stdout + gitleaks.stderr).strip()[:2000]}")

    trunk_files = [path for path in changed_files if (root / path).is_file()]
    failures.extend(run_trunk_check(root, trunk_files))

    if any(fnmatch.fnmatch(path, pattern) for path in changed_files for pattern in IAC_PATTERNS):
        checkov = run(["checkov", "-d", ".", "--quiet", "--compact"], cwd=root, timeout=240)
        if checkov.returncode != 0:
            failures.append(f"checkov failed\n{(checkov.stdout + checkov.stderr).strip()[:2000]}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Legend Claw shared local and CI gate")
    parser.add_argument("--stage", choices=["pre-commit", "pre-push", "pre-pr"], required=True)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
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

    contracts = load_contracts(root)
    changed_files = get_changed_files(root, args.stage, args.base_ref, args.base_sha, args.head_sha)
    if not changed_files:
        print("Legend Claw gate: no changed files")
        return 0

    failures: list[str] = []

    if args.stage in {"pre-push", "pre-pr"}:
        shortstat = get_shortstat(root, args.stage, args.base_ref, args.base_sha, args.head_sha)
        file_count, line_count = parse_shortstat(shortstat)
        budget = contracts.get("boundedChangeSet", {})
        max_files = int(budget.get("maxFiles", 8))
        max_lines = int(budget.get("maxLines", 400))
        if file_count > max_files:
            failures.append(f"bounded change set exceeded: {file_count} files changed (max {max_files})")
        if line_count > max_lines:
            failures.append(f"bounded change set exceeded: {line_count} lines changed (max {max_lines})")

    failures.extend(scan_changed_files(root, changed_files))
    failures.extend(run_contract_commands(root, contracts, changed_files))
    failures.extend(evaluate_coverage(root))
    failures.extend(require_tools(args.stage, changed_files))
    failures.extend(run_external_scanners(root, args.stage, changed_files))

    if failures:
        print("Legend Claw gate: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Legend Claw gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
