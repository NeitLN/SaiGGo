"""Kiểm tra điều kiện heuristic A* và báo cáo heuristic (T22, issue #11).

Tiêu chuẩn: docs/DATA_MODEL.md mục 5, docs/TASKS.md mục T22.
- mini.json cho c = 1, 0 vi phạm;
- mini_bad.json cho c < 1 và A* với c đó khớp Dijkstra trên mọi cặp;
- heuristic_report trả về HeuristicReport với v_max_mps, c, n_violations, worst;
- bất đẳng thức tam giác (consistency) được bảo toàn khi nhân hệ số c.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.algorithms.astar import astar
from app.algorithms.dijkstra import dijkstra
from app.algorithms.heuristics import (
    HeuristicReport,
    HeuristicViolation,
    geo_scale,
    heuristic_report,
    make_geo_heuristic,
)
from app.graph.geo import haversine_m
from app.graph.model import Graph, GraphMeta, load_graph
from app.graph.scenario import baseline_snapshot

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MINI = FIXTURES / "mini.json"
MINI_BAD = FIXTURES / "mini_bad.json"


@pytest.fixture(scope="module")
def mini() -> tuple[Graph, GraphMeta]:
    return load_graph(MINI)


@pytest.fixture(scope="module")
def mini_bad() -> tuple[Graph, GraphMeta]:
    return load_graph(MINI_BAD)


def test_mini_json_heuristic_report(mini: tuple[Graph, GraphMeta]) -> None:
    """mini.json là đồ thị chuẩn: c = 1.0, 0 vi phạm, worst rỗng."""
    graph, _ = mini
    report = heuristic_report(graph)

    assert isinstance(report, HeuristicReport)
    assert report.c == 1.0
    assert report.n_violations == 0
    assert report.worst == []
    assert report.v_max_mps == pytest.approx(10.0)   # 36 km/h = 10 m/s


def test_mini_bad_json_heuristic_report(mini_bad: tuple[Graph, GraphMeta]) -> None:
    """mini_bad.json có cạnh 0 (S->A) dài 200 m < haversine (~399.55 m): c < 1."""
    graph, _ = mini_bad
    report = heuristic_report(graph)

    assert isinstance(report, HeuristicReport)
    assert report.c < 1.0
    # c phải bằng chính geo_scale(graph)
    assert report.c == geo_scale(graph)
    assert report.n_violations == 1
    assert len(report.worst) == 1

    # Kiểm tra phần tử worst
    violation = report.worst[0]
    assert isinstance(violation, HeuristicViolation)
    assert isinstance(violation, tuple)
    assert violation.edge_id == 0
    assert violation.length_m == 200.0
    assert violation.haversine_m > 200.0
    assert violation.ratio == pytest.approx(report.c)
    assert violation.ratio == pytest.approx(200.0 / violation.haversine_m)

    # Hỗ trợ unpack tuple: (edge_id, length_m, haversine_m, ratio)
    e_id, l_m, hav_m, ratio = violation
    assert e_id == 0
    assert l_m == 200.0
    assert hav_m == violation.haversine_m
    assert ratio == violation.ratio


def test_mini_bad_astar_matches_dijkstra_on_all_pairs(mini_bad: tuple[Graph, GraphMeta]) -> None:
    """Trên mini_bad.json, A* dùng c = geo_scale khớp Dijkstra trên 100% cặp node và reopened == 0."""
    graph, meta = mini_bad
    snap = baseline_snapshot(graph)
    n = len(graph.node_lat)

    report = heuristic_report(graph)
    assert report.c < 1.0

    for s in range(n):
        for t in range(n):
            res_d = dijkstra(graph, snap, s, t)
            # make_geo_heuristic mặc định gọi geo_scale(graph) để lấy c
            h = make_geo_heuristic(graph, t)
            res_a = astar(graph, snap, s, t, h)

            assert res_d.status == res_a.status
            if res_d.status == "ok":
                assert res_d.cost_s is not None
                assert res_a.cost_s is not None
                assert abs(res_d.cost_s - res_a.cost_s) <= 1e-9 * max(1.0, res_d.cost_s)

            # Heuristic địa lý với hệ số c giữ tính consistent nên reopened phải luôn bằng 0
            assert res_a.reopened == 0


def test_consistency_restored_by_scaling_c(mini_bad: tuple[Graph, GraphMeta]) -> None:
    """Chứng minh thực nghiệm: không nhân c thì vi phạm consistency; nhân c thì thỏa mãn."""
    graph, _ = mini_bad
    snap = baseline_snapshot(graph)
    c = geo_scale(graph)

    # Xét cạnh 0 (S -> A) có length_m = 200 m, v_max = 10 m/s => w = 20 s
    e = 0
    u, v = graph.edge_u[e], graph.edge_v[e]
    w_uv = snap.weights[e]   # 20.0 s
    target = v               # đích là A

    # Khi c = 1.0 (chưa scale):
    h_unscaled = make_geo_heuristic(graph, target, c=1.0)
    # h(S) ~ 39.955 s > w(S, A) + h(A) = 20.0 + 0 = 20.0 s => vi phạm consistency!
    assert h_unscaled(u) > w_uv + h_unscaled(target)

    # Khi dùng c = geo_scale(graph):
    h_scaled = make_geo_heuristic(graph, target, c=c)
    # h(S) = c * 39.955 s = 20.0 s <= w(S, A) + h(A) = 20.0 s => consistency được phục hồi!
    assert h_scaled(u) <= w_uv + h_scaled(target) + 1e-9

    # Kiểm tra consistency trên toàn bộ các cạnh và mọi đích trong đồ thị
    n = len(graph.node_lat)
    for t in range(n):
        h_t = make_geo_heuristic(graph, t)
        for edge_idx, (src, dst) in enumerate(zip(graph.edge_u, graph.edge_v)):
            w = snap.weights[edge_idx]
            # Bất đẳng thức tam giác: h(src) <= w(src, dst) + h(dst)
            assert h_t(src) <= w + h_t(dst) + 1e-9


def test_heuristic_report_worst_ordering_and_limit_5(tmp_path: Path) -> None:
    """Khi có nhiều hơn 5 vi phạm, report.worst chỉ giữ đúng 5 cạnh tệ nhất sắp tăng dần theo ratio."""
    # Tạo đồ thị có 1 node gốc và 8 node đích với các cạnh có tỷ lệ length / hav khác nhau
    lat_root, lon_root = 10.7725, 106.6980
    n_nodes = 9
    nodes = [{"id": 0, "lat": lat_root, "lon": lon_root}]

    # Rải 8 node theo đường kinh tuyến (cùng lon, khác lat) để khoảng cách đều ~1113 m
    for i in range(1, n_nodes):
        nodes.append({"id": i, "lat": lat_root + i * 0.01, "lon": lon_root})

    # Cạnh 0..7 từ 0 -> i, gán length_m để tạo 7 vi phạm với các tỷ lệ khác nhau
    # Tỷ lệ mong muốn: [0.2, 0.4, 0.1, 0.5, 0.3, 0.6, 0.7, 1.2 (không vi phạm)]
    desired_ratios = [0.2, 0.4, 0.1, 0.5, 0.3, 0.6, 0.7, 1.2]
    edges = []
    for j, r in enumerate(desired_ratios):
        target = j + 1
        hav = haversine_m(lat_root, lon_root, nodes[target]["lat"], nodes[target]["lon"])
        edges.append({
            "id": j,
            "u": 0,
            "v": target,
            "length_m": hav * r,
            "speed_kmh": 36,
            "geometry": [[lon_root, lat_root], [nodes[target]["lon"], nodes[target]["lat"]]],
        })

    data = {
        "format": "saigo-graph/1",
        "dataset_id": "multi-violation",
        "nodes": nodes,
        "edges": edges,
    }
    p = tmp_path / "multi_bad.json"
    p.write_text(json.dumps(data), encoding="utf-8")

    graph, _ = load_graph(p)
    report = heuristic_report(graph)

    # Có 7 cạnh vi phạm (r < 1.0)
    assert report.n_violations == 7
    # worst chỉ lấy tối đa 5 cạnh
    assert len(report.worst) == 5
    # Tỷ lệ nhỏ nhất là 0.1
    assert report.c == pytest.approx(0.1)
    assert report.worst[0].ratio == pytest.approx(0.1)
    assert report.worst[0].edge_id == 2   # cạnh ứng với ratio 0.1

    # Thứ tự các tỷ lệ trong worst phải tăng dần
    ratios = [v.ratio for v in report.worst]
    assert ratios == sorted(ratios)
    assert ratios == pytest.approx([0.1, 0.2, 0.3, 0.4, 0.5])


def test_heuristic_report_zero_distance_edge_not_violation(tmp_path: Path) -> None:
    """Cạnh có khoảng cách haversine = 0 (hai đầu trùng tọa độ) không tính là vi phạm."""
    data = {
        "format": "saigo-graph/1",
        "dataset_id": "zero-hav",
        "nodes": [
            {"id": 0, "lat": 10.7725, "lon": 106.6980},
            {"id": 1, "lat": 10.7725, "lon": 106.6980},  # cùng tọa độ với 0
        ],
        "edges": [
            {
                "id": 0,
                "u": 0,
                "v": 1,
                "length_m": 0.0,
                "speed_kmh": 36,
                "geometry": [[106.6980, 10.7725], [106.6980, 10.7725]],
            }
        ],
    }
    p = tmp_path / "zero_hav.json"
    p.write_text(json.dumps(data), encoding="utf-8")

    graph, _ = load_graph(p)
    report = heuristic_report(graph)

    assert report.c == 1.0
    assert report.n_violations == 0
    assert report.worst == []


def test_heuristic_report_floating_point_tolerance(tmp_path: Path) -> None:
    """Sai số làm tròn (< 1 mm = 1e-3 m) không tính là vi phạm nhưng c vẫn < 1; thiếu >= 1 mm thì tính vi phạm."""
    lat_root, lon_root = 10.7725, 106.6980
    hav = haversine_m(lat_root, lon_root, lat_root + 0.01, lon_root)

    # Trường hợp 1: thiếu 1e-6 m (1 micromet) so với haversine
    data_micro = {
        "format": "saigo-graph/1",
        "dataset_id": "micro-diff",
        "nodes": [
            {"id": 0, "lat": lat_root, "lon": lon_root},
            {"id": 1, "lat": lat_root + 0.01, "lon": lon_root},
        ],
        "edges": [
            {
                "id": 0,
                "u": 0,
                "v": 1,
                "length_m": hav - 1e-6,
                "speed_kmh": 36,
                "geometry": [[lon_root, lat_root], [lon_root, lat_root + 0.01]],
            }
        ],
    }
    p_micro = tmp_path / "micro.json"
    p_micro.write_text(json.dumps(data_micro), encoding="utf-8")
    graph_micro, _ = load_graph(p_micro)
    report_micro = heuristic_report(graph_micro)

    # c < 1 để bảo vệ A* khỏi vượt chi phí thật
    assert report_micro.c < 1.0
    assert report_micro.c == pytest.approx((hav - 1e-6) / hav)
    # n_violations == 0 do nằm trong ngưỡng dung sai tol_m = 1 mm (1e-3 m)
    assert report_micro.n_violations == 0
    assert report_micro.worst == []

    # Trường hợp 2: thiếu 1.0 m (> 1 mm)
    data_macro = {
        "format": "saigo-graph/1",
        "dataset_id": "macro-diff",
        "nodes": [
            {"id": 0, "lat": lat_root, "lon": lon_root},
            {"id": 1, "lat": lat_root + 0.01, "lon": lon_root},
        ],
        "edges": [
            {
                "id": 0,
                "u": 0,
                "v": 1,
                "length_m": hav - 1.0,
                "speed_kmh": 36,
                "geometry": [[lon_root, lat_root], [lon_root, lat_root + 0.01]],
            }
        ],
    }
    p_macro = tmp_path / "macro.json"
    p_macro.write_text(json.dumps(data_macro), encoding="utf-8")
    graph_macro, _ = load_graph(p_macro)
    report_macro = heuristic_report(graph_macro)

    assert report_macro.c < 1.0
    assert report_macro.n_violations == 1
    assert len(report_macro.worst) == 1
    assert report_macro.worst[0].edge_id == 0

