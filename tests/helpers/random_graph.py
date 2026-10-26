"""Bộ sinh đồ thị ngẫu nhiên và chuyển đổi sang NetworkX (docs/DATA_MODEL.md mục 2, 5).

Sinh đồ thị có hướng trong vùng 2 km × 2 km quanh Bến Thành, có cạnh song song,
node không tới được, và chiều dài cạnh luôn >= khoảng cách thẳng (haversine).
Dùng cho đối chứng Dijkstra và A* với NetworkX (T21).
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import networkx as nx

from app.graph.geo import EARTH_R_M, haversine_m
from app.graph.model import Graph, GraphMeta

if TYPE_CHECKING:
    from app.graph.scenario import Snapshot

# Tọa độ trung tâm chợ Bến Thành (DATA_MODEL mục 7)
BEN_THANH_LAT = 10.7725
BEN_THANH_LON = 106.6980

# Bán kính nửa cạnh vùng 2 km × 2 km (1 km mỗi phía)
HALF_BOX_M = 1000.0
_DELTA_LAT = (HALF_BOX_M / EARTH_R_M) * (180.0 / math.pi)
_DELTA_LON = (HALF_BOX_M / (EARTH_R_M * math.cos(math.radians(BEN_THANH_LAT)))) * (180.0 / math.pi)

# Các mức tốc độ mô phỏng (km/h) để v_max có ý nghĩa
SPEED_LEVELS_KMH = (20.0, 30.0, 40.0)


def _generate_nodes_and_edges(
    seed: int,
    n_nodes: int,
    n_edges: int,
) -> tuple[list[dict], list[dict]]:
    """Sinh danh sách thô của node và cạnh theo seed."""
    if n_nodes < 3:
        raise ValueError(f"cần n_nodes >= 3 để có cạnh song song và node không tới được, nhận {n_nodes}")
    if n_edges < 2:
        raise ValueError(f"cần n_edges >= 2 để có ít nhất một cặp cạnh song song, nhận {n_edges}")

    rng = random.Random(seed)

    # 1. Rải node ngẫu nhiên trong vùng 2 km × 2 km quanh Bến Thành
    node_lat = [rng.uniform(BEN_THANH_LAT - _DELTA_LAT, BEN_THANH_LAT + _DELTA_LAT) for _ in range(n_nodes)]
    node_lon = [rng.uniform(BEN_THANH_LON - _DELTA_LON, BEN_THANH_LON + _DELTA_LON) for _ in range(n_nodes)]

    # Node n_nodes - 1 là node không tới được: không cạnh nào trỏ vào nó
    unreachable_node = n_nodes - 1

    # 2. Cạnh: có hướng, length_m >= haversine, có cạnh song song
    raw_edges: list[dict] = []
    key_counter: dict[tuple[int, int], int] = {}

    def add_edge(u: int, v: int, factor: float | None = None, speed: float | None = None) -> None:
        key = key_counter.get((u, v), 0)
        key_counter[(u, v)] = key + 1
        hav = haversine_m(node_lat[u], node_lon[u], node_lat[v], node_lon[v])
        f = factor if factor is not None else rng.uniform(1.0, 1.5)
        length = max(hav, hav * f)
        sp = speed if speed is not None else rng.choice(SPEED_LEVELS_KMH)
        raw_edges.append({
            "u": u,
            "v": v,
            "key": key,
            "length_m": length,
            "speed_kmh": sp,
            "highway": "residential" if sp <= 25 else ("secondary" if sp <= 35 else "primary"),
            "geometry": [
                [node_lon[u], node_lat[u]],
                [node_lon[v], node_lat[v]],
            ],
        })

    # Đảm bảo ít nhất một cặp cạnh song song giữa 0 và 1 với trọng số khác nhau
    add_edge(0, 1, factor=rng.uniform(1.0, 1.2), speed=30.0)
    add_edge(0, 1, factor=rng.uniform(1.2, 1.5), speed=40.0)

    # Các cạnh còn lại: v chọn trong [0, n_nodes - 2] để giữ unreachable_node có in-degree = 0
    candidate_targets = list(range(n_nodes - 1))
    while len(raw_edges) < n_edges:
        u = rng.randrange(n_nodes - 1)
        v = rng.choice(candidate_targets)
        if u != v:
            add_edge(u, v)

    # Sắp xếp theo (u, v, key) trước khi đánh ID (DATA_MODEL mục 2.1)
    raw_edges.sort(key=lambda e: (e["u"], e["v"], e["key"]))
    for j, e in enumerate(raw_edges):
        e["id"] = j
        e["way_ids"] = [10000 + j]
        e["oneway"] = True

    # Tính thành phần liên thông mạnh lớn nhất (largest SCC) bằng NetworkX
    G_temp = nx.DiGraph()
    G_temp.add_nodes_from(range(n_nodes))
    for e in raw_edges:
        G_temp.add_edge(e["u"], e["v"])
    sccs = list(nx.strongly_connected_components(G_temp))
    sccs_candidates = [scc for scc in sccs if unreachable_node not in scc]
    largest_scc = max(sccs_candidates, key=len) if sccs_candidates else set()

    nodes = [
        {
            "id": i,
            "lat": node_lat[i],
            "lon": node_lon[i],
            "name": f"N{i}",
            "osmid": 1000 + i,
            "in_scc": i in largest_scc,
        }
        for i in range(n_nodes)
    ]
    return nodes, raw_edges


def random_graph_dict(
    seed: int,
    n_nodes: int = 50,
    n_edges: int = 150,
) -> dict:
    """Tạo dict theo chuẩn saigo-graph/1 từ đồ thị ngẫu nhiên."""
    nodes, edges = _generate_nodes_and_edges(seed, n_nodes, n_edges)
    return {
        "format": "saigo-graph/1",
        "dataset_id": f"random-{seed}",
        "crs": "EPSG:4326",
        "nodes": nodes,
        "edges": edges,
    }


def make_random_graph(
    seed: int,
    n_nodes: int = 50,
    n_edges: int = 150,
) -> tuple[Graph, GraphMeta]:
    """Sinh bộ đôi (Graph, GraphMeta) ngẫu nhiên có seed (DATA_MODEL mục 2).

    - Node trong 2 km × 2 km quanh Bến Thành.
    - Cạnh có hướng; length_m = haversine × hệ số [1; 1,5] >= haversine.
    - Có ít nhất một cặp cạnh song song và một node không tới được.
    - out_edges[u] tăng dần theo edge id.
    """
    nodes, edges = _generate_nodes_and_edges(seed, n_nodes, n_edges)

    node_lat = [float(n["lat"]) for n in nodes]
    node_lon = [float(n["lon"]) for n in nodes]
    edge_u = [e["u"] for e in edges]
    edge_v = [e["v"] for e in edges]
    edge_length_m = [float(e["length_m"]) for e in edges]
    edge_speed_mps = [float(e["speed_kmh"]) / 3.6 for e in edges]
    edge_base_time_s = [l / s for l, s in zip(edge_length_m, edge_speed_mps)]

    out_edges: list[list[int]] = [[] for _ in range(n_nodes)]
    for j, u in enumerate(edge_u):
        out_edges[u].append(j)

    graph = Graph(
        dataset_id=f"random-{seed}",
        node_lat=node_lat,
        node_lon=node_lon,
        edge_u=edge_u,
        edge_v=edge_v,
        edge_length_m=edge_length_m,
        edge_speed_mps=edge_speed_mps,
        edge_base_time_s=edge_base_time_s,
        out_edges=out_edges,
        v_max_mps=max(edge_speed_mps),
    )
    meta = GraphMeta(
        node_osmid=[n["osmid"] for n in nodes],
        node_name=[n["name"] for n in nodes],
        node_in_scc=[n["in_scc"] for n in nodes],
        edge_key=[e["key"] for e in edges],
        edge_way_ids=[list(e["way_ids"]) for e in edges],
        edge_highway=[e["highway"] for e in edges],
        edge_oneway=[bool(e["oneway"]) for e in edges],
        edge_geometry=[e["geometry"] for e in edges],
    )
    return graph, meta


def to_networkx(graph: Graph, snap: Snapshot | None = None) -> nx.MultiDiGraph:
    """Chuyển Graph hoặc Snapshot sang nx.MultiDiGraph để đối chứng kết quả."""
    G = nx.MultiDiGraph()
    for i in range(len(graph.node_lat)):
        G.add_node(i, lat=graph.node_lat[i], lon=graph.node_lon[i])

    weights = snap.weights if snap is not None else graph.edge_base_time_s
    for e in range(len(graph.edge_u)):
        w = weights[e]
        if math.isinf(w):
            continue  # Cạnh bị đóng trong snapshot, bỏ qua
        G.add_edge(
            graph.edge_u[e],
            graph.edge_v[e],
            key=e,
            weight=w,
            edge_id=e,
            length_m=graph.edge_length_m[e],
        )
    return G
