"""Định tuyến các endpoint API của SaiGo (docs/ARCHITECTURE.md mục 4)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import HealthResponse, RouteRequest, RouteResponse
from app.graph.model import Graph, GraphMeta
from app.services.routing import route

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    """Kiểm tra trạng thái server và đồ thị đã nạp."""
    dataset_loaded = getattr(request.app.state, "dataset_loaded", False)
    dataset_id = getattr(request.app.state, "dataset_id", None)
    return HealthResponse(
        status="ok",
        dataset_loaded=dataset_loaded,
        dataset_id=dataset_id,
    )


@router.post("/route", response_model=RouteResponse)
def compute_route(req: RouteRequest, request: Request) -> RouteResponse:
    """Tìm đường giữa hai điểm theo contract v1."""
    graph: Graph | None = getattr(request.app.state, "graph", None)
    meta: GraphMeta | None = getattr(request.app.state, "meta", None)
    if graph is None or meta is None:
        raise HTTPException(
            status_code=503,
            detail="Chưa nạp đồ thị (dataset not loaded)",
        )
    return route(graph, meta, req)
