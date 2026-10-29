"""Tình huống trên đồ thị mẫu `mini.json`, dùng chung cho test Dijkstra (T11) và A* (T20).

Đáp án độc lập do Bảo tính tay nằm ở `tests/fixtures/mini_expected.json` (T03). Helper ở đây
chỉ dựng Snapshot từ mô tả tình huống trong file đó, không chứa đáp án.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.graph.geo import haversine_m
from app.graph.model import Graph, GraphMeta, load_graph, node_by_name
from app.graph.scenario import (CongestionRule, CongestionZone, Scenario, Snapshot,
                                build_snapshot)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MINI = FIXTURES / "mini.json"
EXPECTED = FIXTURES / "mini_expected.json"


def load_mini() -> tuple[Graph, GraphMeta]:
    return load_graph(MINI)


def expected_cases() -> list[dict]:
    if not EXPECTED.exists():
        return []
    return json.loads(EXPECTED.read_text(encoding="utf-8"))["cases"]


def edge_id(graph: Graph, meta: GraphMeta, name: str) -> int:
    """'A->T' → edge id (fixture không có cạnh song song nên mỗi cặp chỉ có một cạnh)."""
    u_name, v_name = name.split("->")
    u, v = node_by_name(meta, u_name), node_by_name(meta, v_name)
    (e,) = [e for e in graph.out_edges[u] if graph.edge_v[e] == v]
    return e


def covering_zone(meta: GraphMeta) -> CongestionZone:
    """Vùng tròn phủ toàn bộ hình học của đồ thị, dùng cho mô tả `{"all": alpha}`.

    `CongestionZone` chỉ có hình tròn, nên "mọi cạnh" được biểu diễn bằng một vùng đủ lớn:
    tâm là trung điểm khung bao mọi điểm của `meta.edge_geometry`, bán kính là khoảng cách xa
    nhất từ tâm tới một điểm. Hình tròn lồi nên phủ mọi đỉnh hình học là phủ mọi trung điểm
    polyline, tức `edge_multipliers` nhân alpha cho mọi cạnh.
    """
    points = [point for geometry in meta.edge_geometry for point in geometry]   # (lon, lat)
    lats = [point[1] for point in points]
    lons = [point[0] for point in points]
    lat = (min(lats) + max(lats)) / 2
    lon = (min(lons) + max(lons)) / 2
    return CongestionZone(lat, lon, max(haversine_m(lat, lon, p[1], p[0]) for p in points))


def scenario_for(graph: Graph, meta: GraphMeta, case: dict) -> Scenario:
    """Dựng `Scenario` thật từ mô tả ngắn `scenario` của một tình huống trong mini_expected.json.

    Fixture có 3 dạng: `null` (cơ sở), `{"circle": {"center", "radius_m"}, "alpha"}` (một vùng
    tròn quanh một node) và `{"all": alpha}` (mọi cạnh, xem `covering_zone`). Kịch bản cơ sở giữ
    id `"baseline"` như `baseline_snapshot` của backend.
    """
    spec = case.get("scenario")
    if not spec:
        return Scenario(id="baseline")
    if "all" in spec:
        rule = CongestionRule(covering_zone(meta), spec["all"])
        return Scenario(id=case["name"], rules=(rule,))
    circle = spec["circle"]
    center = node_by_name(meta, circle["center"])
    zone = CongestionZone(graph.node_lat[center], graph.node_lon[center], circle["radius_m"])
    return Scenario(id=case["name"], rules=(CongestionRule(zone, spec["alpha"]),))


def snapshot_for(graph: Graph, meta: GraphMeta, case: dict) -> Snapshot:
    """Snapshot theo mô tả `scenario` + `blocked` của một tình huống trong mini_expected.json.

    Luật ùn tắc dựng thành `Scenario` rồi để `build_snapshot` của backend tính hệ số, nên test
    dùng đúng luật thật (docs/DATA_MODEL.md mục 4.1) thay vì tự nhân alpha.
    """
    blocked = frozenset(edge_id(graph, meta, b) for b in case.get("blocked", []))
    return build_snapshot(graph, meta, scenario_for(graph, meta, case), blocked)


def path_names(meta: GraphMeta, node_ids: list[int]) -> list[str]:
    return [meta.node_name[n] for n in node_ids]
