# STATUS
Cập nhật: 25/10/2026, 23:50 (cuối tuần 1) · Người tích hợp: Tiến · Đọc file này đầu mỗi session; giữ ≤ 100 dòng, ghi đè mỗi cuối session.

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
- Mốc: M0 gần xong (T01 chờ review); MW, M1–M2 đang làm.
- Đã tích hợp vào `main`: T-PLAN (#1), T04 (#42), T05 (#44), **T06 (#48, PR #52, Bảo merge 26/10)**.
- Chờ review / merge:
  - **Tiến, đã kiểm, chờ người khác review:**
    - #57 T01: 17 test PASS;
    - #58 T10: 13 test PASS;
    - #59 T11: 13 test PASS, khớp 6/6 tình huống tính tay và NetworkX; xếp chồng trên #57;
    - #55 T00;
    - #56 kế hoạch tuần 2 (draft, chờ họp).
  - **Minh:** #46 → #47 → #53 đủ approve, chờ Minh merge (#53 đang xung đột, cần cập nhật sau #47).
  - **Bảo:** #54 T03 đã được Tiến approve, chờ Bảo merge.
- T01, T10, T11, T20 đã chuyển từ Duy Anh sang Tiến (26/10).

## Bị chặn / rủi ro
- `outer.graphml` (sha256 `24a28327…`) chỉ có trên máy Minh. Tải lại ngày 25/10 đã ra số khác (12.130 so với 12.131 node), nên chưa ai tái lập được dữ liệu cho tới khi Minh đưa file lên Release.
- Thứ tự merge còn lại: #46 → #47 → #53 (PR xếp chồng), rồi #52 và #55. Có thể xung đột nhẹ ở `docs/PROGRESS.md`; sửa thì giữ nội dung của cả hai bên.
- Minh dùng Python 3.14 (networkx 3.7); nhóm chuẩn là 3.11 (networkx 3.6.1). Benchmark chỉ chạy trên 3.11.

## Quyết định
| Quyết định | Trạng thái | Nguồn |
|---|---|---|
| Thêm walking skeleton MW (T13–T15) trước 29/10; T51/T52 mở rộng trên code skeleton | **Đã duyệt** | Tiến, 25/10 |
| Contract `/api/route` v1 ([ARCHITECTURE](ARCHITECTURE.md) mục 4.1) | **Đã chốt** (kỹ thuật, Tiến ủy quyền); Minh xác nhận khi bắt đầu T14 | 25/10 |
| Khóa phiên bản (`requirements-lock.txt`, Python 3.11) + job `audit` không bắt buộc + `setup_dev` nâng setuptools | **Đã duyệt** (Tiến ủy quyền phần hàng rào) | 25/10 |
| Dependabot | **Hoãn**: tránh thêm PR khi hàng chờ review đã đầy; xem lại sau M6 | 25/10 |
| T01, T10, T11, T20 chuyển từ Duy Anh sang Tiến (giữ hạn gốc để thấy T01, T10 trễ) | **Đã chốt**, đã đổi trên GitHub | Tiến, 26/10 |
| Phần còn lại của kế hoạch tuần 2, gồm giảm tải cho Tiến (đang 20/15 giờ; đề xuất T13 → Minh) — [ROADMAP](ROADMAP.md) mục 6 + phiếu [tasks/](tasks/) | **Chờ nhóm duyệt** ở buổi họp 26/10 ([agenda](team/meetings/2026-10-26-agenda.md)) | — |
| Đổi phạm vi: cắt tour, RQ1b 3 kích thước fixed trips, bản đồ rút gọn, điểm kiểm 05/11 + MVP 08/11 ([đề xuất](proposals/2026-10-26-pham-vi.md)) | **Chờ nhóm duyệt**; tuần 3–4 thiếu 20–23 giờ nếu không đổi | — |
| Vùng demo 2 km, `speeds.json`, ngưỡng snap 150 m (Q3, Q4, PROJECT_BRIEF mục 5) | **[Đề xuất]**, chờ nhóm xác nhận ở buổi họp | — |

## Bước tiếp theo
1. Minh hoặc Bảo approve lại #52; Duy Anh, Minh hoặc Bảo approve #55. Merge cả hai.
2. Minh: đưa `outer.graphml` lên Release `data-raw-20261024`, merge #46 → #47 → #53.
3. Duy Anh vắng tuần 2: Tiến đã nhận T01, T10, T11, T20 (26/10); Tiến review #54. **Không chạy `create_backlog.py --sync` từ `main`** trước khi #56 merge, nếu không người được giao sẽ bị đổi ngược về Duy Anh.
4. Họp tối 26/10 theo [agenda](team/meetings/2026-10-26-agenda.md): 3 quyết định phạm vi + Q1–Q5, Q7; sau họp cập nhật TASKS/schedule/GitHub và gửi thư giảng viên nếu cắt tour.
5. Sau khi merge #52: `create_backlog.py --sync` + `setup_project.py --sync` (T51/T52 nhận phụ thuộc T13/T14).

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
