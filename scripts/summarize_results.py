"""Tổng hợp kết quả benchmark thành bảng Markdown (docs/EXPERIMENT_PLAN.md mục 3.2, 3.3, 9).

Cách dùng::

    python scripts/summarize_results.py <run_dir> [<run_dir> ...]

Đọc `measurements.csv` (27 cột mục 3.3), `env.json` và `config.json` của **mọi** thư mục rồi in ra
ba bảng mẫu mục 9: E2 (thuật toán × tầng), E3 (theo `|V|`), E4 (theo `scenario_id`). Chỉ in ra
stdout, **không** ghi vào `docs/EXPERIMENTS.md` (người dẫn số vào tài liệu ở T65).

`r = expanded_A* / expanded_D` và `s = t_D / t_A*` được tính **từng cặp** rồi mới lấy median và tứ
phân vị (mục 3.2), không lấy tỉ số của hai trung bình; `ms = runtime_ns_median / 1e6`. Gộp nhiều lần
chạy thì khoá ghép cặp luôn có `run_id` vì `query_id` chỉ duy nhất trong một lần chạy. Suite không
có dữ liệu thì bảng đó bị bỏ qua kèm lý do; số in theo dấu phẩy thập phân như văn phong tài liệu.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

# 27 cột chuẩn của measurements.csv theo docs/EXPERIMENT_PLAN.md mục 3.3
MEASUREMENT_COLUMNS = (
    "run_id", "suite", "dataset_id", "size_label", "n_nodes", "n_edges", "query_id", "workload",
    "stratum", "source", "target", "hav_m", "algo", "scenario_id", "blocked_count", "status",
    "cost_s", "distance_m", "expanded", "unique_expanded", "reopened", "relaxations", "pushes",
    "max_frontier", "runtime_ns_median", "runtime_ns_min", "repeats",
)
ALGO_ORDER = ("dijkstra", "astar")
ALGO_LABEL = {"dijkstra": "Dijkstra", "astar": "A*"}
SUITE_DEMO, SUITE_SCALING, SUITE_SCENARIO = "demo", "scaling", "scenario"
STRATUM_ORDER = ("ngan", "trung_binh", "dai")
STRATUM_LABEL = {"ngan": "ngắn (δ<0,2)", "trung_binh": "trung bình", "dai": "dài (δ≥0,5)"}
ALL_STRATA = "tất cả"
BASELINE = "baseline"
COST_TOL = 1e-6                       # dung sai khớp chi phí, mục 3.2
MISSING = "—"
USAGE = "cách dùng: python scripts/summarize_results.py <run_dir> [<run_dir> ...]"


@dataclass(frozen=True)
class Row:
    """Một dòng `measurements.csv` đã đọc số (một cặp × một thuật toán)."""

    run_id: str
    suite: str
    dataset_id: str
    size_label: str
    n_nodes: int
    n_edges: int
    query_id: str
    workload: str
    stratum: str
    source: int
    target: int
    algo: str
    scenario_id: str
    status: str
    cost_s: float | None
    expanded: int
    runtime_ms: float


@dataclass(frozen=True)
class RunMeta:
    """Thông tin môi trường của một thư mục kết quả (`env.json` + `config.json`)."""

    path: Path
    run_id: str
    python: str
    git_commit: str
    git_dirty: bool


@dataclass(frozen=True)
class Pair:
    """Một cặp truy vấn có đủ kết quả của cả Dijkstra và A*."""

    dijkstra: Row
    astar: Row

    @property
    def stratum(self) -> str:
        return self.dijkstra.stratum

    @property
    def scenario_id(self) -> str:
        return self.dijkstra.scenario_id

    @property
    def matched(self) -> bool:
        """Khớp chi phí theo mục 3.2: cùng trạng thái; cả hai `no_path` cũng là khớp."""
        first, second = self.dijkstra, self.astar
        if first.status != second.status:
            return False
        if first.status != "ok":
            return True
        if first.cost_s is None or second.cost_s is None:
            return False
        return abs(second.cost_s - first.cost_s) <= COST_TOL * max(1.0, first.cost_s)

    @property
    def ratio(self) -> float | None:
        """`r = expanded_A* / expanded_D`; cặp `expanded_D = 0` bị loại (mục 3.2)."""
        if self.dijkstra.expanded <= 0:
            return None
        return self.astar.expanded / self.dijkstra.expanded

    @property
    def speedup(self) -> float | None:
        """`s = t_D / t_A*` của đúng cặp này."""
        if self.astar.runtime_ms <= 0:
            return None
        return self.dijkstra.runtime_ms / self.astar.runtime_ms


def _cell(text: str) -> str:
    """Thoát dấu `|` để ô như `|V|` không làm vỡ bảng Markdown."""
    return text.replace("|", "\\|")


@dataclass(frozen=True)
class Table:
    """Một bảng Markdown kèm dòng công thức và ghi chú in ngay dưới bảng."""

    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    formulas: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_markdown(self) -> str:
        lines = ["| " + " | ".join(_cell(text) for text in self.headers) + " |",
                 "|" + "|".join("---" for _ in self.headers) + "|"]
        lines.extend("| " + " | ".join(_cell(text) for text in row) + " |" for row in self.rows)
        return "\n".join(lines)


@dataclass(frozen=True)
class Section:
    """Một bảng E2/E3/E4: có bảng kèm dòng nguồn, hoặc lý do bỏ qua."""

    title: str
    table: Table | None = None
    source: str = ""
    skipped: str = ""


# --- Đọc dữ liệu ---

def _number(path: Path, lineno: int, raw: dict[str, str], name: str) -> float:
    """Đọc một ô số; ô rỗng hoặc không phải số là lỗi dữ liệu, không im lặng bỏ qua."""
    try:
        return float(raw[name])
    except (TypeError, ValueError):
        raise ValueError(f"{path}:{lineno}: cột {name} = {raw[name]!r} không phải số") from None


def read_rows(run_dir: Path | str) -> list[Row]:
    """Đọc `measurements.csv` trong `run_dir`; thiếu file/cột hoặc ô số sai thì `ValueError`."""
    path = Path(run_dir) / "measurements.csv"
    if not path.is_file():
        raise FileNotFoundError(f"không thấy {path}")
    rows: list[Row] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in MEASUREMENT_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: thiếu cột {', '.join(missing)} (mục 3.3 EXPERIMENT_PLAN)")
        for lineno, raw in enumerate(reader, start=2):
            cost = raw["cost_s"].strip()
            rows.append(Row(
                run_id=(raw["run_id"] or "").strip(),
                suite=(raw["suite"] or "").strip().lower(),
                dataset_id=(raw["dataset_id"] or "").strip(),
                size_label=(raw["size_label"] or "").strip(),
                n_nodes=int(_number(path, lineno, raw, "n_nodes")),
                n_edges=int(_number(path, lineno, raw, "n_edges")),
                query_id=(raw["query_id"] or "").strip(),
                workload=(raw["workload"] or "").strip(),
                stratum=(raw["stratum"] or "").strip(),
                source=int(_number(path, lineno, raw, "source")),
                target=int(_number(path, lineno, raw, "target")),
                algo=(raw["algo"] or "").strip().lower(),
                scenario_id=(raw["scenario_id"] or "").strip(),
                status=(raw["status"] or "").strip(),
                cost_s=_number(path, lineno, raw, "cost_s") if cost else None,
                expanded=int(_number(path, lineno, raw, "expanded")),
                runtime_ms=_number(path, lineno, raw, "runtime_ns_median") / 1e6,
            ))
    return rows


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"không thấy {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError(f"{path}: JSON hỏng: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError(f"{path}: phải là object JSON")
    return data


def read_meta(run_dir: Path | str) -> RunMeta:
    """Đọc `env.json` + `config.json` của một lần chạy để ghi dòng nguồn."""
    run_dir = Path(run_dir)
    env = _read_json(run_dir / "env.json")
    config = _read_json(run_dir / "config.json")
    python = str(env.get("python_version") or "?").split()[0]
    return RunMeta(path=run_dir, run_id=str(config.get("run_id") or ""),
                   python=python, git_commit=str(env.get("git_commit") or "?"),
                   git_dirty=bool(env.get("git_dirty")))


# --- Ghép cặp và thống kê ---

def pair_stats(rows: Sequence[Row], key_fields: Sequence[str]) -> dict[tuple, Pair]:
    """Ghép hai dòng của cùng một cặp theo `key_fields`; thiếu một thuật toán thì bỏ cặp đó.

    `key_fields` **phải chứa `run_id`** khi gộp nhiều thư mục: `query_id` chỉ duy nhất trong một
    lần chạy, thiếu `run_id` thì cặp của hai lần chạy sẽ ghi đè nhau.
    """
    buckets: dict[tuple, dict[str, Row]] = {}
    for row in rows:
        if row.algo not in ALGO_ORDER:
            continue
        buckets.setdefault(tuple(getattr(row, name) for name in key_fields), {})[row.algo] = row
    return {key: Pair(by_algo["dijkstra"], by_algo["astar"])
            for key, by_algo in buckets.items()
            if "dijkstra" in by_algo and "astar" in by_algo}


def percentile(values: Sequence[float], fraction: float) -> float | None:
    """Phân vị bằng nội suy tuyến tính trên vị trí `(n-1)·p` (cùng cách với numpy mặc định)."""
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def median(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def quartiles(values: Sequence[float]) -> tuple[float | None, float | None]:
    """Tứ phân vị q1, q3; ít hơn 2 giá trị thì không có khoảng tứ phân vị."""
    if len(values) < 2:
        return None, None
    return percentile(values, 0.25), percentile(values, 0.75)


def fmt_number(value: float | None, digits: int = 4) -> str:
    """Số kiểu tài liệu: dấu phẩy thập phân, bỏ số 0 thừa; `None` → `—`."""
    if value is None:
        return MISSING
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return (text or "0").replace(".", ",")


def fmt_percent_rate(rate: float | None) -> str:
    """Tỉ lệ 0..1 → `100,0 %`."""
    if rate is None:
        return MISSING
    return f"{rate * 100:.1f}".replace(".", ",") + " %"


def fmt_percent_value(value: float | None) -> str:
    """Số đã là phần trăm (ví dụ 12,5 nghĩa là 12,5 %) → `12,5 %`."""
    if value is None:
        return MISSING
    return f"{value:.1f}".replace(".", ",") + " %"


def first_seen(values: Iterable) -> list:
    """Giữ thứ tự xuất hiện thay vì sắp xếp tuỳ ý."""
    return list(dict.fromkeys(values))


def order_strata(strata: Iterable[str]) -> list[str]:
    """Thứ tự tầng cố định `ngan → trung_binh → dai`; tầng lạ đặt sau."""
    present = first_seen(s for s in strata if s)
    return ([s for s in STRATUM_ORDER if s in present]
            + [s for s in present if s not in STRATUM_ORDER])


def stratum_label(stratum: str) -> str:
    return STRATUM_LABEL.get(stratum, stratum)


def source_line(rows: Sequence[Row], metas: Sequence[RunMeta], n_pairs: int) -> str:
    """Dòng nguồn của mỗi bảng: run_id, dataset_id, số cặp, Python, git_commit, git_dirty."""
    run_ids = first_seen(r.run_id for r in rows if r.run_id) or first_seen(m.run_id for m in metas)
    datasets = first_seen(r.dataset_id for r in rows if r.dataset_id) or [MISSING]
    pythons = first_seen(m.python for m in metas) or [MISSING]
    commits = first_seen(m.git_commit for m in metas) or [MISSING]
    dirty = any(m.git_dirty for m in metas)
    return ("Nguồn: run_id " + ", ".join(f"`{x}`" for x in run_ids)
            + " · dataset_id " + ", ".join(datasets)
            + f" · {n_pairs} cặp · Python " + ", ".join(pythons)
            + " · git " + ", ".join(commits) + f" (dirty: {'true' if dirty else 'false'})")


def match_rate(pairs: Sequence[Pair]) -> float | None:
    """Tỉ lệ cặp khớp chi phí; không có cặp nào thì `None`."""
    return sum(1 for pair in pairs if pair.matched) / len(pairs) if pairs else None


# --- Bảng E2, E3, E4 ---

def e2_section(rows: Sequence[Row], metas: Sequence[RunMeta]) -> Section:
    """Bảng E2: mỗi thuật toán × mỗi tầng (và "tất cả"): median/p95 ms, median expanded, khớp."""
    title = "E2 — A* vs Dijkstra trên vùng demo"
    demo = [r for r in rows if r.suite == SUITE_DEMO]
    if not demo:
        return Section(title, skipped="không có dòng nào thuộc suite demo (E2)")
    pairs = pair_stats(demo, ("run_id", "query_id"))
    if not pairs:
        return Section(title, skipped="không có cặp nào đủ kết quả của cả hai thuật toán")
    strata = order_strata(r.stratum for r in demo)
    table_rows: list[tuple[str, ...]] = []
    for algo in ALGO_ORDER:
        for key in [*strata, ALL_STRATA]:
            subset = [r for r in demo
                      if r.algo == algo and (key == ALL_STRATA or r.stratum == key)]
            if not subset:
                continue
            rate = None
            if algo == "astar":
                group = [p for p in pairs.values() if key == ALL_STRATA or p.stratum == key]
                rate = match_rate(group)
            table_rows.append((
                ALGO_LABEL[algo], stratum_label(key),
                fmt_number(median([r.runtime_ms for r in subset]), 3),
                fmt_number(percentile([r.runtime_ms for r in subset], 0.95), 3),
                fmt_number(median([float(r.expanded) for r in subset]), 1),
                fmt_percent_rate(rate),
            ))
    table = Table(
        headers=("Thuật toán", "Tầng", "Median ms", "p95 ms", "Median expanded", "Khớp chi phí"),
        rows=tuple(table_rows),
        formulas=("ms = runtime_ns_median / 1e6; median và p95 tính trên từng cặp (mỗi cặp một "
                  "giá trị), p95 nội suy tuyến tính. Khớp chi phí: |cost_A* − cost_D| ≤ "
                  "1e-6·max(1, cost_D); cả hai `no_path` cũng tính khớp."),
    )
    return Section(title, table, source_line(demo, metas, len(pairs)))


def _e3_group(row: Row) -> tuple:
    return (row.dataset_id, row.size_label, row.n_nodes, row.n_edges, row.workload)


def e3_section(rows: Sequence[Row], metas: Sequence[RunMeta]) -> Section:
    """Bảng E3: theo `|V|` — median r, median s, median ms của mỗi thuật toán."""
    title = "E3 — Tăng quy mô bản đồ"
    scaling = [r for r in rows if r.suite == SUITE_SCALING]
    if not scaling:
        return Section(title, skipped="không có dòng nào thuộc suite scaling (E3)")
    pairs = pair_stats(scaling, ("run_id", "workload", "n_nodes", "query_id"))
    groups = sorted(first_seen(_e3_group(r) for r in scaling),
                    key=lambda g: (g[0], g[2], g[4]))
    table_rows: list[tuple[str, ...]] = []
    notes: list[str] = []
    excluded = 0
    for group in groups:
        group_rows = [r for r in scaling if _e3_group(r) == group]
        group_pairs = [p for p in pairs.values() if _e3_group(p.dijkstra) == group]
        ratios = [p.ratio for p in group_pairs if p.ratio is not None]
        speeds = [p.speedup for p in group_pairs if p.speedup is not None]
        excluded += len(group_pairs) - len(ratios)
        dataset_id, size_label, n_nodes, n_edges, workload = group
        table_rows.append((
            size_label or MISSING, str(n_nodes), str(n_edges), workload or MISSING,
            fmt_number(median(ratios)),
            fmt_number(median(speeds)),
            fmt_number(median([r.runtime_ms for r in group_rows if r.algo == "dijkstra"]), 3),
            fmt_number(median([r.runtime_ms for r in group_rows if r.algo == "astar"]), 3),
        ))
        if ratios and speeds:
            parts = []
            if len(ratios) >= 2:
                r_low, r_high = quartiles(ratios)
                parts.append(f"r tứ phân vị [{fmt_number(r_low)}; {fmt_number(r_high)}]")
            if len(speeds) >= 2:
                s_low, s_high = quartiles(speeds)
                parts.append(f"s tứ phân vị [{fmt_number(s_low)}; {fmt_number(s_high)}]")
            if parts:
                notes.append(f"`{size_label or dataset_id}` (|V|={n_nodes}): "
                             + ", ".join(parts))
    if excluded:
        notes.append(f"Bỏ {excluded} cặp có expanded_D = 0 khi tính r (mục 3.2).")
    table = Table(
        headers=("Kích thước", "|V|", "|E|", "Workload", "Median r", "Median s",
                 "Median ms Dijkstra", "Median ms A*"),
        rows=tuple(table_rows),
        formulas=("r = expanded_A*/expanded_D và s = t_D/t_A* tính **từng cặp** rồi mới lấy "
                  "median (mục 3.2), không lấy tỉ số của hai trung bình; bỏ cặp expanded_D = 0."),
        notes=tuple(notes),
    )
    return Section(title, table, source_line(scaling, metas, len(pairs)))


def baseline_costs(rows: Sequence[Row]) -> dict[tuple, float]:
    """Chi phí kịch bản cơ sở theo (|V|, workload, source, target) để tính % tăng chi phí."""
    costs: dict[tuple, float] = {}
    for row in rows:
        if (row.algo != "dijkstra" or row.scenario_id != BASELINE or row.status != "ok"
                or row.cost_s is None):
            continue
        costs.setdefault((row.n_nodes, row.workload, row.source, row.target), row.cost_s)
    return costs


def cost_increase_pct(pair: Pair, baseline: dict[tuple, float]) -> float | None:
    """% tăng chi phí của đúng cặp so với kịch bản cơ sở; thiếu mốc cơ sở thì `None`."""
    row = pair.dijkstra
    if row.status != "ok" or row.cost_s is None:
        return None
    base = baseline.get((row.n_nodes, row.workload, row.source, row.target))
    if base is None or base <= 0:
        return None
    return (row.cost_s - base) / base * 100.0


def e4_section(rows: Sequence[Row], metas: Sequence[RunMeta]) -> Section:
    """Bảng E4: theo `scenario_id` — r, tỉ lệ còn đường, % tăng chi phí so với cơ sở."""
    title = "E4 — Ùn tắc và đóng đường"
    scenario = [r for r in rows if r.suite == SUITE_SCENARIO]
    if not scenario:
        return Section(title, skipped="không có dòng nào thuộc suite scenario (E4)")
    pairs = pair_stats(scenario, ("run_id", "scenario_id", "query_id"))
    names = first_seen(r.scenario_id for r in scenario if r.scenario_id) or [MISSING]
    baseline = baseline_costs(rows)
    table_rows: list[tuple[str, ...]] = []
    missing_baseline = 0
    for name in names:
        sc_pairs = [p for p in pairs.values() if p.scenario_id == name]
        dijkstra_rows = [r for r in scenario if r.scenario_id == name and r.algo == "dijkstra"]
        ratios = [p.ratio for p in sc_pairs if p.ratio is not None]
        increases = [value for p in sc_pairs
                     if (value := cost_increase_pct(p, baseline)) is not None]
        missing_baseline += len(sc_pairs) - len(increases)
        ok_rate = (sum(1 for r in dijkstra_rows if r.status == "ok") / len(dijkstra_rows)
                   if dijkstra_rows else None)
        table_rows.append((
            name, MISSING, fmt_percent_value(median(increases)),
            fmt_number(median(ratios)), fmt_percent_rate(ok_rate),
        ))
    notes = ["`% đổi tuyến` cần `edge_ids` của tuyến, không có trong measurements.csv nên để `—`."]
    if missing_baseline:
        notes.append(f"{missing_baseline} cặp không có mốc `baseline` cùng "
                     "(source, target, workload, |V|) nên không tính % tăng chi phí.")
    table = Table(
        headers=("Kịch bản", "% đổi tuyến", "Median % tăng chi phí", "Median r",
                 "Tỉ lệ còn đường"),
        rows=tuple(table_rows),
        formulas=("r = expanded_A*/expanded_D tính từng cặp rồi lấy median; % tăng chi phí = "
                  "100·(cost_kịch_bản − cost_baseline)/cost_baseline tính từng cặp so với dòng "
                  "`scenario_id = baseline` cùng (source, target, workload, |V|)."),
        notes=tuple(notes),
    )
    return Section(title, table, source_line(scenario, metas, len(pairs)))


# --- In ra ---

def render(rows: Sequence[Row], metas: Sequence[RunMeta]) -> str:
    """Toàn bộ báo cáo Markdown của ba bảng E2, E3, E4."""
    sections = (e2_section(rows, metas), e3_section(rows, metas), e4_section(rows, metas))
    blocks = ["# Tổng hợp kết quả benchmark", ""]
    for section in sections:
        blocks += [f"## {section.title}", ""]
        if section.table is None:
            blocks.append(f"Bỏ qua: {section.skipped}.")
        else:
            blocks += [section.source, "", section.table.to_markdown()]
            if section.table.formulas:
                blocks += ["", f"Công thức: {section.table.formulas}"]
            blocks += [f"- {note}" for note in section.table.notes]
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


def duplicate_run_ids(metas: Sequence[RunMeta]) -> list[str]:
    """Các `run_id` xuất hiện ở nhiều hơn một thư mục (dấu hiệu truyền trùng lần chạy)."""
    counts: dict[str, int] = {}
    for meta in metas:
        if meta.run_id:
            counts[meta.run_id] = counts.get(meta.run_id, 0) + 1
    return [run_id for run_id, count in counts.items() if count > 1]


def _reconfigure() -> None:
    """Ép UTF-8 khi in tiếng Việt ra file/pipe trên console Windows mặc định cp1252."""
    for stream in (sys.stdout, sys.stderr):
        encoding = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
        if encoding == "utf8" or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: nhận các thư mục kết quả, in Markdown; mã thoát 0/1/2."""
    _reconfigure()
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg in ("-h", "--help") for arg in args):
        print(__doc__.strip())
        return 0
    if not args or any(arg.startswith("-") for arg in args):
        print(USAGE, file=sys.stderr)
        return 2
    rows: list[Row] = []
    metas: list[RunMeta] = []
    seen: set[Path] = set()
    for text in args:
        path = Path(text)
        if path.resolve() in seen:                 # truyền trùng thư mục thì bỏ qua
            continue
        seen.add(path.resolve())
        try:
            rows.extend(read_rows(path))
            metas.append(read_meta(path))
        except (OSError, ValueError) as exc:
            print(f"lỗi: {exc}", file=sys.stderr)
            return 1
    repeated = duplicate_run_ids(metas)
    if repeated:
        print("cảnh báo: run_id " + ", ".join(f"`{x}`" for x in repeated)
              + " có ở nhiều thư mục; cặp trùng query_id sẽ bị gộp. "
              "Mỗi lần chạy nên có run_id riêng (--run-id).", file=sys.stderr)
    print(render(rows, metas), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
