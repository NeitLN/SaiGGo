# SaiGo — Tiến độ

Cập nhật sau **mỗi** task: trạng thái, bằng chứng (lệnh đã chạy và kết quả), lỗi còn tồn tại. Không đánh dấu "xong" nếu chưa chạy lệnh kiểm tra của task.

Trạng thái công việc theo thời gian thực nằm trên [GitHub Project](https://github.com/users/NeitLN/projects/3) và burndown ở issue [`tracking`](https://github.com/NeitLN/SaiGGo/issues?q=label%3Atracking) (xem [tracking/README.md](tracking/README.md)). File này giữ phần GitHub không thể hiện: **bằng chứng kiểm chứng** và **lỗi còn tồn tại**.

Ký hiệu: ⬜ chưa làm · 🟨 đang làm · ✅ xong và **đã kiểm chứng** · ⚠️ xong nhưng **chưa kiểm chứng** đầy đủ · ❌ bị chặn / bỏ.

## 1. Tổng quan mốc

| Mốc | Hạn đề xuất | Trạng thái | Ghi chú |
|---|---|---|---|
| M0 Nền móng | 24/10 | ⬜ | |
| M1 Dijkstra trên đồ thị mẫu | 26/10 | ⬜ | |
| M2 A* + đối chứng | 28/10 | ⬜ | |
| M3 Dữ liệu thật trên bản đồ | 28/10 | ⬜ | Song song M0–M2 |
| M4 Tìm đường trên dữ liệu thật | 29/10 | ⬜ | |
| M5 Ùn tắc & đóng đường | 31/10 | ⬜ | |
| M6 Bản đồ tương tác | 04/11 | ⬜ | |
| M7 Benchmark & tăng quy mô | 06/11 | ⬜ | |
| G1 Cổng MVP | 05/11 | ⬜ | Quyết định tích hợp tour |
| M8 Tour (E1) | 02/11 · 08/11 | ⬜ | Có điều kiện |
| M9 Hoàn thiện | 12/11 | ⬜ | Freeze 10/11 |

## 2. Trạng thái task

| Task | Issue | Người | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|---|---|
| T-PLAN Kế hoạch + theo dõi | [#1](https://github.com/NeitLN/SaiGGo/issues/1) | Tiến | ✅ | 7 tài liệu kế hoạch, 40 issue, 10 milestone, Project, burndown tự động |
| T04 Sửa hệ thống theo dõi sau review | [#42](https://github.com/NeitLN/SaiGGo/issues/42) | Tiến | 🟨 | PR chờ review; đã chạy thử tại máy (xem nhật ký 24/10) |
| T05 Hướng dẫn bắt đầu cho từng thành viên | [#44](https://github.com/NeitLN/SaiGGo/issues/44) | Tiến | 🟨 | PR chờ review; `setup_dev.ps1` đã chạy trên máy Tiến |
| T00 Môi trường | [#2](https://github.com/NeitLN/SaiGGo/issues/2) | Tiến | ✅ | Windows 11, Python 3.11.9, Node 24.12.0, FastAPI 0.162.0, uvicorn 0.54.0: `setup_dev.ps1` → `==> Xong`; pytest `1 passed`; `npm run build` OK; `/api/health` trả `{"status":"ok","dataset_loaded":false}` cả trực tiếp lẫn qua proxy Vite; trang http://localhost:5173 hiện "Server chạy, chưa nạp dataset" (đọc DOM bằng Edge headless) |
| T01 Fixture + Graph loader | [#3](https://github.com/NeitLN/SaiGGo/issues/3) | Tiến (chuyển từ Duy Anh 26/10) | 🟨 | PR chờ review. `tests/test_graph_model.py` 17 passed trên fixture `mini.json`. **Chưa kiểm chứng:** nạp đồ thị thật của T31 (chờ Release của T34; Python trên máy Tiến không kết nối được Overpass để tự build lại) |
| T02 OSMnx trên Windows | [#4](https://github.com/NeitLN/SaiGGo/issues/4) | Minh | ⬜ | |
| T03 Đáp án tính tay | [#5](https://github.com/NeitLN/SaiGGo/issues/5) | Bảo | ⬜ | |
| T10 Hàm địa lý | [#6](https://github.com/NeitLN/SaiGGo/issues/6) | Tiến (chuyển từ Duy Anh 26/10) | 🟨 | PR chờ review. `tests/test_geo.py` 13 passed; `haversine_m` khớp `osmnx.distance.great_circle` (sai số < 0,5 m) và trùng hàm của T31 tới 1e-9 m |
| T11 Dijkstra | [#7](https://github.com/NeitLN/SaiGGo/issues/7) | Tiến (chuyển từ Duy Anh 26/10) | 🟨 | PR chờ review (xếp chồng trên T01). `tests/test_dijkstra.py` 13 passed; khớp 6/6 tình huống tính tay của Bảo (#54) về chi phí, tuyến, `expanded`, và khớp chi phí với NetworkX |
| T12 CLI | [#8](https://github.com/NeitLN/SaiGGo/issues/8) | Tiến | ⬜ | |
| T20 A* | [#9](https://github.com/NeitLN/SaiGGo/issues/9) | Tiến (chuyển từ Duy Anh 26/10) | 🟨 | PR chờ review. `tests/test_astar.py` 24 passed: khớp 6/6 tình huống tính tay của Bảo (#54) về chi phí, tuyến, `expanded`; cùng chi phí với Dijkstra trên cả 36 cặp node; `h = 0` cho kết quả giống hệt Dijkstra; `reopened = 0` với heuristic địa lý; hệ số `c` tự tính giữ A* đúng khi có cạnh ngắn hơn khoảng cách thẳng. **Chưa kiểm chứng:** trên dữ liệu thật (T22, T33) |
| T21 Đối chứng ngẫu nhiên | [#10](https://github.com/NeitLN/SaiGGo/issues/10) | Duy Anh | 🟨 | PR chờ review. `tests/test_oracle_networkx.py` 5 passed: 20 đồ thị ngẫu nhiên (seed 0–19) × 50 cặp = 1.000 truy vấn, chi phí Dijkstra và A* khớp `nx.dijkstra_path_length` (sai số `1e-9 · max(1, cost)`), `no_path` ⇔ `NetworkXNoPath`, tuyến nối tiếp đúng chiều, `reopened = 0`; thêm 150 truy vấn có cạnh bị đóng. **Chưa kiểm chứng:** trên dữ liệu thật (T33) |
| T22 Kiểm tra heuristic | [#11](https://github.com/NeitLN/SaiGGo/issues/11) | Duy Anh | ⬜ | |
| T30 Tải dữ liệu | [#12](https://github.com/NeitLN/SaiGGo/issues/12) | Minh | ⬜ | |
| T31 Chuyển đổi + báo cáo | [#13](https://github.com/NeitLN/SaiGGo/issues/13) | Minh + Tiến | ⬜ | |
| T32 Vẽ mạng đường | [#14](https://github.com/NeitLN/SaiGGo/issues/14) | Minh | ⬜ | |
| T33 Dữ liệu thật + đối chứng | [#15](https://github.com/NeitLN/SaiGGo/issues/15) | Duy Anh + Tiến | ⬜ | |
| T40 Snapshot ùn tắc | [#16](https://github.com/NeitLN/SaiGGo/issues/16) | Duy Anh | 🟨 | PR chờ review. `tests/test_scenario.py` 22 passed: vùng tâm A r = 220 m, α = 2 → S→B→T 100 s; α = 2 mọi cạnh → tuyến không đổi, 160 s; α < 1 bị từ chối; đồ thị gốc không đổi; chồng vùng lấy `max`; lọc `highway`; file kịch bản lỗi bị từ chối. **Chưa làm:** CLI `--scenario/--block` (chờ T12) |
| T41 Đóng đường | [#17](https://github.com/NeitLN/SaiGGo/issues/17) | Duy Anh | 🟨 | PR chờ review. `tests/test_closures.py` 20 passed: `reverse_twins` (cùng `way_ids`, hình học đảo ngược); đóng A→T → S→B→T; đóng A→T + B→T → `no_path`; đóng đoạn hai chiều S↔B; đóng một trong hai cạnh song song thì cạnh còn lại vẫn đi được; tuyến của cả Dijkstra và A* không chứa cạnh đóng. **Chưa làm:** đếm cạnh có/không có cạnh đối trên dữ liệu thật (chờ T34) |
| T42 Kịch bản demo | [#18](https://github.com/NeitLN/SaiGGo/issues/18) | Bảo | ⬜ | |
| T50 Snap | [#19](https://github.com/NeitLN/SaiGGo/issues/19) | Minh | ⬜ | |
| T51 API route | [#20](https://github.com/NeitLN/SaiGGo/issues/20) | Tiến | ⬜ | |
| T52 UI tìm đường | [#21](https://github.com/NeitLN/SaiGGo/issues/21) | Minh | ⬜ | |
| T53 UI node mở rộng + kịch bản | [#22](https://github.com/NeitLN/SaiGGo/issues/22) | Minh | ⬜ | |
| T54 UI đóng đường | [#23](https://github.com/NeitLN/SaiGGo/issues/23) | Minh + Tiến | ⬜ | |
| T55 Case demo + kiểm thử tay | [#24](https://github.com/NeitLN/SaiGGo/issues/24) | Bảo | ⬜ | |
| T60 Benchmark vùng demo | [#25](https://github.com/NeitLN/SaiGGo/issues/25) | Tiến | ⬜ | |
| T61 Cắt lồng nhau | [#26](https://github.com/NeitLN/SaiGGo/issues/26) | Minh | ⬜ | |
| T62 Tăng quy mô | [#27](https://github.com/NeitLN/SaiGGo/issues/27) | Tiến | ⬜ | |
| T63 Ùn tắc / đóng đường | [#28](https://github.com/NeitLN/SaiGGo/issues/28) | Tiến | ⬜ | |
| T64 Biểu đồ | [#29](https://github.com/NeitLN/SaiGGo/issues/29) | Bảo | ⬜ | |
| G1 Cổng MVP | [#30](https://github.com/NeitLN/SaiGGo/issues/30) | Tiến | ⬜ | 05/11 |
| T65 Ghi kết quả | [#31](https://github.com/NeitLN/SaiGGo/issues/31) | Cả nhóm | ⬜ | |
| T70 Tour trên ma trận | [#32](https://github.com/NeitLN/SaiGGo/issues/32) | Duy Anh | 🟨 | PR chờ review. `tests/test_tour.py` 37 passed: 1 điểm; ma trận bất đối xứng; ma trận bẫy mà công thức delta đối xứng dự đoán rẻ hơn 18 nhưng chi phí tính lại là 112 so với 40, nên 2-opt không nhận; 2-opt không tăng chi phí và giữ đủ điểm trên 10 ma trận ngẫu nhiên; so với duyệt mọi hoán vị (n = 5). Ngoài phạm vi cam kết (quyết định 26/10), chỉ ở mức thuật toán |
| T71 Held–Karp | [#33](https://github.com/NeitLN/SaiGGo/issues/33) | Duy Anh | ⬜ | |
| T72 Ma trận + API tour | [#34](https://github.com/NeitLN/SaiGGo/issues/34) | Tiến | ⬜ | Chỉ sau G1 |
| T73 UI tour | [#35](https://github.com/NeitLN/SaiGGo/issues/35) | Minh | ⬜ | |
| T74 Benchmark tour | [#36](https://github.com/NeitLN/SaiGGo/issues/36) | Tiến | ⬜ | |
| T80 Máy thứ hai | [#37](https://github.com/NeitLN/SaiGGo/issues/37) | Bảo | ⬜ | |
| T81 Đồng bộ tài liệu | [#38](https://github.com/NeitLN/SaiGGo/issues/38) | Tiến | ⬜ | |
| T82 Tập demo + video | [#39](https://github.com/NeitLN/SaiGGo/issues/39) | Minh + Bảo | ⬜ | |
| T83 Essay | [#40](https://github.com/NeitLN/SaiGGo/issues/40) | Cả nhóm | ⬜ | |

## 3. Đã kiểm chứng / chưa kiểm chứng (23/10/2026)

### ✅ Đã kiểm chứng

- Nội dung repo tại commit `4f98c36`: khung FastAPI có `/api/health`, frontend Vite + Leaflet chưa có dữ liệu, script `prepare_data.py` / `run_benchmarks.py` / `plot_results.py` chỉ in "chưa triển khai", một test `test_health.py`. **Chưa có thuật toán, dữ liệu hay kết quả.**
- Số liệu ví dụ ở [DATA_MODEL.md](DATA_MODEL.md) mục 7 (chi phí 80/100/160 s, `expanded` 5 so với 2 và 3, `no_path`) đã được chạy bằng một script thử độc lập và khớp `networkx.dijkstra_path_length`. Script chưa nằm trong repo; T01/T03/T11 sẽ biến ví dụ này thành test chính thức.
- Mốc thời gian (12/11, 19/11, 22/11) khớp với `Project_Intructions_261.pdf`.

### ⚠️ Chưa kiểm chứng

- Khung **chưa được chạy trên Windows**: máy này chưa có `.venv`, chưa cài FastAPI, chưa có `frontend/node_modules`. (CI GitHub trên Ubuntu đã xanh ở commit `4f98c36`: `pytest` + `npm run build`, nên khung đúng trên Linux.) → T00.
- OSMnx chưa được cài và chưa thử trên Windows. → T02.
- Bảng tốc độ, vùng demo, bán kính ùn tắc, ngưỡng snap 150 m, các kích thước 1/2/3/4,5 km đều là **đề xuất**, chưa thử trên dữ liệu thật.
- Khả năng vẽ mạng đường vùng demo trên Leaflet đủ mượt: chưa đo. → T32.
- Thời gian chạy Python trên đồ thị lớn nhất: chưa đo. → T61 pilot.

## 4. Vấn đề còn tồn tại

| # | Vấn đề | Ảnh hưởng | Xử lý |
|---|---|---|---|
| I1 | Scope gate 23/10 trong proposal không đạt (chưa có code thuật toán) | Phải sắp lại phạm vi | Đã sắp lại ở PROJECT_BRIEF mục 3–4; nên báo giảng viên về D1, D2 |
| I2 | [DEMO.md](DEMO.md) và README vẫn mô tả tour là chế độ chính | Tài liệu mâu thuẫn với kế hoạch mới | T81 |
| I3 | Thư mục gốc có file chưa commit: 2 file PDF slide trùng nội dung (`Group4_SaiGo_Proposal_Slides.pdf` = `SaiGo_Proposal_Slides.pdf`, cùng MD5), file `.pptx`, `SaiGo_Proposal_Script.md`, `Project_Intructions_261.pdf`, một video `.mp4` | Dễ commit nhầm file lớn hoặc trùng | Nhóm quyết định giữ ngoài Git hay chuyển vào `docs/proposal/` |
| I4 | Repo không có ma trận gốc của ví dụ 2-opt ở backup slide B1 | T70 phải dựng lại ví dụ | Ghi trong T70 |
| I5 | Video `.mp4` là mockup giao diện có số liệu không do hệ thống đo (ví dụ "độ tin cậy dự báo", "% giảm ùn tắc") | Không được đưa những số này vào app/slide | DEMO.md mục 1.6 đã loại; giữ nguyên quy tắc |
| I6 | `pip install -e` lỗi trên Windows khi đường dẫn repo có chữ tiếng Việt (setuptools ghi file `.pth` bằng cp1252) | README cũ hướng dẫn sai cho ai clone vào thư mục có dấu | `setup_dev.ps1` chỉ cài thư viện phụ thuộc, không dùng `-e`; khuyên clone vào `C:\dev\SaiGGo` |

## 5. Checklist kiểm thử giao diện (dùng ở T52–T55)

| Mã | Thao tác | Kết quả mong đợi | Lần kiểm gần nhất |
|---|---|---|---|
| UI-1 | Mở app khi backend đang chạy | Mạng đường hiện đúng vị trí; ghi nguồn OSM ở góc bản đồ | — |
| UI-2 | Bấm 2 điểm, bấm **Tìm đường** | Hai tuyến; bảng có chi phí (s), quãng đường (m), node mở rộng, thời gian tính (ms), "Chi phí trùng khớp: có" | — |
| UI-3 | Bấm **Đảo chiều** ở một cặp có đường một chiều | Tuyến/chi phí thay đổi | — |
| UI-4 | Bấm điểm cách đường > 150 m hoặc ngoài vùng | Thông báo lỗi tiếng Việt; không vẽ tuyến | — |
| UI-5 | Bật lớp node mở rộng | Hai màu chấm; nhãn "K node đầu tiên" nếu bị cắt | — |
| UI-6 | Chọn kịch bản `peak-center` ở case demo | Vùng ùn tắc hiện; tuyến đổi; chi phí tăng | — |
| UI-7 | Bấm vào một cạnh trên tuyến → **Đóng đoạn** | Cạnh đỏ; tuyến mới không đi qua; tuyến cũ mờ | — |
| UI-8 | Case "Không còn đường" | Thông báo không có đường; không có đường thẳng nối hai điểm | — |

## 6. Nhật ký

| Ngày | Ai | Việc | Kết quả |
|---|---|---|---|
| 23/10/2026 | Tiến | Lập bộ tài liệu kế hoạch (PROJECT_BRIEF, ARCHITECTURE, DATA_MODEL, ROADMAP, TASKS, EXPERIMENT_PLAN, PROGRESS) | Kế hoạch xong; chưa triển khai code |
| 23/10/2026 | Tiến | Dựng hệ thống theo dõi: 10 milestone, 40 issue có phụ thuộc, GitHub Project, template issue/PR, CODEOWNERS, burndown tự động, bảo vệ branch `main` | Đã kiểm chứng: issue/Project tạo đúng; burndown chạy được tại máy |
| 24/10/2026 | Tiến | Review hệ thống theo dõi (2 người review độc lập), sửa 13 điểm: chốt số cuối ngày vào `daily.csv`, phân biệt đóng qua PR/commit với đóng tay, kiểm tra ước lượng, đếm review theo PR, tổng kết tuần không trùng, sync giữ checkbox và nhãn `blocked`, xử lý issue mở lại, Bảo vào CODEOWNERS, cấp quyền Project cho cả nhóm, yêu cầu người approve khác người push cuối | Đã kiểm chứng tại máy: chạy burndown 2 lần cho `daily.csv` giống nhau; `--sync` 2 lần cho cùng trạng thái issue; checkbox và nhãn `blocked` được giữ. **Chưa kiểm chứng:** workflow mới trên GitHub (chỉ chạy sau khi PR được merge) |
| 24/10/2026 | Tiến | Bộ bắt đầu cho thành viên: `scripts/setup_dev.ps1`, ONBOARDING, KICKOFF, 4 phiếu bắt đầu | Đã kiểm chứng: script chạy tới `==> Xong` bằng Windows PowerShell 5.1, không lỗi cú pháp trên PowerShell 7; phát hiện và tránh lỗi I6. **Chưa kiểm chứng:** script trên máy của Duy Anh, Minh, Bảo; chế độ `-Data` (OSMnx) |
| 25/10/2026 | Tiến | T06: `docs/STATUS.md`; ROADMAP mục 5 (quyết định đắt nếu đổi Q1–Q8) và mục 6 (kế hoạch tuần 2, chờ duyệt); mốc walking skeleton MW (T13–T15, issue #49–#51) và contract `/api/route` v1; `requirements-lock.txt` + CI cài theo file khóa; job `audit`; `setup_dev.ps1` dùng file khóa, nâng setuptools | Đã kiểm chứng: `pip-audit -r requirements-lock.txt` không có lỗ hổng; `setup_dev.ps1 -Data` chạy tới `==> Xong` (Python 3.11.9); pytest `1 passed`; `npm run build` OK; `create_backlog.py --dry-run` 46 task / 139 giờ. Phát hiện: pip và pip-audit đọc file requirements bằng cp1252 nên file khóa phải là ASCII. Job `audit` của CI bắt được 1 lỗ hổng mức high ở dev server (`vite` 8.3.1, `launch-editor`; GHSA-9jrq-w75r-8gcw và các mã khác) → `npm audit fix` nâng `vite` lên 8.3.5, sau đó `npm audit` báo 0 lỗ hổng, build OK. CI Linux cài theo file khóa: PASS |
| 25/10/2026 | Tiến | T00: xác nhận khung chạy trên Windows | Đã kiểm chứng: backend `uvicorn` cổng 8000 trả `/api/health`; frontend Vite cổng 5173 chuyển `/api` qua proxy đúng; trang hiện đúng trạng thái server (DOM đọc bằng Edge headless sau khi JavaScript chạy). Phiên bản: Python 3.11.9, Node 24.12.0, FastAPI 0.162.0, uvicorn 0.54.0. Bảo cũng chạy được trên một máy Windows khác (review PR #52) |
| 26/10/2026 | Tiến | T01: `tests/fixtures/mini.json` (6 node, 8 cạnh, 4 cạnh một chiều), `backend/app/graph/model.py` (`Graph`, `GraphMeta`, `load_graph`, `node_by_name`, kiểm tra theo DATA_MODEL mục 2.3), DATA_MODEL mục 2.1 thêm `in_scc` và `name` | Đã kiểm chứng: viết test trước, chạy thấy lỗi thiếu module, rồi code; `pytest tests/test_graph_model.py` → 17 passed (fixture, cạnh một chiều, `base_time` 40 s, `v_max` 10 m/s, haversine ≤ length ở mọi cạnh, hình học bắt đầu ở u, 8 kiểu dữ liệu sai bị từ chối). **Chưa kiểm chứng:** nạp đồ thị thật (test `realdata` đã có, tự chạy khi có file trên Release) |
