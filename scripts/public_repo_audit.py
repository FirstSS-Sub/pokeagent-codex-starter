#!/usr/bin/env python3
"""Audit tracked files for public-repository hygiene.

The check intentionally focuses on high-confidence issues:

- tracked local-only artifact paths,
- likely local absolute paths,
- machine/user identifiers that should not appear in this starter,
- common credential/token formats,
- unexpectedly large tracked files.

It does not inspect ignored local working directories such as cache/, runs/,
data/, or local_submissions/ because those are intentionally private.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


MAX_TRACKED_FILE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class Finding:
    path: str
    line: int | None
    reason: str


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    return result.stdout.decode("utf-8", errors="replace")


def repo_root() -> Path:
    return Path(run_git("rev-parse", "--show-toplevel").strip())


def tracked_files() -> list[str]:
    raw = run_git("ls-files", "-z")
    return [item for item in raw.split("\0") if item]


def is_probably_text(path: Path) -> bool:
    chunk = path.read_bytes()[:4096]
    return b"\0" not in chunk


def normalized_non_comment(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("#"):
        stripped = stripped[1:].strip()
    return stripped


def content_patterns() -> list[tuple[str, re.Pattern[str]]]:
    slash = "/"
    local_user = "s109" + "74"
    private_namespace = "github-" + "applibot"
    return [
        (
            "macOS absolute home path",
            re.compile(re.escape(slash + "Users" + slash) + r"[A-Za-z0-9._-]+"),
        ),
        (
            "Linux absolute home path",
            re.compile(re.escape(slash + "home" + slash) + r"[A-Za-z0-9._-]+"),
        ),
        (
            "private temp/cache path",
            re.compile(re.escape(slash + "private" + slash) + r"(?:tmp|var)" + re.escape(slash)),
        ),
        ("local machine/user identifier", re.compile(r"\b" + re.escape(local_user) + r"\b")),
        ("private company namespace", re.compile(re.escape(private_namespace), re.IGNORECASE)),
        (
            "OpenAI-style secret key",
            re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
        ),
        (
            "GitHub token",
            re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
        ),
        ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        (
            "private key block",
            re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
        ),
        (
            "Kaggle key assignment with non-placeholder value",
            re.compile(r"\bKAGGLE_KEY\s*=\s*(?!optional\b|replace\b|redacted\b|<|\s*$)[^\s#]+", re.IGNORECASE),
        ),
        (
            "generic credential assignment with non-placeholder value",
            re.compile(
                r"\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*"
                r"['\"]?(?!optional\b|replace\b|example\b|dummy\b|redacted\b|xxx\b|<|\s*$)"
                r"[A-Za-z0-9_./+=-]{12,}",
                re.IGNORECASE,
            ),
        ),
    ]


def blocked_path_patterns() -> list[tuple[str, re.Pattern[str]]]:
    return [
        ("competition data directory is tracked", re.compile(r"(^|/)data/")),
        ("cache directory is tracked", re.compile(r"(^|/)cache/")),
        ("run output directory is tracked", re.compile(r"(^|/)runs/")),
        ("local submission directory is tracked", re.compile(r"(^|/)local_submissions/")),
        ("environment file is tracked", re.compile(r"(^|/)\.env($|[.])")),
        ("Kaggle credential file is tracked", re.compile(r"(^|/)kaggle\.json$")),
        ("archive/package artifact is tracked", re.compile(r"\.(?:tar|tar\.gz|tgz|zip)$")),
        ("raw replay/log artifact is tracked", re.compile(r"\.(?:jsonl|log)$")),
    ]


def audit(root: Path, files: list[str], max_bytes: int) -> list[Finding]:
    findings: list[Finding] = []
    path_rules = blocked_path_patterns()
    content_rules = content_patterns()

    for rel in files:
        for reason, pattern in path_rules:
            if pattern.search(rel) and rel != ".env.example":
                findings.append(Finding(rel, None, reason))

        path = root / rel
        try:
            size = path.stat().st_size
        except OSError as exc:
            findings.append(Finding(rel, None, f"cannot stat tracked file: {exc}"))
            continue

        if size > max_bytes:
            findings.append(Finding(rel, None, f"tracked file exceeds {max_bytes} bytes"))

        if not is_probably_text(path):
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(rel, None, f"cannot read tracked file: {exc}"))
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            check_line = normalized_non_comment(line)
            if not check_line:
                continue
            for reason, pattern in content_rules:
                if pattern.search(check_line):
                    findings.append(Finding(rel, line_no, reason))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=MAX_TRACKED_FILE_BYTES,
        help="maximum expected size for a tracked file",
    )
    args = parser.parse_args()

    root = repo_root()
    files = tracked_files()
    findings = audit(root, files, args.max_bytes)

    if findings:
        print("Public repository audit failed:", file=sys.stderr)
        for finding in findings:
            loc = finding.path if finding.line is None else f"{finding.path}:{finding.line}"
            print(f"- {loc}: {finding.reason}", file=sys.stderr)
        print(
            "\nFix or remove these tracked files before pushing to a public repository.",
            file=sys.stderr,
        )
        return 1

    print(f"OK public repository audit passed: {len(files)} tracked files scanned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
