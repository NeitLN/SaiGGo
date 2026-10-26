"""Khởi tạo ứng dụng FastAPI và nạp đồ thị lúc khởi động (docs/ARCHITECTURE.md mục 4.1)."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI

from app.api.routes import router
from app.graph.model import load_graph

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_graph_path() -> Path:
    """Lấy đường dẫn file đồ thị từ biến môi trường SAIGO_GRAPH hoặc mặc định tests/fixtures/mini.json."""
    raw = os.environ.get("SAIGO_GRAPH", "tests/fixtures/mini.json")
    p = Path(raw)
    if not p.is_absolute():
        if (REPO_ROOT / p).is_file():
            return REPO_ROOT / p
    return p


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan nạp đồ thị khi server khởi động; lỗi nạp file sẽ dừng server (fail-fast)."""
    path = get_graph_path()
    if not path.is_file():
        raise RuntimeError(f"Không tìm thấy file đồ thị tại: {path}")

    try:
        graph, meta = load_graph(path)
    except Exception as err:
        raise RuntimeError(f"Lỗi khi nạp file đồ thị tại {path}: {err}") from err

    app.state.graph = graph
    app.state.meta = meta
    app.state.dataset_id = graph.dataset_id
    app.state.dataset_loaded = True

    yield


app = FastAPI(title="SaiGo API", version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api")
