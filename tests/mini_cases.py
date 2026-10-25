"""Tình huống trên đồ thị mẫu `mini.json`, dùng chung cho test Dijkstra (T11) và A* (T20).

Đáp án độc lập do Bảo tính tay nằm ở `tests/fixtures/mini_expected.json` (T03). Helper ở đây
chỉ dựng Snapshot từ mô tả tình huống trong file đó, không chứa đáp án.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from app.graph.model import Graph, GraphMeta, load_graph, node_by_name
from app.graph.scenario import Snapshot, baseline_snapshot, make_snapshot

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


def _dist_m(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6_371_009 * math.asin(math.sqrt(a))


def snapshot_for(graph: Graph, meta: GraphMeta, case: dict) -> Snapshot:
    """Snapshot theo mô tả `scenario` + `blocked` của một tình huống trong mini_expected.json.

    Luật ùn tắc tạm thời cho test: cạnh có trung điểm (giữa hai đầu) trong vòng tròn thì nhân alpha.
    Luật thật của snapshot làm ở T40.
    """
    scenario = case.get("scenario")
    blocked = frozenset(edge_id(graph, meta, b) for b in case.get("blocked", []))
    if not scenario:
        return baseline_snapshot(graph) if not blocked else make_snapshot(
            graph, graph.edge_base_time_s, blocked, scenario_id="baseline")
    weights = list(graph.edge_base_time_s)
    if "all" in scenario:
        weights = [w * scenario["all"] for w in weights]
    else:
        c = scenario["circle"]
        center = node_by_name(meta, c["center"])
        for e in range(len(weights)):
            u, v = graph.edge_u[e], graph.edge_v[e]
            mid_lat = (graph.node_lat[u] + graph.node_lat[v]) / 2
            mid_lon = (graph.node_lon[u] + graph.node_lon[v]) / 2
            if _dist_m(mid_lat, mid_lon, graph.node_lat[center], graph.node_lon[center]) <= c["radius_m"]:
                weights[e] *= scenario["alpha"]
    return make_snapshot(graph, weights, blocked, scenario_id=case["name"])


def path_names(meta: GraphMeta, node_ids: list[int]) -> list[str]:
    return [meta.node_name[n] for n in node_ids]
