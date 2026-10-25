"""Khoảng cách trên mặt cầu, dùng chung cho heuristic A*, snap và vùng ùn tắc.

Điểm đơn lẻ truyền theo (lat, lon); polyline theo GeoJSON: [[lon, lat], ...].
"""

from __future__ import annotations

import math

EARTH_R_M = 6_371_009   # mét, cùng bán kính OSMnx dùng để tính `length` (DATA_MODEL mục 5.1)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R_M * math.asin(min(1.0, math.sqrt(a)))


def _segment_lengths(coords: list[list[float]]) -> list[float]:
    return [haversine_m(a[1], a[0], b[1], b[0]) for a, b in zip(coords, coords[1:])]


def polyline_length_m(coords: list[list[float]]) -> float:
    return sum(_segment_lengths(coords))


def polyline_midpoint(coords: list[list[float]]) -> tuple[float, float]:
    """(lat, lon) của điểm nằm ở 50% chiều dài polyline (dùng để gán ùn tắc cho cạnh, DATA_MODEL mục 4.1)."""
    if not coords:
        raise ValueError("polyline rỗng")
    lengths = _segment_lengths(coords)
    half = sum(lengths) / 2
    if half == 0:
        return coords[0][1], coords[0][0]
    walked = 0.0
    for (a, b), seg in zip(zip(coords, coords[1:]), lengths):
        if walked + seg >= half:
            # Nội suy tuyến tính trong một đoạn; đoạn đường phố đủ ngắn để sai số không đáng kể.
            f = (half - walked) / seg
            return a[1] + f * (b[1] - a[1]), a[0] + f * (b[0] - a[0])
        walked += seg
    return coords[-1][1], coords[-1][0]
