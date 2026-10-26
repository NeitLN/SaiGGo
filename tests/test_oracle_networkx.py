"""Đối chứng Dijkstra và A* với NetworkX trên đồ thị ngẫu nhiên (T21, issue #10).

Tiêu chuẩn: docs/DATA_MODEL.md mục 2, 5, 6 và docs/tasks/T21-oracle.md.
- 20 đồ thị (seed 0–19) × 50 cặp = 1.000 truy vấn;
- cost_s của dijkstra và astar(make_geo_heuristic) khớp nx.dijkstra_path_length trên MultiDiGraph
  với sai số 1e-9 · max(1, cost); no_path ⇔ NetworkXNoPath;
- Tuyến hợp lệ: cạnh nối tiếp, đúng chiều, tổng trọng số = cost_s, không dùng cạnh bị đóng;
- A* với heuristic địa lý có reopened == 0;
- Đồ thị ngẫu nhiên có cạnh song song, node không tới được, length_m >= haversine.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import networkx as nx
import pytest

from app.algorithms.astar import astar
from app.algorithms.dijkstra import dijkstra
from app.algorithms.heuristics import geo_scale, make_geo_heuristic, zero_heuristic
from app.algorithms.result import SearchResult
from app.graph.geo import haversine_m
from app.graph.model import Graph, load_graph
from app.graph.scenario import Snapshot, baseline_snapshot, make_snapshot
from helpers.random_graph import (
    BEN_THANH_LAT,
    BEN_THANH_LON,
    _DELTA_LAT,
    _DELTA_LON,
    make_random_graph,
    random_graph_dict,
    to_networkx,
)


def _verify_route(graph: Graph, snap: Snapshot, res: SearchResult, source: int, target: int) -> None:
    """Kiểm tra tính hợp lệ của tuyến: nối tiếp, đúng chiều, tổng trọng số, không bị chặn."""
    if source == target:
        assert res.cost_s == 0.0
        assert res.edge_ids == []
        assert res.node_ids == [source]
        assert res.distance_m == 0.0
        return

    assert len(res.edge_ids) >= 1
    assert len(res.node_ids) == len(res.edge_ids) + 1
    assert res.node_ids[0] == source
    assert res.node_ids[-1] == target
    assert graph.edge_u[res.edge_ids[0]] == source
    assert graph.edge_v[res.edge_ids[-1]] == target

    # Kiểm tra liên tiếp và đúng chiều
    for k in range(len(res.edge_ids) - 1):
        assert graph.edge_v[res.edge_ids[k]] == graph.edge_u[res.edge_ids[k + 1]]

    # Kiểm tra từng cạnh
    for k, e in enumerate(res.edge_ids):
        assert e not in snap.blocked
        assert not math.isinf(snap.weights[e])
        assert graph.edge_u[e] == res.node_ids[k]
        assert graph.edge_v[e] == res.node_ids[k + 1]

    # Kiểm tra tổng trọng số và khoảng cách
    tol_cost = 1e-9 * max(1.0, res.cost_s or 0.0)
    w_sum = sum(snap.weights[e] for e in res.edge_ids)
    assert abs(w_sum - res.cost_s) <= tol_cost

    tol_dist = 1e-9 * max(1.0, res.distance_m or 0.0)
    d_sum = sum(graph.edge_length_m[e] for e in res.edge_ids)
    assert abs(d_sum - res.distance_m) <= tol_dist


def test_random_graph_generator_invariants() -> None:
    """Kiểm tra các bất biến cấu trúc của bộ sinh đồ thị ngẫu nhiên."""
    graph, meta = make_random_graph(seed=42, n_nodes=50, n_edges=150)
    n = len(graph.node_lat)
    m = len(graph.edge_u)
    assert n == 50
    assert m == 150

    # 1. Tọa độ nằm trong hộp 2 km × 2 km quanh Bến Thành
    for lat, lon in zip(graph.node_lat, graph.node_lon):
        assert (BEN_THANH_LAT - _DELTA_LAT - 1e-9) <= lat <= (BEN_THANH_LAT + _DELTA_LAT + 1e-9)
        assert (BEN_THANH_LON - _DELTA_LON - 1e-9) <= lon <= (BEN_THANH_LON + _DELTA_LON + 1e-9)

    # 2. Chiều dài length_m >= haversine cho mọi cạnh và c == 1.0
    for u, v, length in zip(graph.edge_u, graph.edge_v, graph.edge_length_m):
        hav = haversine_m(graph.node_lat[u], graph.node_lon[u], graph.node_lat[v], graph.node_lon[v])
        assert length >= hav
    assert geo_scale(graph) == 1.0

    # 3. Có ít nhất một cặp cạnh song song
    parallel_found = False
    edge_pairs: dict[tuple[int, int], int] = {}
    for u, v in zip(graph.edge_u, graph.edge_v):
        edge_pairs[(u, v)] = edge_pairs.get((u, v), 0) + 1
        if edge_pairs[(u, v)] >= 2:
            parallel_found = True
    assert parallel_found, "đồ thị phải có ít nhất một cặp cạnh song song"

    # 4. Có ít nhất một node không tới được (in-degree == 0) và không thuộc SCC lớn nhất
    in_degrees = [0] * n
    for v in graph.edge_v:
        in_degrees[v] += 1
    unreachable_nodes = [i for i, deg in enumerate(in_degrees) if deg == 0]
    assert len(unreachable_nodes) >= 1, "đồ thị phải có ít nhất một node không tới được"
    assert 49 in unreachable_nodes, "node 49 được thiết kế có in-degree == 0"
    assert meta.node_in_scc[49] is False, "node không tới được không thể thuộc SCC lớn nhất"
    assert any(meta.node_in_scc), "phải có ít nhất một node thuộc SCC lớn nhất"

    # 5. out_edges[u] tăng dần theo edge id
    for u, edges in enumerate(graph.out_edges):
        assert edges == sorted(edges), f"out_edges[{u}] phải tăng dần"
        assert len(edges) == len(set(edges)), f"out_edges[{u}] không được trùng edge id"
        for e in edges:
            assert graph.edge_u[e] == u

    # 6. Tốc độ mô phỏng và v_max_mps
    valid_mps = {sp / 3.6 for sp in (20.0, 30.0, 40.0)}
    for sp in graph.edge_speed_mps:
        assert any(math.isclose(sp, v, abs_tol=1e-9) for v in valid_mps)
    assert graph.v_max_mps == max(graph.edge_speed_mps)

    # 7. Tính tái lập: cùng seed cho kết quả giống hệt
    graph2, meta2 = make_random_graph(seed=42, n_nodes=50, n_edges=150)
    assert graph == graph2
    assert meta == meta2

    # 8. Tham số không hợp lệ báo lỗi rõ ràng
    with pytest.raises(ValueError, match="n_nodes >= 3"):
        make_random_graph(seed=1, n_nodes=2, n_edges=10)
    with pytest.raises(ValueError, match="n_edges >= 2"):
        make_random_graph(seed=1, n_nodes=10, n_edges=1)


def test_random_graph_format_compatibility(tmp_path: Path) -> None:
    """Kiểm tra dict sinh ra tương thích hoàn toàn với file saigo-graph/1 và load_graph."""
    seed = 123
    data_dict = random_graph_dict(seed=seed, n_nodes=30, n_edges=80)
    file_path = tmp_path / "random_graph.json"
    file_path.write_text(json.dumps(data_dict), encoding="utf-8")

    loaded_graph, loaded_meta = load_graph(file_path)
    direct_graph, direct_meta = make_random_graph(seed=seed, n_nodes=30, n_edges=80)

    assert loaded_graph == direct_graph
    assert loaded_meta == direct_meta


def test_oracle_networkx_1000_queries() -> None:
    """20 đồ thị (seed 0–19) × 50 cặp = 1.000 truy vấn đối chứng với NetworkX."""
    n_graphs = 20
    queries_per_graph = 50
    total_queries = 0
    ok_count = 0
    no_path_count = 0

    for seed in range(n_graphs):
        graph, _ = make_random_graph(seed=seed, n_nodes=50, n_edges=150)
        snap = baseline_snapshot(graph)
        G = to_networkx(graph, snap)

        # 50 cặp truy vấn bao gồm các trường hợp:
        # - (0, 0): source == target
        # - (0, 49): target là node không tới được (no_path)
        # - (0, 1): cặp có cạnh song song
        # - 47 cặp ngẫu nhiên có seed
        rng_q = random.Random(seed + 1000)
        pairs: list[tuple[int, int]] = [(0, 0), (0, 49), (0, 1)]
        pairs.extend((rng_q.randrange(50), rng_q.randrange(50)) for _ in range(queries_per_graph - 3))

        for source, target in pairs:
            total_queries += 1
            res_dijkstra = dijkstra(graph, snap, source, target)
            h = make_geo_heuristic(graph, target)
            res_astar = astar(graph, snap, source, target, h)

            # Heuristic địa lý là consistent nên reopened phải luôn bằng 0
            assert res_astar.reopened == 0

            try:
                nx_cost = nx.dijkstra_path_length(G, source, target, weight="weight")
                # Tuyến tồn tại
                assert res_dijkstra.status == "ok"
                assert res_astar.status == "ok"
                assert res_dijkstra.cost_s is not None
                assert res_astar.cost_s is not None

                tol = 1e-9 * max(1.0, nx_cost)
                assert abs(res_dijkstra.cost_s - nx_cost) <= tol, (
                    f"seed {seed}, ({source}->{target}): dijkstra={res_dijkstra.cost_s}, nx={nx_cost}"
                )
                assert abs(res_astar.cost_s - nx_cost) <= tol, (
                    f"seed {seed}, ({source}->{target}): astar={res_astar.cost_s}, nx={nx_cost}"
                )
                assert abs(res_dijkstra.cost_s - res_astar.cost_s) <= tol

                _verify_route(graph, snap, res_dijkstra, source, target)
                _verify_route(graph, snap, res_astar, source, target)
                ok_count += 1

            except nx.NetworkXNoPath:
                # Không có đường đi ⇔ NetworkXNoPath
                assert res_dijkstra.status == "no_path"
                assert res_dijkstra.cost_s is None
                assert res_dijkstra.edge_ids == []
                assert res_dijkstra.node_ids == []

                assert res_astar.status == "no_path"
                assert res_astar.cost_s is None
                assert res_astar.edge_ids == []
                assert res_astar.node_ids == []
                no_path_count += 1

    assert total_queries == 1000
    assert ok_count > 0, "phải có ít nhất một truy vấn thành công"
    assert no_path_count > 0, "phải có ít nhất một truy vấn no_path"


def test_oracle_networkx_blocked_edges() -> None:
    """Đối chứng khi có cạnh bị chặn ngẫu nhiên qua Snapshot."""
    n_graphs = 5
    queries_per_graph = 30
    total_queries = 0

    for seed in range(100, 100 + n_graphs):
        graph, _ = make_random_graph(seed=seed, n_nodes=50, n_edges=150)
        rng_block = random.Random(seed + 999)

        # Chặn ngẫu nhiên 15 cạnh
        blocked_edges = frozenset(rng_block.sample(range(len(graph.edge_u)), 15))
        snap = make_snapshot(graph, graph.edge_base_time_s, blocked=blocked_edges, scenario_id="random-blocked")
        G = to_networkx(graph, snap)

        rng_q = random.Random(seed + 2000)
        for _ in range(queries_per_graph):
            total_queries += 1
            source = rng_q.randrange(50)
            target = rng_q.randrange(50)

            res_dijkstra = dijkstra(graph, snap, source, target)
            h = make_geo_heuristic(graph, target)
            res_astar = astar(graph, snap, source, target, h)

            assert res_astar.reopened == 0

            try:
                nx_cost = nx.dijkstra_path_length(G, source, target, weight="weight")
                assert res_dijkstra.status == "ok"
                assert res_astar.status == "ok"
                assert res_dijkstra.cost_s is not None
                assert res_astar.cost_s is not None

                tol = 1e-9 * max(1.0, nx_cost)
                assert abs(res_dijkstra.cost_s - nx_cost) <= tol
                assert abs(res_astar.cost_s - nx_cost) <= tol

                # Tuyến không bao giờ chứa cạnh bị đóng
                for e in res_dijkstra.edge_ids:
                    assert e not in blocked_edges
                for e in res_astar.edge_ids:
                    assert e not in blocked_edges

                _verify_route(graph, snap, res_dijkstra, source, target)
                _verify_route(graph, snap, res_astar, source, target)
            except nx.NetworkXNoPath:
                assert res_dijkstra.status == "no_path"
                assert res_astar.status == "no_path"

    assert total_queries == 150


def test_oracle_zero_heuristic_expands_identically_to_dijkstra() -> None:
    """Khi h = 0, A* phải mở rộng số node và số phép relax giống hệt Dijkstra."""
    graph, _ = make_random_graph(seed=777, n_nodes=40, n_edges=100)
    snap = baseline_snapshot(graph)
    rng_q = random.Random(888)

    for _ in range(25):
        source = rng_q.randrange(40)
        target = rng_q.randrange(40)
        res_d = dijkstra(graph, snap, source, target)
        res_a = astar(graph, snap, source, target, zero_heuristic)

        assert res_d.status == res_a.status
        assert res_d.cost_s == res_a.cost_s
        assert res_d.expanded == res_a.expanded
        assert res_d.relaxations == res_a.relaxations

