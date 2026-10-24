# STATUS
Cập nhật: 25/10/2026 (cuối tuần 1) · Người tích hợp: Tiến · Đọc file này đầu mỗi session; giữ ≤ 100 dòng, ghi đè mỗi cuối session.

Bộ nhớ dự án: mục tiêu/phạm vi/deadline ở [PROJECT_BRIEF.md](PROJECT_BRIEF.md) · quyết định kỹ thuật ở [ARCHITECTURE.md](ARCHITECTURE.md) và [DATA_MODEL.md](DATA_MODEL.md) · mốc, quyết định đắt nếu đổi, kế hoạch tuần ở [ROADMAP.md](ROADMAP.md) · từng task ở [TASKS.md](TASKS.md) + GitHub Issues · bằng chứng chi tiết và lỗi tồn tại ở [PROGRESS.md](PROGRESS.md).

## Tóm tắt
- **Hiện tại:** khung FastAPI (`/api/health`) + Vite/Leaflet trống; chưa có thuật toán, dữ liệu đã nạp hay kết quả. Hệ thống theo dõi (issue, Project, burndown, branch protection) đã chạy.
- **Mong muốn:** walking skeleton chạy trên 2 máy trước 29/10; MVP (Dijkstra/A* trên mạng đường thật, ùn tắc/đóng đường, benchmark tăng quy mô) trước 05/11; final 12/11.
- **Phải giữ nguyên:**
  - `main` chỉ nhận PR có review + CI xanh;
  - dữ liệu thô đóng băng theo sha256;
  - contract `/api/route` v1 chỉ được thêm trường;
  - không số liệu nào chưa đo.
- **Chưa biết:** app chạy trên máy của Duy Anh và Bảo chưa; Leaflet vẽ ~28k cạnh có mượt không; Python chạy đồ thị lớn nhất mất bao lâu.

## Đang ở đâu
- Mốc: M0 (hạn 24/10) **chưa xong**; MW (skeleton), M1–M3 làm trong tuần 2.
- Đã tích hợp vào `main`: T-PLAN (#1), T04 (#42, PR #43). Bằng chứng: CI xanh; workflow Tracking chạy sau merge, `daily.csv` có ngày 23/10.
- Đã kiểm, chờ merge (đủ approve, CI xanh):
  - PR #45: T05, hướng dẫn bắt đầu.
  - PR #46: T02, Minh. `--smoke` PASS trên Python 3.11.9 và 3.14.4, ra cùng số.
  - PR #47: T30, Minh. Đã tải 12.131 node / 27.693 cạnh, sha256 `24a28327…`.
  - PR #52: T06, bộ nhớ dự án + hàng rào. CI 3 job PASS ở `f57d319`; job `audit` đã bắt và sửa lỗ hổng `vite` 8.3.1 → 8.3.5.
- Đang dở: T00 (#2), còn mở trang web + PR.
- **Trễ hạn 24/10, chưa có hoạt động:**
  - T01 (#3, Duy Anh): chặn T11, nên chặn cả skeleton.
  - T03 (#5, Bảo): chỉ chặn khâu chấp nhận của T11.

## Bị chặn / rủi ro
- `outer.graphml` (13,4 MB) chỉ có trên máy Minh. T31 cần cùng một bản → đưa lên GitHub Release trước khi làm T31.
- Merge #45 → #46 → #47 → T06 sẽ xung đột ở `docs/PROGRESS.md` và `docs/TASKS.md` (các dòng sát nhau). Người tích hợp sửa khi ghép, giữ nội dung của cả hai bên.
- Minh dùng Python 3.14 (networkx 3.7); nhóm chuẩn là 3.11 (networkx 3.6.1). Benchmark chỉ chạy trên 3.11.

## Quyết định
| Quyết định | Trạng thái | Nguồn |
|---|---|---|
| Thêm walking skeleton MW (T13–T15) trước 29/10; T51/T52 mở rộng trên code skeleton | **Đã duyệt** | Tiến, 25/10 |
| Contract `/api/route` v1 ([ARCHITECTURE](ARCHITECTURE.md) mục 4.1) | **Đã chốt** (kỹ thuật, Tiến ủy quyền); Minh xác nhận khi bắt đầu T14 | 25/10 |
| Khóa phiên bản (`requirements-lock.txt`, Python 3.11) + job `audit` không bắt buộc + `setup_dev` nâng setuptools | **Đã duyệt** (Tiến ủy quyền phần hàng rào) | 25/10 |
| Dependabot | **Hoãn**: tránh thêm PR khi hàng chờ review đã đầy; xem lại sau M6 | 25/10 |
| Kế hoạch tuần 2 + mức chặn phụ thuộc ([ROADMAP](ROADMAP.md) mục 6) | **Chờ nhóm duyệt** ở buổi họp | — |
| Vùng demo 2 km, `speeds.json`, ngưỡng snap 150 m (Q3, Q4, PROJECT_BRIEF mục 5) | **[Đề xuất]**, chờ nhóm xác nhận ở buổi họp | — |

## Bước tiếp theo
1. Tiến merge #45, rồi #46 (sửa xung đột PROGRESS), rồi #47 (cập nhật branch sau #46), rồi #52 (T06); sau #52 chạy `create_backlog.py --sync` để T51/T52 có phụ thuộc T13/T14.
2. Họp khởi động ([team/KICKOFF.md](team/KICKOFF.md)): duyệt kế hoạch tuần 2, chốt Q3/Q4; nhắc T01, T03.
3. Minh đưa `outer.graphml` lên Release `data-raw-20261024`, ghi cách tải + kiểm sha256.
4. Sau khi nhóm duyệt kế hoạch tuần 2: cập nhật ⛓ và `schedule.csv`, chạy `create_backlog.py --sync` + `setup_project.py --sync`.

## Bộ kiểm nhanh (chạy đầu mỗi session)
- `.venv\Scripts\python.exe -m pytest -q` → hiện `1 passed`
- `cd frontend; npm run build` → build được
- `python scripts/tracking/create_backlog.py --dry-run` → không lỗi, in tổng số task/giờ
- Mỗi tuần: `.venv\Scripts\python.exe -m pip_audit -r requirements-lock.txt` · `cd frontend; npm audit` (job `audit` trong CI làm việc này ở mỗi PR)

## Lệnh khác
- Dựng môi trường: `powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1` (thêm `-Data` cho OSMnx)
- Chạy: `uvicorn app.main:app --reload --app-dir backend` + `cd frontend; npm run dev`
- Burndown: `python scripts/tracking/burndown.py --out build/tracking`
- Đồng bộ backlog: `create_backlog.py --sync`, `setup_project.py --sync`

## Tài liệu lệch với code
- [ARCHITECTURE.md](ARCHITECTURE.md) mục 3 và 4 mô tả file/API **dự kiến**. Code hiện chỉ có `main.py`, `api/routes.py` (`/api/health`), `api/schemas.py`.
