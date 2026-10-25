"""T10: hàm địa lý dùng chung (docs/tasks/T10-geo.md)."""

import pytest

from app.graph.geo import EARTH_R_M, haversine_m, polyline_length_m, polyline_midpoint

BEN_THANH = (10.7725, 106.6980)

# Giá trị tham chiếu tính bằng osmnx.distance.great_circle (osmnx 2.1.1, cùng bán kính 6 371 009 m), ngày 26/10/2026.
REFERENCE = [
    ((10.7798, 106.6990), 819.0409867900955),    # tới khu Nhà thờ Đức Bà
    ((10.7495, 106.6511), 5726.199193139702),    # tới khu Chợ Lớn
    ((10.7725, 106.7080), 1092.3550100472314),   # cùng vĩ độ, lệch 0,01° kinh độ
]


def test_earth_radius_matches_osmnx():
    assert EARTH_R_M == 6_371_009


def test_same_point_is_zero():
    assert haversine_m(*BEN_THANH, *BEN_THANH) == 0


@pytest.mark.parametrize("other, expected", REFERENCE)
def test_matches_osmnx_reference(other, expected):
    assert haversine_m(*BEN_THANH, *other) == pytest.approx(expected, abs=0.5)


@pytest.mark.parametrize("other, _", REFERENCE)
def test_symmetric(other, _):
    assert haversine_m(*BEN_THANH, *other) == pytest.approx(haversine_m(*other, *BEN_THANH))


def test_polyline_length_sums_segments():
    lat, lon = BEN_THANH
    coords = [[lon, lat], [106.7080, lat], [106.7080, 10.7798]]   # GeoJSON: [lon, lat]
    expected = haversine_m(lat, lon, lat, 106.7080) + haversine_m(lat, 106.7080, 10.7798, 106.7080)
    assert polyline_length_m(coords) == pytest.approx(expected)


def test_midpoint_of_two_points_is_the_middle():
    a, b = [106.6980, 10.7725], [106.7000, 10.7745]
    lat, lon = polyline_midpoint([a, b])
    assert (lat, lon) == pytest.approx((10.7735, 106.6990), abs=1e-6)


def test_midpoint_is_at_half_length_not_middle_vertex():
    # Hình chữ L: đoạn 1 dài, đoạn 2 ngắn. Điểm ở 50% chiều dài nằm trên đoạn 1, không phải ở đỉnh giữa.
    lat0, lon0 = BEN_THANH
    coords = [[lon0, lat0], [lon0 + 0.01, lat0], [lon0 + 0.01, lat0 + 0.001]]
    lat, lon = polyline_midpoint(coords)
    assert lat == pytest.approx(lat0)
    assert lon0 < lon < lon0 + 0.01
    total = polyline_length_m(coords)
    assert haversine_m(lat0, lon0, lat, lon) == pytest.approx(total / 2, rel=1e-3)


def test_midpoint_returns_lat_lon_order():
    # Đầu vào là [lon, lat] (GeoJSON), đầu ra là (lat, lon). Đổi chỗ đầu vào thì kết quả phải khác.
    coords = [[106.6980, 10.7725], [106.6990, 10.7735]]
    lat, lon = polyline_midpoint(coords)
    assert 10 < lat < 11 and 106 < lon < 107
    swapped = [[p[1], p[0]] for p in coords]
    assert polyline_midpoint(swapped) != pytest.approx((lat, lon))


def test_midpoint_of_single_point_and_empty():
    assert polyline_midpoint([[106.698, 10.7725]]) == pytest.approx((10.7725, 106.698))
    with pytest.raises(ValueError):
        polyline_midpoint([])
