"""T41: đóng đường một chiều / hai chiều và nhóm cạnh đối (docs/DATA_MODEL.md mục 4.2).

Dijkstra và A* phải cùng chi phí sau khi đóng, và tuyến mới không bao giờ chứa cạnh đã đóng.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.algorithms.astar import astar
from app.algorithms.dijkstra import dijkstra
from app.algorithms.heuristics import make_geo_heuristic
from app.graph.closures import close_both_ways, reverse_twins, validate_blocked
from app.graph.model import load_graph, node_by_name
from app.graph.scenario import make_snapshot
from mini_cases import MINI, edge_id, load_mini, path_names

P = [106.698, 10.7725]            # [lon, lat], cùng vị trí node S của mini.json
Q = [106.6996577, 10.7725]
BULGE_N = [106.6988, 10.7735]     # điểm giữa phình về phía bắc
BULGE_S = [106.6988, 10.7715]     # điểm giữa phình về phía nam


@pytest.fixture(scope="module")
def mini():
    return load_mini()


def snapshot_with(graph, blocked=frozenset()):
    return make_snapshot(graph, graph.edge_base_time_s, frozenset(blocked))


def run(mini, snap, src: str, dst: str) -> dict[str, object]:
    """Chạy cả hai thuật toán trên cùng snapshot; trả kết quả theo tên."""
    graph, meta = mini
    s, t = node_by_name(meta, src), node_by_name(meta, dst)
    return {
        "dijkstra": dijkstra(graph, snap, s, t),
        "astar": astar(graph, snap, s, t, make_geo_heuristic(graph, t)),
    }


def edge(u: int, v: int, geometry: list[list[float]], way_ids=(), key: int = 0,
         length_m: float = 200.0) -> dict:
    return {"u": u, "v": v, "key": key, "way_ids": list(way_ids), "highway": "residential",
            "oneway": False, "length_m": length_m, "speed_kmh": 36, "geometry": geometry}


def make_graph(tmp_path: Path, edges: list[dict]):
    """Đồ thị 2 node P/Q tự dựng trong test, ghi theo `saigo-graph/1` rồi nạp bằng `load_graph`."""
    nodes = [{"name": "P", "lat": P[1], "lon": P[0]}, {"name": "Q", "lat": Q[1], "lon": Q[0]}]
    data = {"format": "saigo-graph/1", "dataset_id": "test-closures", "crs": "EPSG:4326",
            "nodes": [dict(n, id=i) for i, n in enumerate(nodes)],
            "edges": [dict(e, id=j) for j, e in enumerate(edges)]}
    path = tmp_path / "closures.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return load_graph(path)


# --- Nhóm cạnh đối ---

def test_reverse_twins_on_mini(mini):
    graph, meta = mini
    twins = reverse_twins(graph, meta)
    assert len(twins) == len(graph.edge_u)
    assert twins[edge_id(graph, meta, "S->B")] == edge_id(graph, meta, "B->S")
    assert twins[edge_id(graph, meta, "B->S")] == edge_id(graph, meta, "S->B")
    assert twins[edge_id(graph, meta, "T->B")] == edge_id(graph, meta, "B->T")
    assert twins[edge_id(graph, meta, "B->T")] == edge_id(graph, meta, "T->B")
    for name in ("S->A", "A->T", "S->C", "S->D"):          # một chiều: không có cạnh đối
        assert twins[edge_id(graph, meta, name)] is None
    for e, twin in enumerate(twins):                       # đối xứng
        if twin is not None:
            assert twins[twin] == e


def test_reverse_twins_requires_same_way_ids(tmp_path):
    graph, meta = make_graph(tmp_path, [
        edge(0, 1, [P, Q], way_ids=[7]),      # P → Q
        edge(1, 0, [Q, P], way_ids=[7]),      # Q → P cùng way: cạnh đối
        edge(1, 0, [Q, P], way_ids=[8], key=1),   # cùng hình học, khác way
    ])
    assert reverse_twins(graph, meta) == [1, 0, None]


def test_reverse_twins_requires_reversed_geometry(tmp_path):
    graph, meta = make_graph(tmp_path, [
        edge(0, 1, [P, BULGE_N, Q], way_ids=[7]),
        edge(1, 0, [Q, BULGE_N, P], way_ids=[7]),     # đảo ngược đúng, kể cả điểm giữa
        edge(1, 0, [Q, BULGE_S, P], way_ids=[7], key=1),   # cùng hai đầu nhưng phình phía nam
        edge(1, 0, [Q, P], way_ids=[7], key=2),            # thiếu điểm giữa
    ])
    twins = reverse_twins(graph, meta)
    assert twins[0] == 1
    assert twins[2] is None and twins[3] is None


def test_reverse_twins_tolerates_tiny_coordinate_noise(tmp_path):
    noisy_q = [Q[0] + 1e-9, Q[1] - 1e-9]
    graph, meta = make_graph(tmp_path, [
        edge(0, 1, [P, Q], way_ids=[7]),
        edge(1, 0, [noisy_q, P], way_ids=[7]),
    ])
    assert reverse_twins(graph, meta)[0] == 1


def test_reverse_twins_rejects_geometry_off_by_metres(tmp_path):
    off_q = [Q[0] + 1e-4, Q[1]]          # ~11 m về phía đông: không còn là "hình học đảo ngược"
    graph, meta = make_graph(tmp_path, [
        edge(0, 1, [P, Q], way_ids=[7]),
        edge(1, 0, [off_q, P], way_ids=[7]),
    ])
    assert reverse_twins(graph, meta)[0] is None


# --- Kiểm danh sách cạnh đóng ---

def test_validate_blocked_dedups_and_accepts_iterables(mini):
    graph, _ = mini
    assert validate_blocked(graph, [3, 1, 3]) == frozenset({1, 3})
    assert validate_blocked(graph, (e for e in [2, 2])) == frozenset({2})
    assert validate_blocked(graph, []) == frozenset()


@pytest.mark.parametrize("bad", [8, 99, -1, "3", 3.0, True, None])
def test_validate_blocked_rejects_invalid_ids(mini, bad):
    graph, _ = mini
    with pytest.raises(ValueError, match="cạnh đóng"):
        validate_blocked(graph, [bad])


def test_close_both_ways_two_way_segment(mini):
    graph, meta = mini
    both = frozenset({edge_id(graph, meta, "S->B"), edge_id(graph, meta, "B->S")})
    assert close_both_ways(graph, meta, edge_id(graph, meta, "S->B")) == both
    assert close_both_ways(graph, meta, edge_id(graph, meta, "B->S")) == both


def test_close_both_ways_one_way_edge(mini):
    graph, meta = mini
    assert close_both_ways(graph, meta, edge_id(graph, meta, "A->T")) == frozenset({edge_id(graph, meta, "A->T")})


def test_close_both_ways_rejects_invalid_id(mini):
    graph, meta = mini
    with pytest.raises(ValueError, match="cạnh đóng"):
        close_both_ways(graph, meta, 99)


# --- Tìm đường sau khi đóng ---

def test_closing_a_to_t_reroutes_both_algorithms(mini):
    graph, meta = mini
    blocked = close_both_ways(graph, meta, edge_id(graph, meta, "A->T"))
    results = run(mini, snapshot_with(graph, blocked), "S", "T")
    for name, r in results.items():
        assert r.status == "ok", name
        assert path_names(meta, r.node_ids) == ["S", "B", "T"], name
        assert r.cost_s == pytest.approx(100.0), name
        assert not set(r.edge_ids) & blocked, name
    assert results["astar"].cost_s == pytest.approx(results["dijkstra"].cost_s)
    assert results["astar"].reopened == 0


def test_closing_both_entries_to_t_has_no_path(mini):
    graph, meta = mini
    blocked = validate_blocked(graph, [edge_id(graph, meta, "A->T"), edge_id(graph, meta, "B->T")])
    results = run(mini, snapshot_with(graph, blocked), "S", "T")
    for name, r in results.items():
        assert r.status == "no_path", name
        assert r.cost_s is None and r.edge_ids == [] and r.node_ids == [], name


def test_close_both_ways_blocks_both_directions(mini):
    graph, meta = mini
    blocked = close_both_ways(graph, meta, edge_id(graph, meta, "S->B"))
    forward = run(mini, snapshot_with(graph, blocked), "S", "T")
    for name, r in forward.items():
        assert r.status == "ok" and r.cost_s == pytest.approx(80.0), name
        assert path_names(meta, r.node_ids) == ["S", "A", "T"], name
        assert not set(r.edge_ids) & blocked, name
    backward = run(mini, snapshot_with(graph, blocked), "T", "S")
    for name, r in backward.items():
        assert r.status == "no_path", name       # T→S chỉ còn đường qua B→S vừa bị đóng


def test_parallel_edge_one_closed_other_still_usable(tmp_path):
    data = json.loads(MINI.read_text(encoding="utf-8"))
    fast = dict(data["edges"][0], key=1, speed_kmh=72)
    edges = sorted(data["edges"] + [fast], key=lambda e: (e["u"], e["v"], e["key"]))
    for j, e in enumerate(edges):
        e["id"] = j
    data["edges"] = edges
    path = tmp_path / "parallel.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    graph, meta = load_graph(path)

    u, v = node_by_name(meta, "S"), node_by_name(meta, "A")
    fast_id = next(e["id"] for e in edges if e["key"] == 1)
    slow_id = next(e["id"] for e in edges if e["u"] == u and e["v"] == v and e["key"] == 0)

    blocked = close_both_ways(graph, meta, fast_id)
    assert blocked == frozenset({fast_id})       # S→A một chiều: không có cạnh đối
    results = run((graph, meta), snapshot_with(graph, blocked), "S", "T")
    for name, r in results.items():
        assert r.status == "ok", name
        assert r.edge_ids[0] == slow_id and fast_id not in r.edge_ids, name
        assert r.cost_s == pytest.approx(80.0), name
