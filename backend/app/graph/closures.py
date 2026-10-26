"""Đóng đường theo cạnh có hướng và nhóm cạnh đối (docs/DATA_MODEL.md mục 4.2).

Một con đường hai chiều là **hai cạnh có hướng** `u → v` và `v → u`. "Đóng đoạn" của UI
đóng cạnh được bấm và cạnh đối của nó: cùng tập `way_ids`, hình học đảo ngược, hai đầu ngược nhau.
Đường hai làn tách riêng (dual carriageway) thường **không** có cạnh đối, nên thao tác này chỉ
đóng đúng đoạn đã bấm, không phải cả con đường.
"""

from __future__ import annotations

from typing import Iterable

from app.graph.model import Graph, GraphMeta

COORD_TOL = 1e-7   # độ, ~1 cm theo vĩ độ: đủ chặt để không ghép nhầm hai đường khác nhau


def _is_reversed(a: list[list[float]], b: list[list[float]], tol: float = COORD_TOL) -> bool:
    """Hình học `b` có đúng là hình học `a` đảo ngược không (cùng số điểm, sai số ≤ `tol`)."""
    if len(a) != len(b):
        return False
    return all(abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol for p, q in zip(a, reversed(b)))


def reverse_twins(graph: Graph, meta: GraphMeta) -> list[int | None]:
    """`twins[e]` = id cạnh đối của `e`, hoặc `None` nếu cạnh một chiều / không có cạnh đối.

    Cạnh đối: `v → u`, cùng tập `way_ids`, hình học đảo ngược (DATA_MODEL 4.2).
    Nếu có nhiều ứng viên (dữ liệu bất thường) thì lấy id nhỏ nhất, để kết quả tất định.
    """
    m = len(graph.edge_u)
    if len(meta.edge_geometry) != m or len(meta.edge_way_ids) != m:
        raise ValueError("meta không khớp đồ thị: số hình học và way_ids phải bằng số cạnh")
    # Gom cạnh theo (u, v, tập way_ids) để chỉ so hình học với ứng viên cùng khoá ngược.
    groups: dict[tuple[int, int, frozenset[int]], list[int]] = {}
    for e in range(m):
        groups.setdefault((graph.edge_u[e], graph.edge_v[e], frozenset(meta.edge_way_ids[e])), []).append(e)

    twins: list[int | None] = [None] * m
    for e in range(m):
        key = (graph.edge_v[e], graph.edge_u[e], frozenset(meta.edge_way_ids[e]))
        for cand in groups.get(key, ()):
            if _is_reversed(meta.edge_geometry[e], meta.edge_geometry[cand]):
                twins[e] = cand
                break
    return twins


def validate_blocked(graph: Graph, edge_ids: Iterable[int]) -> frozenset[int]:
    """Kiểm `blocked_edge_ids` của request; trả tập id đã bỏ trùng, id sai thì `ValueError` (422 ở API)."""
    m = len(graph.edge_u)
    blocked: set[int] = set()
    for e in edge_ids:
        if not (isinstance(e, int) and not isinstance(e, bool) and 0 <= e < m):
            raise ValueError(f"cạnh đóng {e!r} không phải edge id hợp lệ (0..{m - 1})")
        blocked.add(e)
    return frozenset(blocked)


def close_both_ways(graph: Graph, meta: GraphMeta, edge_id: int) -> frozenset[int]:
    """Đóng `edge_id` và cạnh đối của nó (nếu có) — thao tác "đóng đoạn" hai chiều của UI."""
    blocked = validate_blocked(graph, [edge_id])
    twin = reverse_twins(graph, meta)[edge_id]
    return blocked if twin is None else blocked | {twin}
