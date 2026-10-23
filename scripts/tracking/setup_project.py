"""Tạo GitHub Project cho SaiGo và đồng bộ các trường từ issue có nhãn `task`.

Trường: Status (Todo / In Progress / In Review / Blocked / Done), Hours, Start, Due, Week.
Giá trị Hours/Start/Due/Week lấy từ docs/TASKS.md và docs/tracking/schedule.csv.

    python scripts/tracking/setup_project.py           # tạo project nếu chưa có, thêm và cập nhật item
    python scripts/tracking/setup_project.py --sync    # chỉ cập nhật item (không đụng Status của item đã có)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_backlog import REPO, existing_task_issues, load_schedule, parse_tasks  # noqa: E402

OWNER = "NeitLN"
TITLE = "SaiGo — Delivery Plan"
DESCRIPTION = "Backlog SaiGo (Nhóm 4, Introduction to AI). Mỗi item là một task trong docs/TASKS.md; issue đóng qua PR có 'Closes #n'."
README = f"""## SaiGo — Delivery Plan

Mỗi item là một task trong [docs/TASKS.md](https://github.com/{REPO}/blob/main/docs/TASKS.md).

- **Status:** Todo → In Progress (đã tạo branch) → In Review (đã mở PR) → Done (PR đã merge, issue đóng). Blocked: đang chờ task khác.
- **Hours:** giờ ước lượng, dùng cho burndown.
- **Week:** tuần đến hạn (tuần bắt đầu thứ Hai).
- Burndown cập nhật mỗi ngày ở issue có nhãn `tracking`.
- Quy trình: [CONTRIBUTING.md](https://github.com/{REPO}/blob/main/CONTRIBUTING.md).
"""

STATUS_OPTIONS = [
    ("Todo", "GRAY", "Chưa bắt đầu"),
    ("In Progress", "YELLOW", "Đang làm trên branch"),
    ("In Review", "BLUE", "Đã mở PR, chờ review"),
    ("Blocked", "RED", "Đang chờ task khác hoặc bị lỗi chặn"),
    ("Done", "GREEN", "PR đã merge, issue đóng"),
]

# Tuần bắt đầu thứ Hai.
WEEKS = [
    ("Tuần 1 · 19–25/10", date(2026, 10, 19), date(2026, 10, 25)),
    ("Tuần 2 · 26/10–01/11", date(2026, 10, 26), date(2026, 11, 1)),
    ("Tuần 3 · 02–08/11", date(2026, 11, 2), date(2026, 11, 8)),
    ("Tuần 4 · 09–15/11", date(2026, 11, 9), date(2026, 11, 15)),
    ("Tuần 5 · 16–22/11", date(2026, 11, 16), date(2026, 11, 22)),
]


def run(cmd: list[str], payload: str | None = None) -> str:
    res = subprocess.run(cmd, input=payload.encode("utf-8") if payload else None, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}… failed: {res.stderr.decode('utf-8', 'replace').strip()}")
    return res.stdout.decode("utf-8")


def graphql(query: str, **variables) -> dict:
    body = json.dumps({"query": query, "variables": variables}, ensure_ascii=False)
    out = json.loads(run(["gh", "api", "graphql", "--input", "-"], body))
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def week_of(d: date) -> str:
    for name, start, end in WEEKS:
        if start <= d <= end:
            return name
    raise ValueError(f"ngày {d} nằm ngoài các tuần đã định nghĩa")


def find_project() -> dict | None:
    data = graphql("""query($login:String!){ user(login:$login){ projectsV2(first:50){ nodes{ id number title } } } }""",
                   login=OWNER)
    for p in data["user"]["projectsV2"]["nodes"]:
        if p["title"] == TITLE:
            return p
    return None


def create_project() -> dict:
    owner_id = graphql("query($login:String!){ user(login:$login){ id } }", login=OWNER)["user"]["id"]
    repo_id = graphql("query($o:String!,$n:String!){ repository(owner:$o,name:$n){ id } }",
                      o=REPO.split("/")[0], n=REPO.split("/")[1])["repository"]["id"]
    p = graphql("""mutation($owner:ID!,$title:String!,$repo:ID!){
        createProjectV2(input:{ownerId:$owner,title:$title,repositoryId:$repo}){ projectV2{ id number title } } }""",
                owner=owner_id, title=TITLE, repo=repo_id)["createProjectV2"]["projectV2"]
    graphql("""mutation($id:ID!,$d:String!,$r:String!){
        updateProjectV2(input:{projectId:$id,shortDescription:$d,readme:$r,public:true}){ projectV2{ id } } }""",
            id=p["id"], d=DESCRIPTION, r=README)
    print(f"project + #{p['number']} {TITLE}")
    return p


def fields(project_id: str) -> dict[str, dict]:
    data = graphql("""query($id:ID!){ node(id:$id){ ... on ProjectV2 { fields(first:50){ nodes{
        ... on ProjectV2FieldCommon { id name dataType }
        ... on ProjectV2SingleSelectField { id name dataType options { id name } } } } } } }""", id=project_id)
    return {f["name"]: f for f in data["node"]["fields"]["nodes"]}


def ensure_fields(project_id: str) -> dict[str, dict]:
    have = fields(project_id)
    status = have["Status"]
    if [o["name"] for o in status["options"]] != [o[0] for o in STATUS_OPTIONS]:
        graphql("""mutation($f:ID!,$opts:[ProjectV2SingleSelectFieldOptionInput!]!){
            updateProjectV2Field(input:{fieldId:$f,singleSelectOptions:$opts}){ projectV2Field{ ... on ProjectV2SingleSelectField { id } } } }""",
                f=status["id"], opts=[{"name": n, "color": c, "description": d} for n, c, d in STATUS_OPTIONS])
    for name, dtype in (("Hours", "NUMBER"), ("Start", "DATE"), ("Due", "DATE")):
        if name not in have:
            graphql("""mutation($p:ID!,$n:String!,$t:ProjectV2CustomFieldType!){
                createProjectV2Field(input:{projectId:$p,dataType:$t,name:$n}){ projectV2Field{ ... on ProjectV2FieldCommon { id } } } }""",
                    p=project_id, n=name, t=dtype)
    if "Week" not in have:
        graphql("""mutation($p:ID!,$opts:[ProjectV2SingleSelectFieldOptionInput!]!){
            createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:"Week",singleSelectOptions:$opts}){
              projectV2Field{ ... on ProjectV2FieldCommon { id } } } }""",
                p=project_id, opts=[{"name": n, "color": "GRAY", "description": ""} for n, _, _ in WEEKS])
    return fields(project_id)


def project_items(project_id: str) -> dict[str, dict]:
    """issue node id → {item_id, status}"""
    items, cursor = {}, None
    while True:
        data = graphql("""query($id:ID!,$after:String){ node(id:$id){ ... on ProjectV2 { items(first:100,after:$after){
            pageInfo{ hasNextPage endCursor }
            nodes{ id content{ ... on Issue { id } }
                   fieldValueByName(name:"Status"){ ... on ProjectV2ItemFieldSingleSelectValue { name } } } } } } }""",
                       id=project_id, after=cursor)
        page = data["node"]["items"]
        for n in page["nodes"]:
            if n["content"]:
                items[n["content"]["id"]] = {"item_id": n["id"], "status": (n["fieldValueByName"] or {}).get("name")}
        if not page["pageInfo"]["hasNextPage"]:
            return items
        cursor = page["pageInfo"]["endCursor"]


def set_value(project_id: str, item_id: str, field_id: str, value: dict) -> None:
    graphql("""mutation($p:ID!,$i:ID!,$f:ID!,$v:ProjectV2FieldValue!){
        updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:$v}){ projectV2Item{ id } } }""",
            p=project_id, i=item_id, f=field_id, v=value)


def option_id(field: dict, name: str) -> str:
    return next(o["id"] for o in field["options"] if o["name"] == name)


def main(sync_only: bool) -> None:
    project = find_project()
    if project is None:
        if sync_only:
            sys.exit("chưa có project; chạy không kèm --sync trước")
        project = create_project()
    pid = project["id"]
    f = ensure_fields(pid)
    tasks = {t["id"]: t for t in parse_tasks()}
    sched = load_schedule()
    issues = existing_task_issues()
    items = project_items(pid)

    for tid, issue in sorted(issues.items(), key=lambda kv: kv[1]["number"]):
        if tid not in tasks:
            continue
        s = sched[tid]
        if issue["node_id"] in items:
            item = items[issue["node_id"]]
        else:
            item_id = graphql("""mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p,contentId:$c}){ item{ id } } }""",
                              p=pid, c=issue["node_id"])["addProjectV2ItemById"]["item"]["id"]
            item = {"item_id": item_id, "status": None}
        iid = item["item_id"]
        set_value(pid, iid, f["Hours"]["id"], {"number": tasks[tid]["hours"]})
        set_value(pid, iid, f["Start"]["id"], {"date": s["start"]})
        set_value(pid, iid, f["Due"]["id"], {"date": s["due"]})
        set_value(pid, iid, f["Week"]["id"], {"singleSelectOptionId": option_id(f["Week"], week_of(date.fromisoformat(s["due"])))})
        if item["status"] is None:
            status = "Done" if issue["state"] == "closed" else "Todo"
            set_value(pid, iid, f["Status"]["id"], {"singleSelectOptionId": option_id(f["Status"], status)})
        print(f"item #{issue['number']} {tid}")
    print(f"https://github.com/users/{OWNER}/projects/{project['number']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sync", action="store_true")
    main(ap.parse_args().sync)
