"""T11: Dijkstra và SearchResult (docs/DATA_MODEL.md mục 6, docs/tasks/T11-dijkstra.md)."""

import json
import math

import pytest

from app.algorithms.dijkstra import dijkstra
from app.graph.model import load_graph, node_by_name
from app.graph.scenario import baseline_snapshot, make_snapshot
from mini_cases import MINI, edge_id, expected_cases, load_mini, path_names, snapshot_for


@pytest.fixture(scope="module")
def mini():
    return load_mini()


def run(mini, src, dst, snap=None):
    graph, meta = mini
    snap = snap or baseline_snapshot(graph)
    return dijkstra(graph, snap, node_by_name(meta, src), node_by_name(meta, dst))


# --- Đáp án ở DATA_MODEL mục 7 (đã chạy kiểm bằng NetworkX khi lập kế hoạch) ---

def test_base_s_to_t(mini):
    r = run(mini, "S", "T")
    assert r.status == "ok"
    assert r.cost_s == pytest.approx(80.0)
    assert path_names(mini[1], r.node_ids) == ["S", "A", "T"]
    assert r.expanded == 5            # S, C, D, A, B; không tính lần pop đích
    assert r.distance_m == pytest.approx(800.0)


def test_directed_t_to_s_differs(mini):
    r = run(mini, "T", "S")
    assert r.cost_s == pytest.approx(100.0)
    assert path_names(mini[1], r.node_ids) == ["T", "B", "S"]


def test_no_path_when_both_entries_to_t_blocked(mini):
    graph, meta = mini
    blocked = {edge_id(graph, meta, "A->T"), edge_id(graph, meta, "B->T")}
    r = run(mini, "S", "T", make_snapshot(graph, graph.edge_base_time_s, frozenset(blocked)))
    assert r.status == "no_path"
    assert r.cost_s is None and r.edge_ids == [] and r.node_ids == []
    assert r.expanded == 5            # duyệt hết các node tới được rồi mới kết luận


def test_source_equals_target(mini):
    r = run(mini, "B", "B")
    assert r.status == "ok" and r.cost_s == 0 and r.edge_ids == [] and r.node_ids == [3]
    assert r.expanded == 0


def test_cost_is_sum_of_route_weights(mini):
    graph, meta = mini
    snap = baseline_snapshot(graph)
    r = run(mini, "S", "T", snap)
    assert r.cost_s == pytest.approx(sum(snap.weights[e] for e in r.edge_ids))
    # Các cạnh nối tiếp nhau, đúng chiều, khớp node_ids.
    assert [graph.edge_u[e] for e in r.edge_ids] == r.node_ids[:-1]
    assert [graph.edge_v[e] for e in r.edge_ids] == r.node_ids[1:]


def test_counters_consistent(mini):
    r = run(mini, "S", "T")
    assert r.unique_expanded == r.expanded and r.reopened == 0
    assert r.pushes >= r.relaxations >= 1
    assert 1 <= r.max_frontier <= r.pushes


def test_trace_limit(mini):
    graph, meta = mini
    snap = baseline_snapshot(graph)
    s, t = node_by_name(meta, "S"), node_by_name(meta, "T")
    assert dijkstra(graph, snap, s, t).trace == []
    full = dijkstra(graph, snap, s, t, trace_limit=10)
    assert path_names(meta, full.trace) == ["S", "C", "D", "A", "B"] and not full.trace_truncated
    cut = dijkstra(graph, snap, s, t, trace_limit=2)
    assert len(cut.trace) == 2 and cut.trace_truncated and cut.expanded == 5


def test_parallel_edge_uses_cheaper_edge_id(tmp_path):
    # Thêm cạnh song song S→A (key 1) nhanh gấp đôi; tuyến phải dùng đúng edge id của cạnh đó.
    data = json.loads(MINI.read_text(encoding="utf-8"))
    fast = dict(data["edges"][0], key=1, speed_kmh=72)
    edges = sorted(data["edges"] + [fast], key=lambda e: (e["u"], e["v"], e["key"]))
    for j, e in enumerate(edges):
        e["id"] = j
    data["edges"] = edges
    p = tmp_path / "parallel.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    graph, meta = load_graph(p)
    fast_id = next(e for e in edges if e["key"] == 1)["id"]
    r = dijkstra(graph, baseline_snapshot(graph), node_by_name(meta, "S"), node_by_name(meta, "T"))
    assert r.edge_ids[0] == fast_id
    assert r.cost_s == pytest.approx(20.0 + 40.0)


def test_blocking_cheaper_parallel_edge_falls_back(tmp_path):
    data = json.loads(MINI.read_text(encoding="utf-8"))
    fast = dict(data["edges"][0], key=1, speed_kmh=72)
    edges = sorted(data["edges"] + [fast], key=lambda e: (e["u"], e["v"], e["key"]))
    for j, e in enumerate(edges):
        e["id"] = j
    data["edges"] = edges
    p = tmp_path / "parallel.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    graph, meta = load_graph(p)
    fast_id = next(e for e in edges if e["key"] == 1)["id"]
    snap = make_snapshot(graph, graph.edge_base_time_s, frozenset({fast_id}))
    r = dijkstra(graph, snap, node_by_name(meta, "S"), node_by_name(meta, "T"))
    assert fast_id not in r.edge_ids
    assert r.cost_s == pytest.approx(80.0)


def test_invalid_node_rejected(mini):
    graph, _ = mini
    with pytest.raises(ValueError):
        dijkstra(graph, baseline_snapshot(graph), 0, 99)


def test_snapshot_rejects_bad_weights(mini):
    graph, _ = mini
    with pytest.raises(ValueError):
        make_snapshot(graph, [1.0] * 3)                       # sai độ dài
    with pytest.raises(ValueError):
        make_snapshot(graph, [-1.0] + [1.0] * 7)             # trọng số âm
    with pytest.raises(ValueError):
        make_snapshot(graph, [math.nan] + [1.0] * 7)         # không hữu hạn
    with pytest.raises(ValueError):
        make_snapshot(graph, graph.edge_base_time_s, frozenset({99}))   # cạnh đóng không tồn tại


def test_snapshot_id_stable_and_depends_on_blocked(mini):
    graph, _ = mini
    a = make_snapshot(graph, graph.edge_base_time_s, frozenset({4, 1}))
    b = make_snapshot(graph, graph.edge_base_time_s, frozenset({1, 4}))
    c = make_snapshot(graph, graph.edge_base_time_s, frozenset({1}))
    assert a.snapshot_id == b.snapshot_id != c.snapshot_id
    assert math.isinf(a.weights[4]) and math.isinf(a.weights[1])


def test_baseline_does_not_modify_graph(mini):
    graph, _ = mini
    before = list(graph.edge_base_time_s)
    make_snapshot(graph, graph.edge_base_time_s, frozenset({0}))
    assert graph.edge_base_time_s == before


# --- Đáp án tính tay độc lập của Bảo (T03); bỏ qua nếu file chưa có ---

@pytest.mark.parametrize("case", expected_cases(), ids=lambda c: c["name"])
def test_matches_hand_calculation(mini, case):
    graph, meta = mini
    snap = snapshot_for(graph, meta, case)
    r = dijkstra(graph, snap, node_by_name(meta, case["source"]), node_by_name(meta, case["target"]))
    want = case["dijkstra"]
    assert r.status == want["status"]
    if want["cost_s"] is None:
        assert r.cost_s is None
    else:
        assert r.cost_s == pytest.approx(want["cost_s"])
    assert path_names(meta, r.node_ids) == want["path"]
    assert r.expanded == want["expanded"]
