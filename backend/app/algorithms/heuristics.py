"""Heuristic cho A* (docs/DATA_MODEL.md mục 5).

h(n) = c · haversine(n, đích) / v_max: thời gian đi thẳng tới đích ở tốc độ lớn nhất, nên không
vượt chi phí thật còn lại. Với c = geo_scale(graph), h còn consistent kể cả khi dữ liệu có cạnh
ngắn hơn khoảng cách thẳng (mục 5.1–5.2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, NamedTuple

from app.graph.geo import haversine_m
from app.graph.model import Graph

Heuristic = Callable[[int], float]


class HeuristicViolation(NamedTuple):
    """Một cạnh vi phạm điều kiện độ dài (length_m < haversine_m - tol_m)."""
    edge_id: int
    length_m: float       # mét
    haversine_m: float    # mét
    ratio: float          # length_m / haversine_m


@dataclass(frozen=True)
class HeuristicReport:
    """Báo cáo kiểm tra điều kiện heuristic trên đồ thị."""
    v_max_mps: float      # m/s, tốc độ lớn nhất trong đồ thị
    c: float              # hệ số co giãn địa lý theo geo_scale(graph)
    n_violations: int     # số cạnh có length_m < haversine_m - tol_m
    worst: list[HeuristicViolation]   # tối đa 5 cạnh vi phạm có ratio nhỏ nhất


_scale_cache: dict[int, tuple[Graph, float]] = {}   # id(graph) → (graph, c); Graph không hash được


def geo_scale(graph: Graph) -> float:
    """c = min(1, min_e length_m(e) / hav(u_e, v_e)) trên các cạnh có hav > 0 (DATA_MODEL mục 5.1)."""
    hit = _scale_cache.get(id(graph))
    if hit is not None and hit[0] is graph:
        return hit[1]
    lat, lon = graph.node_lat, graph.node_lon
    c = 1.0
    for u, v, length in zip(graph.edge_u, graph.edge_v, graph.edge_length_m):
        hav = haversine_m(lat[u], lon[u], lat[v], lon[v])
        if hav > 0:
            c = min(c, length / hav)
    _scale_cache[id(graph)] = (graph, c)
    return c


def make_geo_heuristic(graph: Graph, target: int, c: float | None = None) -> Heuristic:
    """`c = None` thì dùng geo_scale(graph); truyền c riêng chỉ khi đã kiểm (T22)."""
    if c is None:
        c = geo_scale(graph)
    if not 0.0 <= c <= 1.0:
        raise ValueError(f"c = {c!r} phải nằm trong [0, 1], nếu không h có thể vượt chi phí thật")
    lat, lon = graph.node_lat, graph.node_lon
    lat_t, lon_t = lat[target], lon[target]
    scale = c / graph.v_max_mps

    def h(n: int) -> float:
        return scale * haversine_m(lat[n], lon[n], lat_t, lon_t)

    return h


def zero_heuristic(_: int) -> float:
    """h = 0: A* thành Dijkstra (dùng để test)."""
    return 0.0


def heuristic_report(graph: Graph, tol_m: float = 1e-3) -> HeuristicReport:
    """Báo cáo kiểm tra điều kiện heuristic trên đồ thị (docs/DATA_MODEL.md mục 5.1).

    Tính c = geo_scale(graph) chính xác không phụ thuộc ngưỡng để đảm bảo tính đúng của A*.
    Đếm vi phạm khi `length_m < haversine_m - tol_m` (mặc định tol_m = 1 mm = 1e-3 m để bỏ qua
    sai số làm tròn dấu phẩy động 7 chữ số thập phân khi lưu file, khớp với manifest dữ liệu thật).
    Danh sách worst chứa tối đa 5 cạnh vi phạm có tỷ lệ length_m / haversine_m nhỏ nhất.
    """
    c = geo_scale(graph)
    v_max_mps = graph.v_max_mps

    violations: list[HeuristicViolation] = []
    lat, lon = graph.node_lat, graph.node_lon
    for e, (u, v, length) in enumerate(zip(graph.edge_u, graph.edge_v, graph.edge_length_m)):
        hav = haversine_m(lat[u], lon[u], lat[v], lon[v])
        if hav > 0 and length < hav - tol_m:
            violations.append(HeuristicViolation(e, length, hav, length / hav))

    n_violations = len(violations)
    violations.sort(key=lambda item: (item.ratio, item.edge_id))
    worst = violations[:5]

    return HeuristicReport(
        v_max_mps=v_max_mps,
        c=c,
        n_violations=n_violations,
        worst=worst,
    )
