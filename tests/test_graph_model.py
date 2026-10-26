"""T01: bộ nạp đồ thị `saigo-graph/1` (docs/DATA_MODEL.md mục 2, docs/tasks/T01-graph-format.md)."""

import json
import math
from pathlib import Path

import pytest

from app.graph.model import Graph, GraphMeta, load_graph, node_by_name

ROOT = Path(__file__).resolve().parent.parent
MINI = ROOT / "tests" / "fixtures" / "mini.json"
MANIFEST = ROOT / "data" / "processed" / "manifest.json"


def haversine_m(lat1, lon1, lat2, lon2):
    # Bản tạm chỉ để kiểm fixture; hàm dùng chung nằm ở app.graph.geo (T10).
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6_371_009 * math.asin(math.sqrt(a))


@pytest.fixture(scope="module")
def mini():
    return load_graph(MINI)


def edge_between(graph: Graph, u: int, v: int) -> list[int]:
    return [e for e in graph.out_edges[u] if graph.edge_v[e] == v]


def test_mini_counts(mini):
    graph, meta = mini
    assert isinstance(graph, Graph) and isinstance(meta, GraphMeta)
    assert graph.dataset_id == "mini"
    assert len(graph.node_lat) == 6
    assert len(graph.edge_u) == 8


def test_node_by_name(mini):
    _, meta = mini
    assert [node_by_name(meta, n) for n in "SATBCD"] == [0, 1, 2, 3, 4, 5]
    with pytest.raises(KeyError):
        node_by_name(meta, "X")


def test_out_edges_of_s_sorted_by_id(mini):
    graph, meta = mini
    s = node_by_name(meta, "S")
    assert graph.out_edges[s] == [0, 1, 2, 3]


def test_directed_one_way(mini):
    graph, meta = mini
    a, t = node_by_name(meta, "A"), node_by_name(meta, "T")
    assert len(edge_between(graph, a, t)) == 1
    assert edge_between(graph, t, a) == []  # không có T→A: đồ thị có hướng


def test_base_time_and_v_max(mini):
    graph, meta = mini
    s, a = node_by_name(meta, "S"), node_by_name(meta, "A")
    (e,) = edge_between(graph, s, a)
    assert graph.edge_length_m[e] == 400
    assert graph.edge_speed_mps[e] == pytest.approx(10.0)
    assert graph.edge_base_time_s[e] == pytest.approx(40.0)
    assert graph.v_max_mps == pytest.approx(10.0)


def test_length_not_shorter_than_haversine(mini):
    # Điều kiện để heuristic A* là cận dưới (DATA_MODEL mục 5.1).
    graph, _ = mini
    for e in range(len(graph.edge_u)):
        u, v = graph.edge_u[e], graph.edge_v[e]
        hav = haversine_m(graph.node_lat[u], graph.node_lon[u], graph.node_lat[v], graph.node_lon[v])
        assert hav <= graph.edge_length_m[e]


def test_meta_geometry_lon_lat_from_u(mini):
    graph, meta = mini
    for e in range(len(graph.edge_u)):
        u = graph.edge_u[e]
        lon, lat = meta.edge_geometry[e][0]
        assert (lat, lon) == pytest.approx((graph.node_lat[u], graph.node_lon[u]))


def test_in_scc_defaults_true_when_missing(mini):
    _, meta = mini
    assert meta.node_in_scc == [True] * 6


def test_graph_is_immutable(mini):
    graph, _ = mini
    with pytest.raises(AttributeError):
        graph.v_max_mps = 99


def _swap_first_two_edges(d):
    # Đổi chỗ (0,1) và (0,3) nhưng vẫn đánh id theo vị trí: id hợp lệ, thứ tự (u, v, key) thì sai.
    d["edges"][0], d["edges"][1] = d["edges"][1], d["edges"][0]
    for j, e in enumerate(d["edges"]):
        e["id"] = j


def _broken(tmp_path, mutate):
    data = json.loads(MINI.read_text(encoding="utf-8"))
    mutate(data)
    p = tmp_path / "broken.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d.update(format="other/1"), "format"),
    (lambda d: d["edges"][0].update(speed_kmh=0), "speed_kmh"),
    (lambda d: d["edges"][0].update(speed_kmh=float("nan")), "speed_kmh"),
    (lambda d: d["edges"][0].update(length_m=-1), "length_m"),
    (lambda d: d["edges"][0].update(v=99), "v"),
    (lambda d: d["edges"][1].update(id=7), "id"),
    (lambda d: d["nodes"][2].update(id=5), "id"),
    (lambda d: d.update(edges=[]), "cạnh"),
    (lambda d: _swap_first_two_edges(d), r"\(u, v, key\)"),
    (lambda d: d["edges"][1].update(v=d["edges"][0]["v"]), r"\(u, v, key\)"),   # trùng (0, 1, 0)
])
def test_invalid_graph_rejected(tmp_path, mutate, message):
    with pytest.raises(ValueError, match=message):
        load_graph(_broken(tmp_path, mutate))


@pytest.mark.realdata
def test_loads_real_demo_graph():
    if not MANIFEST.exists():
        pytest.skip("chưa có data/processed/manifest.json (T31)")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    path = ROOT / manifest["file"]
    if not path.exists():
        pytest.skip(f"chưa có {manifest['file']}; chạy prepare_data.py build trước")
    graph, meta = load_graph(path)
    assert len(graph.node_lat) == manifest["node_count"]
    assert len(graph.edge_u) == manifest["edge_count"]
    assert sum(meta.node_in_scc) == manifest["scc_node_count"]
    assert graph.v_max_mps * 3.6 == pytest.approx(manifest["v_max_kmh"])
