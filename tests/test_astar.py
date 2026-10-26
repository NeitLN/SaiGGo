"""T20: A* với heuristic địa lý (docs/DATA_MODEL.md mục 5–6, docs/tasks/T20-astar.md)."""

import json

import pytest

from app.algorithms.astar import astar
from app.algorithms.dijkstra import dijkstra
from app.algorithms.heuristics import geo_scale, make_geo_heuristic, zero_heuristic
from app.graph.model import load_graph, node_by_name
from app.graph.scenario import baseline_snapshot, make_snapshot
from mini_cases import edge_id, expected_cases, load_mini, path_names, snapshot_for


@pytest.fixture(scope="module")
def mini():
    return load_mini()


def run(mini, src, dst, snap=None, heuristic=None, **kw):
    graph, meta = mini
    snap = snap or baseline_snapshot(graph)
    s, t = node_by_name(meta, src), node_by_name(meta, dst)
    h = heuristic if heuristic is not None else make_geo_heuristic(graph, t)
    return astar(graph, snap, s, t, h, **kw)


def all_pairs(mini):
    names = [n for n in mini[1].node_name]
    return [(a, b) for a in names for b in names]


# --- Đáp án tính tay độc lập của Bảo (T03) ---

@pytest.mark.parametrize("case", expected_cases(), ids=lambda c: c["name"])
def test_matches_hand_calculation(mini, case):
    graph, meta = mini
    snap = snapshot_for(graph, meta, case)
    r = run(mini, case["source"], case["target"], snap)
    want = case["astar"]
    assert r.status == want["status"]
    if want["cost_s"] is None:
        assert r.cost_s is None
    else:
        assert r.cost_s == pytest.approx(want["cost_s"])
    assert path_names(meta, r.node_ids) == want["path"]
    assert r.expanded == want["expanded"]
    assert r.reopened == 0


def test_base_s_to_t_expands_only_s_and_a(mini):
    r = run(mini, "S", "T", trace_limit=10)
    assert r.cost_s == pytest.approx(80.0)
    assert path_names(mini[1], r.trace) == ["S", "A"]
    assert r.expanded == r.unique_expanded == 2


def test_no_path_explores_every_reachable_node(mini):
    graph, meta = mini
    blocked = frozenset({edge_id(graph, meta, "A->T"), edge_id(graph, meta, "B->T")})
    r = run(mini, "S", "T", make_snapshot(graph, graph.edge_base_time_s, blocked))
    assert r.status == "no_path" and r.cost_s is None and r.edge_ids == []
    assert r.expanded == 5


# --- A* cùng chi phí với Dijkstra; h = 0 thì giống hệt Dijkstra ---

def test_same_cost_as_dijkstra_on_all_pairs(mini):
    graph, meta = mini
    snap = baseline_snapshot(graph)
    for a, b in all_pairs(mini):
        s, t = node_by_name(meta, a), node_by_name(meta, b)
        d = dijkstra(graph, snap, s, t)
        r = astar(graph, snap, s, t, make_geo_heuristic(graph, t))
        assert r.status == d.status, (a, b)
        assert r.cost_s == pytest.approx(d.cost_s) if d.cost_s is not None else r.cost_s is None
        assert r.expanded <= d.expanded, (a, b)
        assert r.reopened == 0, (a, b)


@pytest.mark.parametrize("case", expected_cases(), ids=lambda c: c["name"])
def test_zero_heuristic_is_exactly_dijkstra(mini, case):
    graph, meta = mini
    snap = snapshot_for(graph, meta, case)
    s, t = node_by_name(meta, case["source"]), node_by_name(meta, case["target"])
    d = dijkstra(graph, snap, s, t, trace_limit=10)
    r = astar(graph, snap, s, t, zero_heuristic, trace_limit=10)
    assert r == d


def test_route_weights_sum_to_cost(mini):
    graph, _ = mini
    snap = baseline_snapshot(graph)
    r = run(mini, "T", "S", snap)
    assert sum(snap.weights[e] for e in r.edge_ids) == pytest.approx(r.cost_s)
    assert r.distance_m == pytest.approx(sum(graph.edge_length_m[e] for e in r.edge_ids))


# --- Heuristic ---

def test_heuristic_is_zero_at_target_and_never_overestimates(mini):
    graph, meta = mini
    snap = baseline_snapshot(graph)
    for a, b in all_pairs(mini):
        s, t = node_by_name(meta, a), node_by_name(meta, b)
        h = make_geo_heuristic(graph, t)
        assert h(t) == 0.0
        d = dijkstra(graph, snap, s, t)
        if d.cost_s is not None:
            assert h(s) <= d.cost_s + 1e-9, (a, b)


def test_heuristic_is_consistent_on_every_edge(mini):
    graph, _ = mini
    for t in range(len(graph.node_lat)):
        h = make_geo_heuristic(graph, t)
        for e in range(len(graph.edge_u)):
            u, v = graph.edge_u[e], graph.edge_v[e]
            assert h(u) <= graph.edge_base_time_s[e] + h(v) + 1e-9


def test_geo_scale_is_one_when_every_edge_is_at_least_straight_line(mini):
    assert geo_scale(mini[0]) == 1.0


def test_default_heuristic_stays_admissible_when_an_edge_is_shorter_than_straight_line(tmp_path):
    # Cạnh A→T dài 1 m nhưng hai đầu cách nhau ~111 m (lỗi dữ liệu kiểu làm tròn/đơn vị).
    # c = 1 cố định thì h(A) ≈ 111 s > chi phí thật 1 s và A* chọn S→T (3 s); c tự tính phải giữ đúng 2 s.
    S, A, T = range(3)
    lat = [10.770, 10.770, 10.771]
    arcs = [(S, A, 1.0), (S, T, 3.0), (A, T, 1.0)]
    data = {
        "format": "saigo-graph/1", "dataset_id": "short-edge",
        "nodes": [{"id": i, "lat": lat[i], "lon": 106.69} for i in range(3)],
        "edges": [{"id": j, "u": u, "v": v, "length_m": w, "speed_kmh": 3.6,
                   "geometry": [[106.69, lat[u]], [106.69, lat[v]]]} for j, (u, v, w) in enumerate(arcs)],
    }
    p = tmp_path / "short.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    graph, _ = load_graph(p)
    assert geo_scale(graph) < 0.01
    r = astar(graph, baseline_snapshot(graph), S, T, make_geo_heuristic(graph, T))
    assert r.cost_s == pytest.approx(2.0)
    assert r.node_ids == [S, A, T]


def test_heuristic_scale_c(mini):
    graph, meta = mini
    t = node_by_name(meta, "T")
    s = node_by_name(meta, "S")
    assert make_geo_heuristic(graph, t, c=0.5)(s) == pytest.approx(make_geo_heuristic(graph, t)(s) / 2)
    with pytest.raises(ValueError):
        make_geo_heuristic(graph, t, c=1.5)


# --- Mở lại node khi heuristic không consistent ---

def test_inconsistent_heuristic_reopens_and_stays_optimal(tmp_path):
    # S→A 3, S→B 1, B→A 1, A→T 3. h(B) = 3 không vượt chi phí thật (4) nhưng không consistent
    # (3 > w(B,A) + h(A) = 1): A bị mở rộng với g = 3, sau đó tìm được g = 2 qua B nên phải mở lại.
    S, A, B, T = range(4)
    arcs = [(S, A, 3), (S, B, 1), (A, T, 3), (B, A, 1)]       # đã sắp theo (u, v)
    data = {
        "format": "saigo-graph/1", "dataset_id": "reopen-test",
        "nodes": [{"id": i, "lat": 10.77 + i * 1e-3, "lon": 106.69} for i in range(4)],
        "edges": [{"id": j, "u": u, "v": v, "length_m": w, "speed_kmh": 3.6,
                   "geometry": [[106.69, 10.77 + u * 1e-3], [106.69, 10.77 + v * 1e-3]]}
                  for j, (u, v, w) in enumerate(arcs)],
    }
    p = tmp_path / "reopen.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    graph, _ = load_graph(p)
    h = {S: 0.0, A: 0.0, B: 3.0, T: 0.0}.get
    r = astar(graph, baseline_snapshot(graph), S, T, h, trace_limit=10)
    assert r.cost_s == pytest.approx(5.0)
    assert r.node_ids == [S, B, A, T]
    assert r.trace == [S, A, B, A]
    assert (r.expanded, r.unique_expanded, r.reopened) == (4, 3, 1)


# --- Biên ---

def test_source_equals_target(mini):
    r = run(mini, "A", "A")
    assert r.status == "ok" and r.cost_s == 0.0 and r.expanded == 0 and r.node_ids == [mini[1].node_name.index("A")]


def test_invalid_node_rejected(mini):
    graph, _ = mini
    with pytest.raises(ValueError):
        astar(graph, baseline_snapshot(graph), 0, 99, zero_heuristic)
