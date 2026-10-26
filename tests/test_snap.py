"""Kiểm tra chức năng snap tọa độ về node có ngưỡng (T50, issue #19)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from app.graph.geo import haversine_m
from app.graph.model import Graph, GraphMeta, load_graph
from app.graph.snap import SnapError, SnapResult, nearest_node

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MINI_GRAPH_PATH = FIXTURES_DIR / "mini.json"


@pytest.fixture
def mini_graph():
    """Nạp đồ thị mini.json dùng cho kiểm thử snap."""
    return load_graph(MINI_GRAPH_PATH)


def test_snap_near_s_mini(mini_graph):
    """Điểm gần node S (id 0) trong mini.json phải snap về node 0 với khoảng cách chính xác tới 0.01m."""
    graph, meta = mini_graph
    # S có tọa độ (10.7725, 106.6980)
    lat, lon = 10.77251, 106.69801
    expected_dist = round(haversine_m(lat, lon, graph.node_lat[0], graph.node_lon[0]), 2)

    res = nearest_node(graph, meta, lat, lon, max_m=150.0)
    assert isinstance(res, SnapResult)
    assert res.node_id == 0
    assert res.snap_distance_m == expected_dist
    assert 0.0 < res.snap_distance_m < 2.0


def test_snap_exceeds_max_m_raises_snap_error(mini_graph):
    """Điểm cách mọi node > 150m phải ném ngoại lệ SnapError có chứa khoảng cách và ngưỡng."""
    graph, meta = mini_graph
    # Tọa độ cách xa cụm node của mini.json (> 1000m)
    lat, lon = 10.7850, 106.6980

    with pytest.raises(SnapError) as exc_info:
        nearest_node(graph, meta, lat, lon, max_m=150.0)

    err = exc_info.value
    assert isinstance(err, ValueError), "SnapError phải là lớp con của ValueError"
    assert err.max_m == 150.0
    assert err.distance_m is not None
    assert err.distance_m > 150.0
    assert "150.00" in str(err)
    assert f"{err.distance_m:.2f}" in str(err)


def test_snap_max_m_none_allows_distant_point(mini_graph):
    """Khi max_m=None thì không giới hạn khoảng cách, trả về node gần nhất dù ở xa."""
    graph, meta = mini_graph
    lat, lon = 10.7850, 106.6980

    res = nearest_node(graph, meta, lat, lon, max_m=None)
    assert isinstance(res, SnapResult)
    assert res.snap_distance_m > 150.0
    # Node B (id 3) ở phía bắc nhất (10.7751949, 106.7016577)
    assert res.node_id == 3


def test_snap_ignores_nodes_outside_scc():
    """Node không thuộc SCC (node_in_scc=False) không bao giờ được chọn dù ở gần hơn."""
    # Node 0 ở xa (thuộc SCC), Node 1 ở rất gần điểm bấm (ngoài SCC)
    graph = Graph(
        dataset_id="test_scc",
        node_lat=[10.7725, 10.7730],
        node_lon=[106.6980, 106.6980],
        edge_u=[0],
        edge_v=[0],
        edge_length_m=[10.0],
        edge_speed_mps=[10.0],
        edge_base_time_s=[1.0],
        out_edges=[[0], []],
        v_max_mps=10.0,
    )
    meta = GraphMeta(
        node_osmid=[1, 2],
        node_name=["Node 0 (SCC)", "Node 1 (non-SCC)"],
        node_in_scc=[True, False],  # Node 1 ngoài SCC
        edge_key=[0],
        edge_way_ids=[[100]],
        edge_highway=["primary"],
        edge_oneway=[True],
        edge_geometry=[[[106.6980, 10.7725], [106.6980, 10.7725]]],
    )

    # Điểm bấm rất gần Node 1
    query_lat, query_lon = 10.77301, 106.69801
    res = nearest_node(graph, meta, query_lat, query_lon, max_m=150.0)

    # Phải chọn Node 0, tuyệt đối không chọn Node 1
    assert res.node_id == 0
    assert res.snap_distance_m > 50.0


def test_snap_tie_breaking_smaller_id():
    """Khi hai node có khoảng cách bằng nhau tới điểm bấm, phải chọn node có id nhỏ hơn."""
    # Điểm bấm tại (10.0, 106.0)
    # Node 1 tại (10.001, 106.0) cách ~111m
    # Node 2 tại (9.999, 106.0) cách ~111m (đối xứng, cùng khoảng cách)
    graph = Graph(
        dataset_id="test_tie",
        node_lat=[10.001, 9.999],
        node_lon=[106.0, 106.0],
        edge_u=[],
        edge_v=[],
        edge_length_m=[],
        edge_speed_mps=[],
        edge_base_time_s=[],
        out_edges=[[], []],
        v_max_mps=10.0,
    )
    meta = GraphMeta(
        node_osmid=[1, 2],
        node_name=["N1", "N2"],
        node_in_scc=[True, True],
        edge_key=[],
        edge_way_ids=[],
        edge_highway=[],
        edge_oneway=[],
        edge_geometry=[],
    )

    res = nearest_node(graph, meta, 10.0, 106.0, max_m=150.0)
    assert res.node_id == 0  # Chọn node đầu tiên (id 0) thay vì id 1


def test_snap_invalid_coordinates(mini_graph):
    """Tọa độ không hợp lệ (ngoài phạm vi hoặc không hữu hạn) phải ném ValueError."""
    graph, meta = mini_graph

    with pytest.raises(ValueError, match="vĩ độ"):
        nearest_node(graph, meta, 95.0, 106.0)

    with pytest.raises(ValueError, match="vĩ độ"):
        nearest_node(graph, meta, -91.0, 106.0)

    with pytest.raises(ValueError, match="kinh độ"):
        nearest_node(graph, meta, 10.0, 185.0)

    with pytest.raises(ValueError, match="kinh độ"):
        nearest_node(graph, meta, 10.0, -181.0)

    with pytest.raises(ValueError, match="vĩ độ"):
        nearest_node(graph, meta, float("nan"), 106.0)

    with pytest.raises(ValueError, match="kinh độ"):
        nearest_node(graph, meta, 10.0, float("inf"))

    with pytest.raises(ValueError, match="vĩ độ"):
        nearest_node(graph, meta, True, 106.0)  # bool không hợp lệ


def test_snap_invalid_max_m(mini_graph):
    """Ngưỡng max_m âm hoặc không hữu hạn phải ném ValueError."""
    graph, meta = mini_graph

    with pytest.raises(ValueError, match="max_m"):
        nearest_node(graph, meta, 10.7725, 106.6980, max_m=-1.0)

    with pytest.raises(ValueError, match="max_m"):
        nearest_node(graph, meta, 10.7725, 106.6980, max_m=float("nan"))

    with pytest.raises(ValueError, match="max_m"):
        nearest_node(graph, meta, 10.7725, 106.6980, max_m=True)


def test_snap_no_nodes_in_scc_raises_value_error():
    """Nếu đồ thị không có node nào thuộc SCC thì ném ValueError."""
    graph = Graph(
        dataset_id="test_no_scc",
        node_lat=[10.7725],
        node_lon=[106.6980],
        edge_u=[],
        edge_v=[],
        edge_length_m=[],
        edge_speed_mps=[],
        edge_base_time_s=[],
        out_edges=[[]],
        v_max_mps=10.0,
    )
    meta = GraphMeta(
        node_osmid=[1],
        node_name=["N0"],
        node_in_scc=[False],  # Không có node nào trong SCC
        edge_key=[],
        edge_way_ids=[],
        edge_highway=[],
        edge_oneway=[],
        edge_geometry=[],
    )

    with pytest.raises(ValueError, match="không có node nào thuộc thành phần liên thông mạnh"):
        nearest_node(graph, meta, 10.7725, 106.6980)


def test_snap_result_immutable():
    """Kiểm tra SnapResult là dataclass frozen không cho gán lại thuộc tính."""
    res = SnapResult(node_id=0, snap_distance_m=10.5)
    assert res.node_id == 0
    assert res.snap_distance_m == 10.5

    with pytest.raises(AttributeError):
        res.node_id = 1

