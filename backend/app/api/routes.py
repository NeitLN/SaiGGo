from fastapi import APIRouter

from app.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Chưa có pipeline dữ liệu; cập nhật khi graph được nạp lúc khởi động.
    return HealthResponse(status="ok", dataset_loaded=False)
