# T13 — Skeleton phía API: `/api/route` tối giản trên `mini.json`

Tuần mục tiêu: 2 (28–29/10; **đường mỏng chạy được trước tối 28/10**) · Giao cho: Tiến · Nhánh: `t13-api-skeleton` · Issue: [#49](https://github.com/NeitLN/SaiGGo/issues/49)
Review: Minh (đối chiếu contract với phía UI) · Người tích hợp: Tiến
Phụ thuộc: T11 (**tích hợp**) · T10 (**tích hợp**: tạm dùng hàm nội bộ, đổi sang `geo.haversine_m` khi T10 merge) · Ước lượng: 3 giờ

## Mục tiêu
API thật, mỏng nhất, trả tuyến Dijkstra theo đúng **contract v1** ([ARCHITECTURE](../ARCHITECTURE.md) mục 4.1).

## Việc cần làm
1. **`main.py`:** nạp đồ thị khi khởi động từ biến môi trường `SAIGO_GRAPH` (mặc định `tests/fixtures/mini.json`); `/api/health` trả `dataset_loaded: true` và `dataset_id`.
2. **`services/routing.py`:**
   - `nearest_node_naive(graph, lat, lon) -> (node_id, snap_distance_m)`: duyệt tuyến tính, chưa giới hạn 150 m, chỉ xét node `in_scc`. **Đúng tên hàm này**: T50 (tuần 3) thay bằng bản có ngưỡng.
   - `route(graph, meta, req) -> dict`: snap → `baseline_snapshot` → đo `perf_counter_ns` quanh `dijkstra()` → gắn geometry `[lon, lat]` từ `GraphMeta`.
3. **`api/schemas.py`** + **`api/routes.py`:** `POST /api/route` theo contract v1; lỗi đầu vào trả 422.
4. **`tests/test_api_route.py`** (TestClient + `mini.json`):
   - bấm gần S, gần T → `cost_s = 80`;
   - đảo lại → `cost_s = 100`;
   - geometry bắt đầu ở S và kết thúc ở T;
   - thiếu `source` → 422.

## Sở hữu (chỉ task này được tạo/sửa) trong tuần 2
- `backend/app/main.py`
- `backend/app/api/*`
- `backend/app/services/routing.py`
- `tests/test_api_route.py`, `tests/test_health.py`

## Dùng (chỉ đọc)
- `graph/model.py` (T01), `algorithms/*` (T11)
- Contract v1

## Tiêu chí chấp nhận
- [ ] **28/10 tối:** chạy backend + frontend của T14 trên máy Tiến, bấm 2 điểm ra tuyến (test có thể chưa đủ)
- [ ] **29/10:** `pytest tests/test_api_route.py tests/test_health.py -q` → PASS; mọi trường trong contract v1 đều có trong response
- [ ] Minh xác nhận response khớp kiểu dữ liệu trong `frontend/src/api.ts`

## Ngoài phạm vi
A* trong API (sau T20); snap có ngưỡng (T50); `/api/dataset` và `/api/network` (tuần 3).
