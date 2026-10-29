"""Ánh xạ (snap) điểm GPS về node gần nhất trong đồ thị (docs/DATA_MODEL.md mục 8.4, 8.5).

Hỗ trợ kiểm tra ngưỡng khoảng cách max_m (mặc định 150m), lọc node theo thành phần
liên thông mạnh lớn nhất (SCC), và giải quyết hòa khoảng cách bằng ID node nhỏ hơn.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from app.graph.geo import haversine_m
from app.graph.model import Graph, GraphMeta

TOL_TIE_M = 1e-7   # ~0.1 mm: ngưỡng phân định hòa khoảng cách số thực


class SnapError(ValueError):
    """Lỗi khi điểm cần snap cách mạng đường vượt quá ngưỡng cho phép (docs/ARCHITECTURE.md mục 4)."""

    def __init__(
        self,
        message: str,
        *,
        distance_m: float | None = None,
        max_m: float | None = None,
    ) -> None:
        super().__init__(message)
        self.distance_m = distance_m
        self.max_m = max_m


@dataclass(frozen=True)
class SnapResult:
    """Kết quả ánh xạ điểm về node mạng đường."""

    node_id: int
    snap_distance_m: float


def _finite(x: object) -> bool:
    """Kiểm tra số thực hữu hạn, loại trừ bool."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def nearest_node(
    graph: Graph,
    meta: GraphMeta,
    lat: float,
    lon: float,
    max_m: float | None = 150.0,
) -> SnapResult:
    """Tìm node gần nhất trong đồ thị, chỉ xét các node thuộc SCC lớn nhất (DATA_MODEL 8.4, 8.5).

    Tham số:
        graph: Đồ thị Graph chứa tọa độ các đỉnh
        meta: GraphMeta chứa cờ node_in_scc
        lat: Vĩ độ của điểm cần snap [-90, 90]
        lon: Kinh độ của điểm cần snap [-180, 180]
        max_m: Ngưỡng khoảng cách tối đa (mét), None nếu không giới hạn

    Trả về:
        SnapResult: node_id và khoảng cách snap_distance_m (làm tròn 2 chữ số thập phân)

    Ngoại lệ:
        ValueError: Tọa độ hoặc max_m không hợp lệ, hoặc không có node nào trong SCC
        SnapError: Khoảng cách tới node gần nhất vượt quá max_m
    """
    if not (_finite(lat) and -90.0 <= lat <= 90.0):
        raise ValueError(f"vĩ độ lat={lat!r} không hợp lệ (phải thuộc [-90, 90])")
    if not (_finite(lon) and -180.0 <= lon <= 180.0):
        raise ValueError(f"kinh độ lon={lon!r} không hợp lệ (phải thuộc [-180, 180])")

    if max_m is not None:
        if not (_finite(max_m) and max_m >= 0.0):
            raise ValueError(f"ngưỡng max_m={max_m!r} phải là số hữu hạn không âm hoặc None")

    n = len(graph.node_lat)
    if n == 0:
        raise ValueError("đồ thị không có node nào")
    if len(meta.node_in_scc) != n:
        raise ValueError(f"meta.node_in_scc có độ dài {len(meta.node_in_scc)} != số node {n}")

    # Chỉ xét các node thuộc SCC lớn nhất (DATA_MODEL mục 8.4)
    candidate_nodes = [i for i in range(n) if meta.node_in_scc[i]]
    if not candidate_nodes:
        raise ValueError("đồ thị không có node nào thuộc thành phần liên thông mạnh (SCC)")

    best_node = -1
    best_dist = math.inf

    for i in candidate_nodes:
        d = haversine_m(lat, lon, graph.node_lat[i], graph.node_lon[i])
        if d < best_dist - TOL_TIE_M:
            best_dist = d
            best_node = i
        elif abs(d - best_dist) <= TOL_TIE_M and (best_node == -1 or i < best_node):
            # Hòa khoảng cách: ưu tiên id nhỏ hơn
            best_node = i

    if max_m is not None and best_dist > max_m:
        raise SnapError(
            f"Điểm ({lat}, {lon}) cách mạng đường {best_dist:.2f} m, vượt quá ngưỡng cho phép {max_m:.2f} m",
            distance_m=round(best_dist, 2),
            max_m=max_m,
        )

    return SnapResult(node_id=best_node, snap_distance_m=round(best_dist, 2))

