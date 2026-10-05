#!/usr/bin/env python3
"""
Rigorous secret scanner for Kalyan AI Personality Venture.
Scans the codebase for exposed credentials, live API keys, and sensitive tokens.
"""

import os
import re
import sys
from pathlib import Path

# Sensitive regex signatures
SECRET_PATTERNS = [
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("OpenAI API Key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b")),
    ("Anthropic API Key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{32,}\b")),
    ("Google / Gemini API Key", re.compile(r"\bAIza[0-9A-Za-z-_]{35}\b")),
    ("GitHub Personal Access Token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b")),
    ("Generic Private Key", re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----")),
    ("Hardcoded Live Secret String", re.compile(r"""(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*['"][a-zA-Z0-9_\-]{24,}['"]""", re.IGNORECASE)),
]

IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", ".pytest_cache", "__pycache__", "dist", "build"}
IGNORE_EXTS = {".png", ".jpg", ".jpeg", ".ico", ".svg", ".lock", ".db", ".sqlite", ".sqlite3", ".pyc"}
IGNORE_FILES = {".env.example"}

def scan_repo(root_path: Path):
    findings = []
    files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Exclude ignored dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext in IGNORE_EXTS or fname in IGNORE_FILES:
                continue

            file_path = Path(dirpath) / fname
            files_scanned += 1

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    for line_num, line in enumerate(f, 1):
                        # Skip comment lines that document placeholders
                        if "REPLACE_WITH" in line or "dummy" in line or "placeholder" in line:
                            continue
                        for pattern_name, regex in SECRET_PATTERNS:
                            matches = regex.findall(line)
                            if matches:
                                findings.append({
                                    "file": str(file_path.relative_to(root_path)),
                                    "line": line_num,
                                    "type": pattern_name,
                                    "match_excerpt": line.strip()[:100]
                                })
            except Exception as e:
                findings.append({
                    "file": str(file_path.relative_to(root_path)),
                    "line": 0,
                    "type": "ReadError",
                    "match_excerpt": str(e)
                })

    return files_scanned, findings

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    print(f"[*] Starting Secret Scan across repository: {repo_root}")
    scanned_count, issues = scan_repo(repo_root)
    print(f"[*] Files Scanned: {scanned_count}")
    
    if issues:
        print(f"[!] POTENTIAL SECRETS DETECTED: {len(issues)}")
        for item in issues:
            print(f"  - {item['file']}:{item['line']} [{item['type']}] -> {item['match_excerpt']}")
        sys.exit(1)
    else:
        print("[+] SUCCESS: Zero secrets, hardcoded API keys, or private credentials found in repository.")
        sys.exit(0)
