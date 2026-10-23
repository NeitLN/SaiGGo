"""Burndown và báo cáo tiến độ SaiGo, tính từ dữ liệu thật trên GitHub.

Nguồn: issue có nhãn `task` (ước lượng giờ nằm trong mục "Ước lượng (giờ)" của issue),
pull request và review của repo. Không có số nào nhập tay.

Cách tính:
- Phạm vi ngày d = tổng giờ của task đã được tạo trước hết ngày d.
- Còn lại ngày d = tổng giờ của task đã tạo nhưng chưa đóng tại hết ngày d.
  Task đóng với lý do "not planned" được tính là cắt phạm vi, không tính là hoàn thành.
- Đường lý tưởng: từ phạm vi ngày bắt đầu giảm đều về 0 vào ngày final ready.
- Giờ của task nhiều người phụ trách được chia đều cho các người đó.

    python scripts/tracking/burndown.py --out build/tracking            # xuất PNG, CSV, REPORT.md
    python scripts/tracking/burndown.py --out build/tracking --update-issue
    python scripts/tracking/burndown.py --out build/tracking --weekly-comment

Token: biến môi trường GITHUB_TOKEN, nếu không có thì dùng `gh auth token`.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "NeitLN/SaiGGo")
VN = timezone(timedelta(hours=7))  # Việt Nam không có giờ mùa hè
START = date(2026, 10, 23)          # ngày lập backlog
END = date(2026, 11, 12)            # final ready (Project_Intructions_261.pdf)
WEEKS = [
    ("Tuần 1 · 19–25/10", date(2026, 10, 19), date(2026, 10, 25)),
    ("Tuần 2 · 26/10–01/11", date(2026, 10, 26), date(2026, 11, 1)),
    ("Tuần 3 · 02–08/11", date(2026, 11, 2), date(2026, 11, 8)),
    ("Tuần 4 · 09–15/11", date(2026, 11, 9), date(2026, 11, 15)),
    ("Tuần 5 · 16–22/11", date(2026, 11, 16), date(2026, 11, 22)),
]
NAMES = {"NeitLN": "Tiến", "anh7032": "Duy Anh", "Jayson135724": "Minh", "dobaovlu": "Bảo"}
IMAGE_URL = f"https://raw.githubusercontent.com/{REPO}/tracking/burndown.png"


# ---------- GitHub API ----------

def token() -> str:
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def api(path: str, method: str = "GET", payload: dict | None = None):
    req = urllib.request.Request(
        f"https://api.github.com/{path}", method=method,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={"Authorization": f"Bearer {token()}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req) as res:
        body = res.read()
    return json.loads(body) if body else None


def paged(path: str) -> list:
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        batch = api(f"{path}{sep}per_page=100&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def vn_date(ts: str | None) -> date | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(VN).date()


# ---------- dữ liệu ----------

def section(body: str, heading: str) -> str:
    m = re.search(rf"###\s*{re.escape(heading)}\s*\n(.*?)(?=\n###\s|\Z)", body or "", re.S)
    return m.group(1).strip() if m else ""


def load_tasks() -> list[dict]:
    tasks = []
    for i in paged(f"repos/{REPO}/issues?state=all&labels=task"):
        if "pull_request" in i:
            continue
        est = section(i["body"], "Ước lượng (giờ)").replace(",", ".")
        try:
            hours = float(est.split()[0])
        except (ValueError, IndexError):
            hours = 0.0
        owners = re.findall(r"@([A-Za-z0-9-]+)", section(i["body"], "Người phụ trách"))
        owners = owners or [a["login"] for a in i["assignees"]]
        closed = vn_date(i["closed_at"])
        tasks.append({
            "number": i["number"], "title": i["title"], "hours": hours, "owners": owners,
            "created": vn_date(i["created_at"]), "closed": closed,
            "cut": i["state"] == "closed" and i.get("state_reason") == "not_planned",
            "milestone": (i["milestone"] or {}).get("title", ""),
            "due": section(i["body"], "Thời gian dự kiến").split("→")[-1].strip(),
        })
    return tasks


def load_prs() -> list[dict]:
    prs = []
    for p in paged(f"repos/{REPO}/pulls?state=all"):
        reviews = paged(f"repos/{REPO}/pulls/{p['number']}/reviews")
        prs.append({
            "number": p["number"], "author": p["user"]["login"], "merged": vn_date(p["merged_at"]),
            "reviews": [(r["user"]["login"], vn_date(r["submitted_at"])) for r in reviews
                        if r["user"] and r["user"]["login"] != p["user"]["login"]],
        })
    return prs


# ---------- tính toán ----------

def series(tasks: list[dict], today: date) -> list[dict]:
    last = max(END, today)
    scope0 = sum(t["hours"] for t in tasks if t["created"] <= START)
    span = (END - START).days
    rows = []
    d = START
    while d <= last:
        scope = sum(t["hours"] for t in tasks if t["created"] <= d)
        remaining = sum(t["hours"] for t in tasks if t["created"] <= d and not (t["closed"] and t["closed"] <= d))
        done = sum(t["hours"] for t in tasks if t["closed"] and t["closed"] <= d and not t["cut"])
        ideal = max(0.0, scope0 * (1 - (d - START).days / span)) if d <= END else 0.0
        rows.append({"date": d.isoformat(), "scope_h": scope, "remaining_h": remaining if d <= today else None,
                     "done_h": done if d <= today else None, "ideal_h": round(ideal, 2)})
        d += timedelta(days=1)
    return rows


def week_stats(tasks: list[dict], prs: list[dict], today: date) -> list[dict]:
    out = []
    for name, ws, we in WEEKS:
        if ws > max(today, END):
            continue
        end = min(we, today)
        planned = 0.0
        for t in tasks:
            try:
                due = datetime.strptime(t["due"], "%d/%m/%Y").date()
            except ValueError:
                continue
            if ws <= due <= we:
                planned += t["hours"]
        done = [t for t in tasks if t["closed"] and ws <= t["closed"] <= we and not t["cut"]]
        remaining = sum(t["hours"] for t in tasks if t["created"] <= end and not (t["closed"] and t["closed"] <= end))
        out.append({
            "week": name, "planned_h": planned, "done_h": sum(t["hours"] for t in done), "done_n": len(done),
            "remaining_h": remaining if ws <= today else None,
            "prs_merged": sum(1 for p in prs if p["merged"] and ws <= p["merged"] <= we),
            "reviews": sum(1 for p in prs for _, d in p["reviews"] if d and ws <= d <= we),
        })
    return out


def member_stats(tasks: list[dict], prs: list[dict]) -> list[dict]:
    agg = defaultdict(lambda: {"assigned_h": 0.0, "done_h": 0.0, "done_n": 0, "open_n": 0, "prs": 0, "reviews": 0})
    for t in tasks:
        if t["cut"] or not t["owners"]:
            continue
        share = t["hours"] / len(t["owners"])
        for o in t["owners"]:
            agg[o]["assigned_h"] += share
            if t["closed"]:
                agg[o]["done_h"] += share
                agg[o]["done_n"] += 1
            else:
                agg[o]["open_n"] += 1
    for p in prs:
        if p["merged"]:
            agg[p["author"]]["prs"] += 1
        for reviewer, _ in p["reviews"]:
            agg[reviewer]["reviews"] += 1
    return [{"login": k, "name": NAMES.get(k, k), **v} for k, v in sorted(agg.items(), key=lambda kv: NAMES.get(kv[0], kv[0]))]


# ---------- xuất ----------

def plot(rows: list[dict], path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    xs = [date.fromisoformat(r["date"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=120)
    ax.plot(xs, [r["ideal_h"] for r in rows], "--", color="#888", label="Lý tưởng")
    ax.step(xs, [r["scope_h"] for r in rows], where="post", color="#c8a", alpha=0.6, label="Phạm vi (tổng giờ)")
    actual = [(x, r["remaining_h"]) for x, r in zip(xs, rows) if r["remaining_h"] is not None]
    if actual:
        ax.plot(*zip(*actual), marker="o", color="#d9480f", label="Còn lại (thực tế)")
    for _, ws, _ in WEEKS:
        if xs[0] <= ws <= xs[-1]:
            ax.axvline(ws, color="#ddd", lw=0.8, zorder=0)
    ax.axvline(date(2026, 11, 5), color="#1c7ed6", lw=1, ls=":", label="Cổng G1 (05/11)")
    ax.set_title("SaiGo — Burndown theo giờ ước lượng")
    ax.set_ylabel("Giờ còn lại")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", fontsize=8)
    from matplotlib.dates import DateFormatter, DayLocator
    ax.xaxis.set_major_locator(DayLocator(interval=2))
    ax.xaxis.set_major_formatter(DateFormatter("%d/%m"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return True


def fmt(h) -> str:
    return "—" if h is None else f"{h:g}"


def report(rows, weeks, members, tasks, today: date, now: datetime, image_version: str) -> str:
    cur = next(r for r in rows if r["date"] == today.isoformat()) if START <= today else rows[0]
    total = sum(t["hours"] for t in tasks if not t["cut"])
    done_h = sum(t["hours"] for t in tasks if t["closed"] and not t["cut"])
    open_n = sum(1 for t in tasks if not t["closed"])
    cut_h = sum(t["hours"] for t in tasks if t["cut"])
    gap = (cur["remaining_h"] or 0) - cur["ideal_h"]
    recent = sorted((t for t in tasks if t["closed"] and (today - t["closed"]).days < 7),
                    key=lambda t: t["closed"], reverse=True)

    lines = [
        "## 📉 Burndown SaiGo",
        "",
        f"_Tự động cập nhật {now:%H:%M %d/%m/%Y} (giờ VN) bởi workflow `tracking.yml`. "
        "Số liệu tính từ trạng thái issue/PR thật trên GitHub, không nhập tay. "
        "Cách tính ở đầu file `scripts/tracking/burndown.py`._",
        "",
        f"![Burndown]({IMAGE_URL}?v={image_version})",
        "",
        f"- **Phạm vi:** {total:g} giờ ước lượng, {len(tasks)} task"
        + (f" (đã cắt {cut_h:g} giờ)" if cut_h else ""),
        f"- **Đã xong:** {done_h:g} giờ · **Còn lại:** {fmt(cur['remaining_h'])} giờ, {open_n} task mở",
        f"- **Đường lý tưởng hôm nay:** {cur['ideal_h']:g} giờ → "
        + ("đúng kế hoạch" if abs(gap) < 0.5
           else f"**chậm** hơn kế hoạch {gap:.1f} giờ" if gap > 0
           else f"nhanh hơn kế hoạch {-gap:.1f} giờ"),
        f"- Mốc: cổng G1 05/11 · final ready {END:%d/%m} · thuyết trình 19/11 · nộp 22/11",
        "",
        "### Theo tuần",
        "",
        "| Tuần | Giờ đến hạn | Giờ hoàn thành | Task xong | Còn lại cuối tuần | PR merge | Review |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for w in weeks:
        lines.append(f"| {w['week']} | {w['planned_h']:g} | {w['done_h']:g} | {w['done_n']} | {fmt(w['remaining_h'])} | {w['prs_merged']} | {w['reviews']} |")
    lines += [
        "",
        "### Theo thành viên",
        "",
        "| Thành viên | Giờ được giao | Giờ đã xong | Task xong | Task mở | PR đã merge | Review cho người khác |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for m in members:
        lines.append(f"| {m['name']} (@{m['login']}) | {m['assigned_h']:.1f} | {m['done_h']:.1f} | {m['done_n']} | {m['open_n']} | {m['prs']} | {m['reviews']} |")
    lines += ["", "### Hoàn thành 7 ngày qua", ""]
    lines += [f"- {t['closed']:%d/%m} · #{t['number']} {t['title']} ({t['hours']:g} h)" for t in recent] or ["- Chưa có"]
    lines += ["", f"Dữ liệu từng ngày: [`burndown.csv`](https://github.com/{REPO}/blob/tracking/burndown.csv) trên branch `tracking`."]
    return "\n".join(lines) + "\n"


def weekly_comment(weeks, today: date) -> str | None:
    done_weeks = [w for w in weeks if any(name == w["week"] and we < today for name, _, we in WEEKS)]
    if not done_weeks:
        return None
    w = done_weeks[-1]
    return (f"### Tổng kết {w['week']}\n\n"
            f"- Giờ đến hạn trong tuần: {w['planned_h']:g} · giờ hoàn thành: {w['done_h']:g} ({w['done_n']} task)\n"
            f"- Còn lại cuối tuần: {fmt(w['remaining_h'])} giờ\n"
            f"- PR đã merge: {w['prs_merged']} · review: {w['reviews']}\n\n"
            "_Tạo tự động bởi workflow `tracking.yml`._\n")


def tracking_issue() -> int:
    issues = paged(f"repos/{REPO}/issues?state=open&labels=tracking")
    if not issues:
        raise SystemExit("không tìm thấy issue mở có nhãn `tracking`")
    return issues[0]["number"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("build/tracking"))
    ap.add_argument("--update-issue", action="store_true", help="ghi REPORT.md vào issue có nhãn tracking")
    ap.add_argument("--weekly-comment", action="store_true", help="bình luận tổng kết tuần vừa qua vào issue tracking")
    ap.add_argument("--image-version", default=None, help="tham số chống cache ảnh (mặc định: thời điểm chạy)")
    a = ap.parse_args()

    now = datetime.now(VN)
    today = now.date()
    tasks, prs = load_tasks(), load_prs()
    rows = series(tasks, today)
    weeks = week_stats(tasks, prs, today)
    members = member_stats(tasks, prs)

    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / "burndown.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    has_png = plot(rows, a.out / "burndown.png")
    md = report(rows, weeks, members, tasks, today, now, a.image_version or now.strftime("%Y%m%d%H%M"))
    (a.out / "REPORT.md").write_text(md, encoding="utf-8")
    print(f"{len(tasks)} task, {len(prs)} PR → {a.out} (png: {has_png})")

    if a.update_issue:
        num = tracking_issue()
        api(f"repos/{REPO}/issues/{num}", "PATCH", {"body": md})
        print(f"đã cập nhật issue #{num}")
    if a.weekly_comment:
        body = weekly_comment(weeks, today)
        if body:
            num = tracking_issue()
            api(f"repos/{REPO}/issues/{num}/comments", "POST", {"body": body})
            print(f"đã bình luận tổng kết tuần vào #{num}")


if __name__ == "__main__":
    main()
