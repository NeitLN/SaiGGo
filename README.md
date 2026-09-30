# SaiGo

**Delivery Route Planning on Ho Chi Minh City Street Networks Using Heuristic Search**
Lập kế hoạch lộ trình giao hàng trên mạng đường TP.HCM bằng tìm kiếm heuristic.

Đồ án môn Introduction to AI (261_72ITSE30303_01) — Nhóm 4: Võ Việt Tiến, Bùi Duy Anh, Đỗ Quốc Bảo, Võ Hoàng Minh.

> **Trạng thái:** khung dự án. Chưa có thuật toán, dataset hay kết quả thực nghiệm.

SaiGo dùng **mạng đường thực** từ OpenStreetMap, nhưng **thời gian di chuyển và giao thông là mô phỏng**.
Không cung cấp ETA giao thông trực tiếp hay điều hướng thương mại.

## Phạm vi

- Tìm đường: Dijkstra và A* (tự cài đặt)
- Thứ tự giao: thứ tự nhập → Nearest Neighbor → 2-opt trên ma trận chi phí có hướng
- Kịch bản giao thông mô phỏng và chặn đường, lập lại lộ trình
- Benchmark offline có thể tái lập

Đặc tả đầy đủ: [docs/TOPIC.md](docs/TOPIC.md).

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `backend/app/api/` | Endpoint FastAPI và schema |
| `backend/app/services/` | Điều phối route/tour/snapshot |
| `backend/app/algorithms/` | Dijkstra, A*, NN, 2-opt |
| `backend/app/graph/` | Adapter, geometry, snap, manifest |
| `frontend/` | TypeScript + Vite + Leaflet |
| `scripts/` | Chuẩn bị dữ liệu, benchmark, vẽ biểu đồ |
| `tests/` | pytest |
| `data/config/`, `data/demo/` | Cấu hình và case demo |
| `results/` | Kết quả benchmark |
| `docs/` | Đề tài, thuật toán, thực nghiệm, demo |

## Chạy local (Windows)

Yêu cầu: Python 3.11+, Node.js 20+.

```powershell
# Backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --app-dir backend

# Frontend (terminal khác)
cd frontend
npm install
npm run dev
```

Mở http://localhost:5173. Frontend gọi backend qua proxy `/api` → `http://127.0.0.1:8000`.

Chạy test:

```powershell
pytest -q
```

Công cụ tải dữ liệu OSM: `pip install -e ".[data]"`.

## Dữ liệu và giấy phép

Dữ liệu đường phố © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), giấy phép ODbL.
Giấy phép mã nguồn chưa chọn; giấy phép mã nguồn không bao phủ dataset.
