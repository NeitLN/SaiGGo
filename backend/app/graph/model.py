"""Đồ thị `saigo-graph/1`: định dạng file và bộ nạp dùng chung (docs/DATA_MODEL.md mục 2).

`Graph` chỉ chứa những gì thuật toán cần, dạng list theo chỉ số để tra cứu O(1).
`GraphMeta` chứa thứ để vẽ và tra cứu (tên, hình học, way OSM); thuật toán không đọc nó.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

FORMAT = "saigo-graph/1"


@dataclass(frozen=True)
class Graph:
    dataset_id: str
    node_lat: list[float]
    node_lon: list[float]
    edge_u: list[int]
    edge_v: list[int]
    edge_length_m: list[float]
    edge_speed_mps: list[float]
    edge_base_time_s: list[float]
    out_edges: list[list[int]]   # out_edges[u] = các edge id đi ra từ u, tăng dần
    v_max_mps: float             # tốc độ lớn nhất trong các cạnh, dùng cho heuristic A*


@dataclass(frozen=True)
class GraphMeta:
    node_osmid: list[int | None]
    node_name: list[str | None]
    node_in_scc: list[bool]      # node ngoài SCC lớn nhất: vẫn vẽ, không dùng làm điểm snap (mục 8.4)
    edge_key: list[int]
    edge_way_ids: list[list[int]]
    edge_highway: list[str | None]
    edge_oneway: list[bool]
    edge_geometry: list[list[list[float]]]   # [[lon, lat], ...], bắt đầu ở u


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def load_graph(path: str | Path) -> tuple[Graph, GraphMeta]:
    """Đọc file `saigo-graph/1`; dữ liệu sai thì raise ValueError (DATA_MODEL mục 2.3)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format") != FORMAT:
        raise ValueError(f"format phải là {FORMAT!r}, file có {data.get('format')!r}")
    nodes, edges = data["nodes"], data["edges"]
    if not edges:
        raise ValueError("đồ thị không có cạnh nào")
    n = len(nodes)

    for i, node in enumerate(nodes):
        if node["id"] != i:
            raise ValueError(f"nodes[{i}].id phải bằng {i}, file có {node['id']}")
        if not (_finite(node["lat"]) and _finite(node["lon"])):
            raise ValueError(f"nodes[{i}] có lat/lon không hợp lệ")

    out_edges: list[list[int]] = [[] for _ in range(n)]
    speed_mps, base_time = [], []
    for j, e in enumerate(edges):
        if e["id"] != j:
            raise ValueError(f"edges[{j}].id phải bằng {j}, file có {e['id']}")
        for end in ("u", "v"):
            if not (isinstance(e[end], int) and 0 <= e[end] < n):
                raise ValueError(f"edges[{j}].{end} = {e[end]!r} không phải node hợp lệ")
        if not (_finite(e["length_m"]) and e["length_m"] >= 0):
            raise ValueError(f"edges[{j}].length_m = {e['length_m']!r} phải hữu hạn và không âm")
        if not (_finite(e["speed_kmh"]) and e["speed_kmh"] > 0):
            raise ValueError(f"edges[{j}].speed_kmh = {e['speed_kmh']!r} phải hữu hạn và dương")
        mps = e["speed_kmh"] / 3.6
        speed_mps.append(mps)
        base_time.append(e["length_m"] / mps)
        out_edges[e["u"]].append(j)

    graph = Graph(
        dataset_id=data["dataset_id"],
        node_lat=[float(x["lat"]) for x in nodes],
        node_lon=[float(x["lon"]) for x in nodes],
        edge_u=[e["u"] for e in edges],
        edge_v=[e["v"] for e in edges],
        edge_length_m=[float(e["length_m"]) for e in edges],
        edge_speed_mps=speed_mps,
        edge_base_time_s=base_time,
        out_edges=out_edges,
        v_max_mps=max(speed_mps),
    )
    meta = GraphMeta(
        node_osmid=[x.get("osmid") for x in nodes],
        node_name=[x.get("name") for x in nodes],
        node_in_scc=[bool(x.get("in_scc", True)) for x in nodes],
        edge_key=[e.get("key", 0) for e in edges],
        edge_way_ids=[list(e.get("way_ids", [])) for e in edges],
        edge_highway=[e.get("highway") for e in edges],
        edge_oneway=[bool(e.get("oneway", False)) for e in edges],
        edge_geometry=[e["geometry"] for e in edges],
    )
    return graph, meta


def node_by_name(meta: GraphMeta, name: str) -> int:
    """Chỉ số node theo tên (fixture có `name`, dữ liệu thật thì không)."""
    try:
        return meta.node_name.index(name)
    except ValueError:
        raise KeyError(f"không có node tên {name!r}") from None
