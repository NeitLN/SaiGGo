"""Dịch vụ định tuyến, snap tọa độ và ghép hình học tuyến đường (docs/ARCHITECTURE.md mục 4.1, 5)."""

from __future__ import annotations

import time

from app.algorithms.astar import astar
from app.algorithms.dijkstra import dijkstra
from app.algorithms.heuristics import make_geo_heuristic
from app.algorithms.result import SearchResult
from app.api.schemas import (
    AlgorithmRouteResult,
    GeometryLineString,
    RouteRequest,
    RouteResponse,
    SnappedPoint,
    SnappedResponse,
)
from app.graph.geo import haversine_m
from app.graph.model import Graph, GraphMeta
from app.graph.scenario import Snapshot, baseline_snapshot


def nearest_node_naive(graph: Graph, meta: GraphMeta, lat: float, lon: float) -> tuple[int, float]:
    """Tìm node gần nhất duyệt tuyến tính, chỉ xét node thuộc SCC lớn nhất (T13 skeleton)."""
    n = len(graph.node_lat)
    if n == 0:
        raise ValueError("đồ thị không có node nào")

    # Chỉ xét các node thuộc SCC lớn nhất theo quy định
    candidates = [i for i in range(n) if meta.node_in_scc[i]]
    if not candidates:
        candidates = list(range(n))

    best_node = candidates[0]
    best_dist = haversine_m(lat, lon, graph.node_lat[best_node], graph.node_lon[best_node])

    for i in candidates[1:]:
        dist = haversine_m(lat, lon, graph.node_lat[i], graph.node_lon[i])
        if dist < best_dist:
            best_dist = dist
            best_node = i

    return best_node, round(best_dist, 2)


def build_geometry(
    graph: Graph,
    meta: GraphMeta,
    source_node: int,
    edge_ids: list[int],
    status: str,
) -> GeometryLineString:
    """Tạo GeoJSON LineString từ danh sách cạnh đã đi, tọa độ [lon, lat]."""
    if status != "ok":
        return GeometryLineString(type="LineString", coordinates=[])

    if not edge_ids:
        # Trường hợp source == target (không qua cạnh nào)
        return GeometryLineString(
            type="LineString",
            coordinates=[[graph.node_lon[source_node], graph.node_lat[source_node]]],
        )

    coords: list[list[float]] = []
    for idx, e in enumerate(edge_ids):
        geom = meta.edge_geometry[e]
        if not geom:
            u, v = graph.edge_u[e], graph.edge_v[e]
            geom = [
                [graph.node_lon[u], graph.node_lat[u]],
                [graph.node_lon[v], graph.node_lat[v]],
            ]
        if idx == 0:
            coords.extend(geom)
        else:
            if coords and geom and coords[-1] == geom[0]:
                coords.extend(geom[1:])
            else:
                coords.extend(geom)

    return GeometryLineString(type="LineString", coordinates=coords)


def _run_algorithm(
    algo: str,
    graph: Graph,
    snap: Snapshot,
    s_node: int,
    t_node: int,
    trace_limit: int,
) -> tuple[SearchResult, float]:
    """Chạy thuật toán và đo thời gian thực thi (ms) bằng perf_counter_ns."""
    if algo == "dijkstra":
        t0 = time.perf_counter_ns()
        res = dijkstra(graph, snap, s_node, t_node, trace_limit=trace_limit)
        t1 = time.perf_counter_ns()
    else:  # astar (RouteRequest schema đã đảm bảo chỉ có "dijkstra" hoặc "astar")
        t0 = time.perf_counter_ns()
        h = make_geo_heuristic(graph, t_node)
        res = astar(graph, snap, s_node, t_node, h, trace_limit=trace_limit)
        t1 = time.perf_counter_ns()

    runtime_ms = (t1 - t0) / 1_000_000.0
    return res, round(runtime_ms, 3)


def route(
    graph: Graph,
    meta: GraphMeta,
    req: RouteRequest,
) -> RouteResponse:
    """Xử lý yêu cầu tìm đường theo contract v1."""
    # 1. Snap điểm đầu và điểm cuối về node gần nhất trong SCC
    s_node, s_dist = nearest_node_naive(graph, meta, req.source.lat, req.source.lon)
    t_node, t_dist = nearest_node_naive(graph, meta, req.target.lat, req.target.lon)

    snapped = SnappedResponse(
        source=SnappedPoint(
            node_id=s_node,
            lat=graph.node_lat[s_node],
            lon=graph.node_lon[s_node],
            snap_distance_m=s_dist,
        ),
        target=SnappedPoint(
            node_id=t_node,
            lat=graph.node_lat[t_node],
            lon=graph.node_lon[t_node],
            snap_distance_m=t_dist,
        ),
    )

    # 2. Xây snapshot cơ sở (skeleton chỉ chạy baseline)
    snap = baseline_snapshot(graph)

    # 3. Đo lường và chạy các thuật toán được yêu cầu
    results: dict[str, AlgorithmRouteResult] = {}

    for algo in req.algorithms:
        res, runtime_ms = _run_algorithm(algo, graph, snap, s_node, t_node, req.trace_limit)
        geom = build_geometry(graph, meta, s_node, res.edge_ids, res.status)
        trace_coords = [[graph.node_lon[nid], graph.node_lat[nid]] for nid in res.trace]

        results[algo] = AlgorithmRouteResult(
            status=res.status,
            cost_s=res.cost_s,
            distance_m=res.distance_m,
            edge_ids=res.edge_ids,
            geometry=geom,
            expanded=res.expanded,
            runtime_ms=runtime_ms,
            trace=trace_coords,
            trace_truncated=res.trace_truncated,
        )

    # 4. Kiểm tra costs_match khi có cả Dijkstra và A*
    costs_match = None
    if "dijkstra" in results and "astar" in results:
        res_d = results["dijkstra"]
        res_a = results["astar"]
        if res_d.status == "ok" and res_a.status == "ok":
            cd = res_d.cost_s
            ca = res_a.cost_s
            if cd is not None and ca is not None:
                costs_match = abs(cd - ca) <= 1e-6 * max(1.0, cd)
        elif res_d.status == "no_path" and res_a.status == "no_path":
            costs_match = True
        else:
            costs_match = False

    return RouteResponse(
        dataset_id=graph.dataset_id,
        snapshot_id=snap.snapshot_id,
        snapped=snapped,
        results=results,
        costs_match=costs_match,
        warnings=[],
    )
