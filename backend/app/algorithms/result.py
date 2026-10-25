"""Kết quả tìm kiếm dùng chung cho Dijkstra và A* (docs/DATA_MODEL.md mục 6.2).

Thời gian chạy không nằm ở đây: nơi gọi (API, benchmark) tự đo bằng perf_counter_ns
quanh lời gọi hàm, để mọi thuật toán được đo cùng một cách.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.graph.model import Graph


@dataclass(frozen=True)
class SearchResult:
    status: str                      # "ok" | "no_path"
    cost_s: float | None
    edge_ids: list[int]              # tuyến theo cạnh, đúng chiều đi
    node_ids: list[int]              # [source, ..., target]
    distance_m: float | None
    expanded: int                    # số lần pop entry hợp lệ rồi duyệt cạnh ra; không tính lần pop đích
    unique_expanded: int
    reopened: int
    relaxations: int                 # số lần g[v] được cập nhật thành giá trị tốt hơn
    pushes: int
    max_frontier: int
    trace: list[int] = field(default_factory=list)   # K node mở rộng đầu tiên (K = trace_limit)
    trace_truncated: bool = False


def check_endpoints(graph: Graph, source: int, target: int) -> None:
    n = len(graph.node_lat)
    for name, node in (("source", source), ("target", target)):
        if not (isinstance(node, int) and 0 <= node < n):
            raise ValueError(f"{name} = {node!r} không phải node hợp lệ (0..{n - 1})")


def build_route(graph: Graph, pred_edge: list[int], source: int, target: int) -> tuple[list[int], list[int]]:
    """Dựng tuyến từ predecessor theo **cạnh**, để giữ đúng cạnh song song đã đi."""
    edges = []
    node = target
    while node != source:
        e = pred_edge[node]
        edges.append(e)
        node = graph.edge_u[e]
    edges.reverse()
    nodes = [source] + [graph.edge_v[e] for e in edges]
    return edges, nodes
