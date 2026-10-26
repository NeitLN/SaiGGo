"""Snapshot: trọng số cạnh cho đúng một lần tìm kiếm (docs/DATA_MODEL.md mục 4.3).

Đồ thị gốc không bao giờ bị sửa; ùn tắc và đóng đường chỉ nằm trong snapshot.

T40 thêm `Scenario` / `CongestionZone` (luật ùn tắc theo vùng, mục 4.1),
`build_snapshot` và `load_scenarios` (đọc `data/config/scenarios.json`) vào file này,
dùng lại đúng kiểu `Snapshot` và `make_snapshot` của T11.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.graph.geo import haversine_m, polyline_midpoint
from app.graph.model import Graph, GraphMeta

SCENARIO_FORMAT = "saigo-scenarios/1"


@dataclass(frozen=True)
class Snapshot:
    dataset_id: str
    scenario_id: str
    weights: list[float]      # weights[e], giây; math.inf nếu cạnh bị đóng
    blocked: frozenset[int]
    snapshot_id: str


def make_snapshot(graph: Graph, weights: list[float], blocked: frozenset[int] = frozenset(),
                  scenario_id: str = "custom") -> Snapshot:
    """Snapshot từ trọng số đã tính; cạnh trong `blocked` thành vô cực."""
    m = len(graph.edge_u)
    if len(weights) != m:
        raise ValueError(f"cần {m} trọng số, nhận {len(weights)}")
    for e, w in enumerate(weights):
        if not (math.isfinite(w) and w >= 0):
            raise ValueError(f"trọng số cạnh {e} = {w!r} phải hữu hạn và không âm")
    bad = [e for e in blocked if not (isinstance(e, int) and 0 <= e < m)]
    if bad:
        raise ValueError(f"cạnh đóng không tồn tại: {sorted(bad)}")
    final = [math.inf if e in blocked else w for e, w in enumerate(weights)]
    key = f"{graph.dataset_id}|{scenario_id}|{','.join(map(str, sorted(blocked)))}"
    return Snapshot(graph.dataset_id, scenario_id, final, frozenset(blocked),
                    hashlib.sha1(key.encode("utf-8")).hexdigest()[:12])


def baseline_snapshot(graph: Graph) -> Snapshot:
    """Kịch bản cơ sở: trọng số = thời gian cơ sở, không đóng cạnh nào."""
    return make_snapshot(graph, graph.edge_base_time_s, frozenset(), scenario_id="baseline")


def _finite(x) -> bool:
    """Cùng quy ước với model._finite: số thực hữu hạn, không nhận bool."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _number(value, what: str) -> float:
    if not _finite(value):
        raise ValueError(f"{what} = {value!r} phải là số hữu hạn")
    return float(value)


@dataclass(frozen=True)
class CongestionZone:
    """Vùng ùn tắc hình tròn (DATA_MODEL 4.1): tâm (lat, lon), bán kính mét, tính cả biên."""

    lat: float
    lon: float
    radius_m: float
    type: str = "circle"

    def __post_init__(self) -> None:
        if self.type != "circle":
            raise ValueError(f"loại vùng {self.type!r} chưa hỗ trợ, chỉ có 'circle'")
        if not (_finite(self.lat) and -90.0 <= self.lat <= 90.0):
            raise ValueError(f"vĩ độ tâm vùng = {self.lat!r} không hợp lệ")
        if not (_finite(self.lon) and -180.0 <= self.lon <= 180.0):
            raise ValueError(f"kinh độ tâm vùng = {self.lon!r} không hợp lệ")
        if not (_finite(self.radius_m) and self.radius_m >= 0.0):
            raise ValueError(f"bán kính vùng = {self.radius_m!r} phải hữu hạn và không âm")

    def contains(self, lat: float, lon: float) -> bool:
        """Điểm có nằm trong vùng không; biên được tính là trong."""
        return haversine_m(lat, lon, self.lat, self.lon) <= self.radius_m


@dataclass(frozen=True)
class CongestionRule:
    """Một luật ùn tắc: cạnh có trung điểm trong `zone` (và đúng loại đường, nếu có) chịu `alpha`."""

    zone: CongestionZone
    alpha: float
    highway: tuple[str, ...] | None = None   # None = mọi loại đường

    def __post_init__(self) -> None:
        # alpha ≥ 1 giữ heuristic A* đúng (DATA_MODEL 4.1 điểm 4 và 5.2).
        if not (_finite(self.alpha) and self.alpha >= 1.0):
            raise ValueError(
                f"alpha = {self.alpha!r} phải hữu hạn và ≥ 1; "
                "alpha < 1 nghĩa là đường nhanh hơn cơ sở, heuristic A* sẽ không còn đúng")
        if self.highway is not None:
            if isinstance(self.highway, str) or not all(isinstance(h, str) for h in self.highway):
                raise ValueError("highway phải là danh sách tên loại đường, ví dụ ['primary']")
            object.__setattr__(self, "highway", tuple(self.highway))

    def applies_to(self, highway: str | None) -> bool:
        """Luật có áp cho cạnh loại `highway` không."""
        if self.highway is None:
            return True
        return highway is not None and highway in self.highway


@dataclass(frozen=True)
class Scenario:
    """Kịch bản ùn tắc: danh sách luật; `rules` rỗng nghĩa là cơ sở (mọi hệ số bằng 1)."""

    id: str
    label: str = ""
    rules: tuple[CongestionRule, ...] = ()

    def __post_init__(self) -> None:
        if not (isinstance(self.id, str) and self.id.strip()):
            raise ValueError("id kịch bản không được rỗng")
        object.__setattr__(self, "rules", tuple(self.rules))
        for rule in self.rules:
            if not isinstance(rule, CongestionRule):
                raise ValueError(f"luật ùn tắc phải là CongestionRule, nhận {type(rule).__name__}")


def zone_from_dict(data: dict, *, where: str = "vùng") -> CongestionZone:
    """Dựng `CongestionZone` từ object JSON `{"type": "circle", "lat", "lon", "radius_m"}`."""
    if not isinstance(data, dict):
        raise ValueError(f"{where}: phải là object JSON")
    return CongestionZone(
        lat=_number(data.get("lat"), f"{where}.lat"),
        lon=_number(data.get("lon"), f"{where}.lon"),
        radius_m=_number(data.get("radius_m"), f"{where}.radius_m"),
        type=data.get("type", "circle"),
    )


def rule_from_dict(data: dict, *, where: str = "luật") -> CongestionRule:
    """Dựng `CongestionRule` từ object JSON `{"zone": {...}, "highway": [...], "alpha": 2.0}`."""
    if not isinstance(data, dict):
        raise ValueError(f"{where}: phải là object JSON")
    if "zone" not in data:
        raise ValueError(f"{where}: thiếu 'zone'")
    highway = data.get("highway")
    if highway is not None and not isinstance(highway, list):
        raise ValueError(f"{where}.highway phải là danh sách tên loại đường")
    return CongestionRule(
        zone=zone_from_dict(data["zone"], where=f"{where}.zone"),
        alpha=_number(data.get("alpha"), f"{where}.alpha"),
        highway=tuple(highway) if highway is not None else None,
    )


def scenario_from_dict(data: dict, *, where: str = "kịch bản") -> Scenario:
    """Dựng `Scenario` từ object JSON `{"id", "label", "rules"}`."""
    if not isinstance(data, dict):
        raise ValueError(f"{where}: phải là object JSON")
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError(f"{where}.rules phải là danh sách")
    return Scenario(
        id=data.get("id"),
        label=data.get("label", ""),
        rules=tuple(rule_from_dict(r, where=f"{where}.rules[{i}]") for i, r in enumerate(rules)),
    )


def load_scenarios(path: str | Path) -> dict[str, Scenario]:
    """Đọc file `saigo-scenarios/1`; trả dict id → `Scenario`, giữ thứ tự trong file.

    File phải có kịch bản `baseline` (luật rỗng) để nơi gọi luôn có mốc so sánh.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format") != SCENARIO_FORMAT:
        raise ValueError(f"format phải là {SCENARIO_FORMAT!r}, file có {data.get('format')!r}")
    items = data.get("scenarios")
    if not isinstance(items, list) or not items:
        raise ValueError("file kịch bản phải có danh sách 'scenarios' không rỗng")
    scenarios: dict[str, Scenario] = {}
    for i, item in enumerate(items):
        scenario = scenario_from_dict(item, where=f"scenarios[{i}]")
        if scenario.id in scenarios:
            raise ValueError(f"scenarios[{i}]: id {scenario.id!r} bị trùng")
        scenarios[scenario.id] = scenario
    if "baseline" not in scenarios:
        raise ValueError("file kịch bản phải có kịch bản 'baseline'")
    return scenarios


def edge_multipliers(graph: Graph, meta: GraphMeta, scenario: Scenario) -> list[float]:
    """Hệ số `multiplier[e]` theo DATA_MODEL 4.1: mặc định 1, bằng `max(alpha)` của các luật khớp.

    Cạnh khớp luật khi trung điểm **dọc theo hình học** (50% chiều dài polyline, hàm
    `geo.polyline_midpoint`) nằm trong vùng, và loại đường của cạnh khớp danh sách của luật.
    """
    multipliers = [1.0] * len(graph.edge_u)
    if not scenario.rules:
        return multipliers
    for e, geometry in enumerate(meta.edge_geometry):
        lat, lon = polyline_midpoint(geometry)
        best = 1.0
        for rule in scenario.rules:
            if rule.applies_to(meta.edge_highway[e]) and rule.zone.contains(lat, lon):
                best = max(best, rule.alpha)   # max, không phải tích: hai vùng chồng nhau mô tả cùng chỗ tắc
        multipliers[e] = best
    return multipliers


def build_snapshot(graph: Graph, meta: GraphMeta, scenario: Scenario,
                   blocked: Iterable[int] = frozenset()) -> Snapshot:
    """Snapshot cho một request: `weights[e] = base_time_s(e) × multiplier(e)`, cạnh đóng thành vô cực.

    Chỉ đọc `graph` và `meta`, không sửa gì trong đồ thị gốc.
    """
    multipliers = edge_multipliers(graph, meta, scenario)
    weights = [t * a for t, a in zip(graph.edge_base_time_s, multipliers)]
    return make_snapshot(graph, weights, frozenset(blocked), scenario_id=scenario.id)

