"""A* trên đồ thị có hướng, trọng số không âm (docs/DATA_MODEL.md mục 5–6).

Cùng quy tắc với Dijkstra (mục 6.3), chỉ khác độ ưu tiên là f = g + h. Heap chứa
(f, counter, node, g lúc push); entry lỗi thời (g lớn hơn g[node] hiện tại) bị bỏ qua khi pop,
trước khi kiểm tra đích. Node đã mở rộng vẫn được mở lại nếu tìm được g tốt hơn; với heuristic
consistent việc này không xảy ra, và `reopened` đếm lại để kiểm chứng.
"""

from __future__ import annotations

import heapq
import math

from app.algorithms.heuristics import Heuristic
from app.algorithms.result import SearchResult, build_route, check_endpoints
from app.graph.model import Graph
from app.graph.scenario import Snapshot


def astar(graph: Graph, snap: Snapshot, source: int, target: int, heuristic: Heuristic,
          *, trace_limit: int = 0) -> SearchResult:
    check_endpoints(graph, source, target)
    if source == target:
        return SearchResult("ok", 0.0, [], [source], 0.0, 0, 0, 0, 0, 0, 0)

    weights, out_edges, edge_v = snap.weights, graph.out_edges, graph.edge_v
    n = len(graph.node_lat)
    g = [math.inf] * n
    pred_edge = [-1] * n
    closed = bytearray(n)                 # node đã mở rộng ít nhất một lần
    g[source] = 0.0
    heap = [(heuristic(source), 0, source, 0.0)]
    counter = 1
    expanded = reopened = relaxations = 0
    pushes = max_frontier = 1
    trace: list[int] = []

    while heap:
        _, _, u, d = heapq.heappop(heap)
        if d > g[u]:
            continue                      # entry lỗi thời
        if u == target:
            edges, nodes = build_route(graph, pred_edge, source, target)
            return SearchResult("ok", d, edges, nodes, sum(graph.edge_length_m[e] for e in edges),
                                expanded, expanded - reopened, reopened, relaxations, pushes, max_frontier,
                                trace, trace_limit > 0 and expanded > trace_limit)
        if closed[u]:
            reopened += 1
        closed[u] = 1
        expanded += 1
        if len(trace) < trace_limit:
            trace.append(u)
        for e in out_edges[u]:
            w = weights[e]
            if w == math.inf:
                continue                  # cạnh bị đóng trong snapshot này
            v = edge_v[e]
            nd = d + w
            if nd < g[v]:
                g[v] = nd
                pred_edge[v] = e
                relaxations += 1
                heapq.heappush(heap, (nd + heuristic(v), counter, v, nd))
                counter += 1
                pushes += 1
                max_frontier = max(max_frontier, len(heap))

    return SearchResult("no_path", None, [], [], None, expanded, expanded - reopened, reopened, relaxations,
                        pushes, max_frontier, trace, trace_limit > 0 and expanded > trace_limit)
