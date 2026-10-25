"""Snapshot: trọng số cạnh cho đúng một lần tìm kiếm (docs/DATA_MODEL.md mục 4.3).

Đồ thị gốc không bao giờ bị sửa; ùn tắc và đóng đường chỉ nằm trong snapshot.
T40 thêm `Scenario` (luật ùn tắc theo vùng) và `build_snapshot` vào file này,
dùng lại đúng kiểu `Snapshot` dưới đây.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from app.graph.model import Graph


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
