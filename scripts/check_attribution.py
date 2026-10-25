"""Kiểm tra mọi commit chỉ mang tên thành viên nhóm (CONTRIBUTING.md mục 6).

Tác giả, người commit và mọi dòng `Co-authored-by` phải có email nằm trong
`.github/allowed-identities.txt`. Mô tả PR không được chứa dòng `Co-authored-by` lạ
hay dòng quảng cáo "Generated with ...".

    python scripts/check_attribution.py <base-ref> [<head-ref>]   # kiểm các commit base..head
    PR_BODY="..." python scripts/check_attribution.py <base-ref>     # kiểm thêm mô tả PR
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_FILE = ROOT / ".github" / "allowed-identities.txt"
CO_AUTHOR = re.compile(r"^\s*co-authored-by:\s*(.*?)\s*<([^>]+)>\s*$", re.IGNORECASE | re.MULTILINE)
# Dòng quảng cáo do công cụ tự thêm: cụm "Generated with/by" ở đầu dòng (có thể có biểu tượng phía trước).
PROMO = re.compile(r"^[^\w\n]*generated (with|by)\b", re.IGNORECASE | re.MULTILINE)


def allowed_emails() -> set[str]:
    lines = ALLOWED_FILE.read_text(encoding="utf-8").splitlines()
    return {s.strip().lower() for s in lines if s.strip() and not s.lstrip().startswith("#")}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout.decode("utf-8", "replace")


def check_text(text: str, allowed: set[str], where: str) -> list[str]:
    problems = [f"{where}: Co-authored-by {name} <{email}> không phải thành viên nhóm"
                for name, email in CO_AUTHOR.findall(text) if email.lower() not in allowed]
    m = PROMO.search(text)
    if m:
        problems.append(f"{where}: có dòng {m.group(0)!r}")
    return problems


def main() -> int:
    base = sys.argv[1]
    head = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    allowed = allowed_emails()
    problems: list[str] = []
    log = git("log", "--format=%H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%B%x1e", f"{base}..{head}")
    for record in filter(None, (r.strip() for r in log.split("\x1e"))):
        sha, an, ae, cn, ce, message = record.split("\x1f", 5)
        if ae.lower() not in allowed:
            problems.append(f"commit {sha[:7]}: tác giả {an} <{ae}> không có trong danh sách")
        if ce.lower() not in allowed:
            problems.append(f"commit {sha[:7]}: người commit {cn} <{ce}> không có trong danh sách")
        problems += check_text(message, allowed, f"commit {sha[:7]}")
    problems += check_text(os.environ.get("PR_BODY", ""), allowed, "mô tả PR")

    if problems:
        print("Commit hoặc PR mang tên người ngoài nhóm (CONTRIBUTING.md mục 6):")
        for p in problems:
            print(f"  - {p}")
        print("Sửa: đặt đúng git config user.name/user.email; xóa dòng Co-authored-by lạ "
              "(git commit --amend hoặc git rebase -i) rồi push lại; sửa mô tả PR.")
        return 1
    print(f"OK: mọi commit trong {base}..{head} chỉ mang tên thành viên nhóm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
