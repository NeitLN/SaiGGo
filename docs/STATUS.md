# STATUS
Cập nhật: 26/10/2026 (đầu tuần 2) · Người tích hợp: Tiến · Đọc file này đầu mỗi session; giữ ≤ 100 dòng, ghi đè mỗi cuối session.

Bộ nhớ dự án: mục tiêu/phạm vi/deadline ở [PROJECT_BRIEF.md](PROJECT_BRIEF.md) · quyết định kỹ thuật ở [ARCHITECTURE.md](ARCHITECTURE.md) và [DATA_MODEL.md](DATA_MODEL.md) · mốc, quyết định đắt nếu đổi, kế hoạch tuần ở [ROADMAP.md](ROADMAP.md) · từng task ở [TASKS.md](TASKS.md) + GitHub Issues · bằng chứng chi tiết và lỗi tồn tại ở [PROGRESS.md](PROGRESS.md).

## Tóm tắt
- **Hiện tại:** trên `main` đã có bộ nạp đồ thị + fixture `mini.json` (T01), hàm địa lý (T10), Dijkstra + `SearchResult` + `Snapshot` (T11), đáp án tính tay (T03). API mới có `/api/health`; frontend còn trống; chưa có A*, dữ liệu thật đã nạp hay số đo benchmark.
- **Mong muốn:** walking skeleton chạy trên 2 máy trước 29/10; **điểm kiểm bằng chứng 05/11**; MVP tích hợp 08/11 (có điều kiện); final 12/11.
- **Phải giữ nguyên:**
  - `main` chỉ nhận PR có review + CI xanh;
  - commit chỉ mang tên thành viên nhóm (job `identity`, sau khi #60 merge);
  - dữ liệu thô đóng băng theo sha256;
  - contract `/api/route` v1 chỉ được thêm trường;
  - không số liệu nào chưa đo.
- **Chưa biết:** Duy Anh quay lại khi nào (hạn báo 01/11); máy thứ hai build lại dữ liệu có ra cùng sha256 không; Python chạy đồ thị lớn nhất mất bao lâu.

## Đang ở đâu
- Mốc: M1 có Dijkstra, còn CLI (T12). MW và A* (T20) bắt đầu tuần này.
- Đã tích hợp vào `main`: T-PLAN (#1), T04, T05, T06 (#52), **T03 (#54), T01 (#57), T11 (#59), T10 (#58)**.
- **26/10, lịch sử `main` đã được viết lại** để bỏ 2 dòng đồng tác giả ngoài nhóm. Ai clone trước đó: `git fetch origin; git switch main; git reset --hard origin/main`.
- Chờ review / merge:
  - #55 T00: đã approve, chờ merge.
  - #60 kiểm danh tính commit: đã approve; Tiến sửa regex theo góp ý của Bảo nên cần approve lại.
  - #56 kế hoạch tuần 2: **nội dung đã duyệt 26/10**, đã sửa theo góp ý của Bảo, chờ Bảo approve.
  - **Minh:** #46 → #47 → #53 đủ approve, chưa merge. Trước khi merge #53 phải sửa `test_load_graph_reads_file` thành `g, _ = model.load_graph(...)` ([T34](tasks/T34-release-data.md)).
- Phân công tuần 2 đã duyệt: Tiến T20 + kiểm thứ tự ID cạnh + tích hợp; Minh T34, T14, **T13**; Bảo T15, **T12**, T21 (dự phòng). Chi tiết: [ROADMAP](ROADMAP.md) mục 6.

## Bị chặn / rủi ro
- `outer.graphml` (sha256 `24a28327…`) chỉ có trên máy Minh. Tải lại ngày 25/10 đã ra số khác (12.130 so với 12.131 node), nên chưa ai tái lập được dữ liệu cho tới khi Minh đưa file lên Release (T34). Tiêu chí dữ liệu thật của T01 chờ việc này.
- Minh dùng Python 3.14 (networkx 3.7); nhóm chuẩn là 3.11 (networkx 3.6.1). Benchmark chỉ chạy trên 3.11.
- Ngân sách tuần 3–4 vẫn thiếu 6–9 giờ dù đã chọn S1; phần nghiên cứu sẽ cắt chọn ở buổi họp 01/11.
- Tài liệu ngoài tuần 2 chưa đồng bộ với quyết định phạm vi 26/10 (xem mục cuối).

## Quyết định
| Quyết định | Trạng thái | Nguồn |
|---|---|---|
| Thêm walking skeleton MW (T13–T15) trước 29/10; T51/T52 mở rộng trên code skeleton | **Đã duyệt** | Tiến, 25/10 |
| Contract `/api/route` v1 ([ARCHITECTURE](ARCHITECTURE.md) mục 4.1) | **Đã chốt** (kỹ thuật, Tiến ủy quyền); Minh xác nhận khi bắt đầu T14 | 25/10 |
| Khóa phiên bản (`requirements-lock.txt`, Python 3.11) + job `audit` không bắt buộc + `setup_dev` nâng setuptools | **Đã duyệt** (Tiến ủy quyền phần hàng rào) | 25/10 |
| Dependabot | **Hoãn**: tránh thêm PR khi hàng chờ review đã đầy; xem lại sau M6 | 25/10 |
| T01, T10, T11, T20 chuyển từ Duy Anh sang Tiến | **Đã chốt**; T01, T10, T11 đã merge | Tiến, 26/10 |
| Kế hoạch tuần 2 ([ROADMAP](ROADMAP.md) mục 6): T13 → Minh, T12 → Bảo, T21 → Bảo (dự phòng) | **Đã duyệt** | Nhóm, 26/10 (theo xác nhận của Tiến) |
| Đổi phạm vi ([đề xuất](proposals/2026-10-26-pham-vi.md)): cắt tour và T32, RQ1b 3 kích thước fixed trips, bản đồ rút gọn, điểm kiểm 05/11 + MVP 08/11; nhân lực S1 | **Đã duyệt**; chưa đồng bộ tài liệu/GitHub; chưa báo giảng viên | Nhóm, 26/10 (theo xác nhận của Tiến) |
| Q1–Q5, Q7 ([agenda](team/meetings/2026-10-26-agenda.md)): `in_scc`, Release dữ liệu thô, vùng demo 2 km, `speeds.json` đóng băng, luật ùn tắc/đóng đường, máy benchmark | **Đã duyệt**; Q2 còn chờ Release (T34) | Nhóm, 26/10 |
| Ngưỡng snap 150 m (PROJECT_BRIEF mục 5) | **[Đề xuất]**, giả định hiện hành; agenda không chốt riêng | — |
| Khoản cắt 4 (đóng đường qua API/CLI) và 5 (RQ1b còn 2 kích thước) | **Chưa kích hoạt**; cần nhóm đồng ý riêng | — |

## Bước tiếp theo
1. Bảo approve lại #56 và #60 (sau khi sửa regex); Tiến merge #55, #56, #60, rồi đưa `identity` vào check bắt buộc.
2. Bảo đăng issue *Biên bản họp* ghi nhận quyết định 26/10.
3. Minh: T34 (sửa test trong #53, merge #46 → #47 → #53, tạo Release), rồi T14, T13.
4. Tiến: PR nhỏ kiểm thứ tự ID cạnh trong `load_graph` → T20; PR đồng bộ phạm vi ([ROADMAP](ROADMAP.md) mục 6.6), **chỉ chạy `create_backlog.py --sync` sau khi TASKS và `schedule.csv` đã khớp**; gửi thư báo giảng viên.
5. Bảo: T15 (29/10), T12 (30–31/10).

## Bộ kiểm nhanh (chạy đầu mỗi session)
- `.venv\Scripts\python.exe -m pytest -q` → tại `main` `44320c8` (26/10): 50 passed, 1 skipped (test `realdata`, chưa có dữ liệu)
- `cd frontend; npm run build` → build được
- `python scripts/tracking/create_backlog.py --dry-run` → không lỗi, in tổng số task/giờ
- Mỗi tuần: `.venv\Scripts\python.exe -m pip_audit -r requirements-lock.txt` · `cd frontend; npm audit` (job `audit` trong CI làm việc này ở mỗi PR)

## Lệnh khác
- Dựng môi trường: `powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1` (thêm `-Data` cho OSMnx)
- Chạy: `uvicorn app.main:app --reload --app-dir backend` + `cd frontend; npm run dev`
- Burndown: `python scripts/tracking/burndown.py --out build/tracking`
- Đồng bộ backlog: `create_backlog.py --sync`, `setup_project.py --sync`

## Tài liệu lệch với code / với quyết định
- [ARCHITECTURE.md](ARCHITECTURE.md) mục 3 và 4 mô tả file/API **dự kiến**. Code hiện có `graph/model.py`, `graph/geo.py`, `graph/scenario.py`, `algorithms/result.py`, `algorithms/dijkstra.py`; API mới có `/api/health`.
- ROADMAP mục 1–5, TASKS phần ngoài tuần 2, PROJECT_BRIEF, EXPERIMENT_PLAN, DEMO, PROGRESS (bảng trạng thái) **chưa đồng bộ** với quyết định phạm vi 26/10; PR đồng bộ theo sau #56. Khi lệch, [đề xuất phạm vi](proposals/2026-10-26-pham-vi.md) được ưu tiên.
