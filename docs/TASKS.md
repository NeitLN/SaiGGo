# SaiGo — Danh sách task

Mỗi task vừa sức một buổi (khoảng 2–4 giờ). Nếu một task kéo dài quá hai buổi, tách nhỏ và ghi lý do vào [PROGRESS.md](PROGRESS.md). Người phụ trách là **[Đề xuất]**: Tiến có thể vào làm cùng ở mọi task.

Ký hiệu: 👤 phụ trách · ⏱ ước lượng · ⛓ phụ thuộc · 📁 file · 📦 đầu ra · ✅ hoàn thành khi · ▶ kiểm tra · 🧠 kiến thức cần hiểu để giải thích.

Thứ tự gợi ý trong tuần đầu: **T00 → T01 → T03 → T10 → T11 → T12 → T20 → T21 → T22**, song song **T02 → T30 → T31 → T32**.

Mỗi task ở đây là một GitHub Issue (nhãn `task`). Trạng thái theo dõi trên GitHub Project, quy trình ở [CONTRIBUTING.md](../CONTRIBUTING.md). Khi sửa task ở file này, chạy lại `python scripts/tracking/create_backlog.py --sync` để cập nhật issue.

---

## M0 — Nền móng

### T-PLAN — Lập kế hoạch triển khai và hệ thống theo dõi
- 👤 Tiến · ⏱ 4 h · ⛓ —
- **Mục tiêu:** có kế hoạch, backlog và công cụ theo dõi trước khi viết code.
- **Việc cần làm:** viết bộ tài liệu kế hoạch trong `docs/`; tạo labels, milestones, issues, GitHub Project; viết template issue/PR, CONTRIBUTING, script burndown.
- 📁 `docs/*.md`, `docs/tracking/`, `.github/`, `scripts/tracking/`, `CONTRIBUTING.md`
- 📦 Kế hoạch + backlog trên GitHub + burndown tự động.
- ✅ Mọi task có issue; burndown hiện trên issue theo dõi.
- ▶ Mở tab Issues và Project của repo.
- 🧠 Vì sao chia nhỏ task; burndown đọc thế nào.

### T00 — Dựng môi trường và xác nhận khung chạy
- 👤 Tiến · ⏱ 1–2 h · ⛓ —
- **Mục tiêu:** chứng minh khung hiện có chạy trên Windows trước khi viết code mới.
- **Việc cần làm:**
  1. `python -m venv .venv`, kích hoạt, `pip install -e ".[dev]"`.
  2. Chạy `pytest -q`.
  3. Chạy backend: `uvicorn app.main:app --reload --app-dir backend`; mở `http://127.0.0.1:8000/api/health`.
  4. `cd frontend && npm install && npm run build && npm run dev`; mở `http://localhost:5173`.
  5. Ghi phiên bản Python, Node, FastAPI vào PROGRESS.md.
- 📁 PROGRESS.md (không đổi code)
- 📦 Môi trường chạy được; phiên bản được ghi lại.
- ✅ `pytest` báo `1 passed`; trang web hiện "Server chạy, chưa nạp dataset".
- ▶ `pytest -q` · `npm run build`
- 🧠 Vai trò venv; vì sao frontend gọi `/api` qua proxy của Vite (`vite.config.ts`).

### T01 — Chốt định dạng đồ thị, tạo fixture mẫu và bộ nạp Graph
- 👤 Duy Anh (Tiến review) · ⏱ 3 h · ⛓ T00
- **Mục tiêu:** có một đồ thị nhỏ tính tay được và một hàm nạp dùng chung cho mọi phần sau.
- **Việc cần làm:**
  1. Viết `tests/fixtures/mini.json` theo đúng `saigo-graph/1`, dựa trên ví dụ ở [DATA_MODEL.md](DATA_MODEL.md) mục 7. Đổi mét sang lat/lon quanh tâm (10.7725, 106.6980); mỗi node có thêm trường tùy chọn `"name": "S"`.
  2. Viết `Graph` (dataclass) và `load_graph(path)` trong `backend/app/graph/model.py`: đọc JSON, kiểm tra (DATA_MODEL mục 2.3), dựng `out_edges`, tính `base_time_s`, `v_max_mps`.
  3. Hàm `node_by_name(graph, "S")` để test và CLI dùng tên.
  4. Test: số node/cạnh, đường một chiều (A→T có, T→A không), cạnh lỗi (tốc độ ≤ 0) bị từ chối.
- 📁 `backend/app/graph/model.py`, `tests/fixtures/mini.json`, `tests/test_graph_model.py`
- 📦 Bộ nạp đồ thị + fixture.
- ✅ Test xanh; định dạng JSON được Minh xác nhận là sẽ xuất ra được ở T31.
- ▶ `pytest tests/test_graph_model.py -q`
- 🧠 Đồ thị có hướng; adjacency list theo **edge id**; vì sao cần `key` cho cạnh song song; `base_time = length / (km/h ÷ 3,6)`.

### T02 — Thử OSMnx trên Windows
- 👤 Minh (Tiến hỗ trợ) · ⏱ 2 h · ⛓ T00
- **Mục tiêu:** phát hiện sớm rủi ro cài đặt thư viện địa lý.
- **Việc cần làm:**
  1. `pip install -e ".[data]"`. Nếu lỗi, tạo môi trường conda-forge riêng (`conda create -n saigo-data -c conda-forge osmnx`) và ghi lại.
  2. Thêm chế độ `--smoke` vào `scripts/prepare_data.py`: tải bbox ~500 m quanh Bến Thành với `network_type="drive"`, in số node/cạnh, số cạnh có `oneway=True`, rồi lưu GraphML vào `data/raw/smoke.graphml`.
  3. Ghi phiên bản OSMnx, NetworkX, geopandas, shapely vào PROGRESS.md.
- 📁 `scripts/prepare_data.py`, `pyproject.toml` (khóa phiên bản nếu cần)
- 📦 Lệnh smoke chạy được.
- ✅ In ra số node/cạnh > 0 trên máy Windows của nhóm.
- ▶ `python scripts/prepare_data.py --smoke`
- 🧠 OSMnx trả `MultiDiGraph`; `network_type="drive"` gồm những loại đường nào; vì sao không tải lại dữ liệu mỗi lần chạy.

### T03 — Bảng kết quả tính tay cho đồ thị mẫu
- 👤 Bảo (Duy Anh review) · ⏱ 2 h · ⛓ — (chỉ cần DATA_MODEL mục 7)
- **Mục tiêu:** có đáp án độc lập để kiểm tra code Dijkstra/A*.
- **Việc cần làm:**
  1. Với 6 tình huống ở DATA_MODEL mục 7, chạy tay Dijkstra: ghi bảng từng bước (heap, `g`, node pop).
  2. Làm tương tự cho A* tình huống cơ sở: tính `h`, `f` từng node.
  3. Ghi kết quả vào `tests/fixtures/mini_expected.json`: chi phí, tuyến, số node mở rộng.
- 📁 `tests/fixtures/mini_expected.json`, `docs/ALGORITHMS.md` (thêm bảng chạy tay)
- 📦 Đáp án + bảng giải thích.
- ✅ Duy Anh đối chiếu và xác nhận; có ít nhất một bảng từng bước cho Dijkstra và một cho A*.
- ▶ Review thủ công; sau T11/T20 các test đọc file này phải xanh.
- 🧠 Thứ tự pop của Dijkstra; vì sao A* không pop C và D.

### T04 — Sửa hệ thống theo dõi sau review
- 👤 Tiến (Duy Anh review) · ⏱ 3 h · ⛓ T-PLAN
- **Mục tiêu:** số liệu theo dõi không bị viết lại, không bị "làm đẹp", và đồng bộ không xóa thông tin đang dùng.
- **Việc cần làm:** burndown lưu số cuối ngày vào `daily.csv` (chỉ ghi thêm); tách task hoàn thành qua PR/commit với task đóng thủ công và task bị cắt; kiểm tra ước lượng; đếm review theo cặp người–PR; bình luận tổng kết tuần không trùng; `create_backlog.py` giữ checkbox, nhãn `blocked` và tìm issue theo "Mã task"; `setup_project.py` xử lý issue mở lại; thêm Bảo vào CODEOWNERS; sửa phụ thuộc T80 và hạn T03.
- 📁 `scripts/tracking/*.py`, `.github/workflows/tracking.yml`, `.github/CODEOWNERS`, `docs/tracking/`, `docs/TASKS.md`
- 📦 Hệ thống theo dõi đã sửa.
- ✅ Chạy `burndown.py` tại máy ra cùng số với issue theo dõi; chạy `create_backlog.py --sync` hai lần liên tiếp không đổi gì.
- ▶ `python scripts/tracking/burndown.py --out build/tracking` · `python scripts/tracking/create_backlog.py --dry-run`
- 🧠 Vì sao lịch sử burndown phải chỉ ghi thêm; khác biệt giữa "đóng issue" và "hoàn thành có bằng chứng".

### T05 — Hướng dẫn bắt đầu cho từng thành viên
- 👤 Tiến (Duy Anh review) · ⏱ 3 h · ⛓ T04
- **Mục tiêu:** mỗi thành viên tự dựng được môi trường và bắt đầu task đầu tiên mà không phải hỏi lại.
- **Việc cần làm:** `scripts/setup_dev.ps1` dựng môi trường bằng một lệnh; `docs/team/ONBOARDING.md` (cài đặt, git đúng tên, quy trình PR/review, lỗi thường gặp); phiếu bắt đầu cho từng người trong `docs/team/start/`; chương trình họp khởi động `docs/team/KICKOFF.md`; README dùng script mới.
- 📁 `scripts/setup_dev.ps1`, `docs/team/`, `README.md`
- 📦 Bộ tài liệu bắt đầu + script.
- ✅ Script chạy tới `==> Xong` trên Windows PowerShell 5.1; mọi link trong tài liệu mở được.
- ▶ `powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1`
- 🧠 Vì sao commit phải mang tên đúng người; vì sao `pip install -e` lỗi với đường dẫn có dấu trên Windows.

---

## M1 — Dijkstra trên đồ thị mẫu

### T10 — Hàm địa lý
- 👤 Duy Anh · ⏱ 1–2 h · ⛓ T00
- **Mục tiêu:** có hàm khoảng cách dùng chung cho heuristic, snap và ùn tắc.
- **Việc cần làm:** `haversine_m(lat1, lon1, lat2, lon2)` với R = 6 371 009 m; `polyline_midpoint(coords)` (điểm ở 50% chiều dài); test với một cặp điểm có khoảng cách đã biết, test 2 điểm trùng nhau = 0 và test thứ tự `[lon, lat]` của GeoJSON.
- 📁 `backend/app/graph/geo.py`, `tests/test_geo.py`
- 📦 Module `geo`.
- ✅ Sai số < 0,5 m so với giá trị tham chiếu (tính bằng `osmnx.distance.great_circle` hoặc một công cụ trực tuyến, ghi nguồn trong test).
- ▶ `pytest tests/test_geo.py -q`
- 🧠 Công thức haversine; vì sao GeoJSON là `[lon, lat]` còn Leaflet là `[lat, lon]`.

### T11 — Dijkstra và SearchResult
- 👤 Duy Anh · ⏱ 3–4 h · ⛓ T01, T03
- **Mục tiêu:** cài Dijkstra đúng quy tắc ở DATA_MODEL mục 6.
- **Việc cần làm:**
  1. `SearchResult` + hàm dựng tuyến từ `pred_edge` trong `algorithms/result.py`.
  2. `dijkstra(graph, snap, source, target, trace_limit=0)` với heap `(g, counter, node)`, lazy deletion, dừng khi pop đích, đếm `expanded`, `relaxations`, `pushes`, `max_frontier`.
  3. Tạm thời tạo `Snapshot` cơ sở bằng hàm nhỏ `baseline_snapshot(graph)` (T40 sẽ thay).
  4. Test: 6 tình huống trong `mini_expected.json`; `source == target`; cạnh song song (thêm vào bản sao fixture một cạnh S→A nhanh hơn → tuyến phải dùng đúng edge id đó); tổng `weights` theo `edge_ids` bằng `cost_s`.
- 📁 `backend/app/algorithms/result.py`, `dijkstra.py`, `tests/test_dijkstra.py`
- 📦 Dijkstra chạy trên fixture.
- ✅ Mọi test xanh; `expanded` = 5 ở tình huống cơ sở.
- ▶ `pytest tests/test_dijkstra.py -q`
- 🧠 Vì sao Dijkstra đúng khi trọng số không âm; lazy deletion; độ phức tạp `O((V+E) log V)`; vì sao lưu predecessor là **cạnh**.

### T12 — CLI tìm đường
- 👤 Tiến · ⏱ 2 h · ⛓ T11
- **Mục tiêu:** chạy thuật toán từ dòng lệnh để kiểm tra và giải thích, chưa cần web.
- **Việc cần làm:** `python -m app.cli route --graph <file> --from S --to T --algo dijkstra|astar|both` (nhận tên node hoặc `--from-latlon lat,lon`); in tuyến (tên/ID), chi phí (s), quãng đường (m), số node mở rộng, thời gian chạy (ms).
- 📁 `backend/app/cli.py`
- 📦 Lệnh CLI.
- ✅ Kết quả in ra khớp `mini_expected.json`.
- ▶ `python -m app.cli route --graph tests/fixtures/mini.json --from S --to T --algo dijkstra` (chạy trong thư mục `backend/` hoặc với `PYTHONPATH=backend`)
- 🧠 Đo thời gian bằng `perf_counter_ns` chỉ quanh lời gọi thuật toán.

---

## M2 — A* và đối chứng

### T20 — A* với heuristic địa lý
- 👤 Duy Anh · ⏱ 3 h · ⛓ T10, T11
- **Mục tiêu:** A* cho cùng chi phí với Dijkstra nhưng mở rộng ít node hơn trên fixture.
- **Việc cần làm:**
  1. `astar(graph, snap, source, target, heuristic, trace_limit=0)`: ưu tiên `g + h`, cho phép mở lại, đếm `reopened`.
  2. `make_geo_heuristic(graph, target, c=1.0)` và `zero_heuristic`.
  3. Test: chi phí bằng Dijkstra ở cả 6 tình huống; `expanded` = 2 ở tình huống cơ sở; với `zero_heuristic` thì `expanded` giống hệt Dijkstra; `reopened == 0`.
- 📁 `backend/app/algorithms/astar.py`, `heuristics.py`, `tests/test_astar.py`
- 📦 A* chạy trên fixture.
- ✅ Mọi test xanh.
- ▶ `pytest tests/test_astar.py -q` · CLI `--algo both`
- 🧠 `f = g + h`; admissible và consistent; chứng minh phác thảo ở DATA_MODEL mục 5.2; vì sao `h = 0` biến A* thành Dijkstra.

### T21 — Đối chứng NetworkX trên đồ thị ngẫu nhiên
- 👤 Duy Anh (Tiến review) · ⏱ 3 h · ⛓ T20
- **Mục tiêu:** bằng chứng thực nghiệm rằng code đúng trên nhiều đồ thị, không chỉ fixture.
- **Việc cần làm:**
  1. Bộ sinh đồ thị ngẫu nhiên có seed: node có tọa độ, cạnh có hướng, `length ≥ haversine` (nhân một hệ số ≥ 1), có cạnh song song và cặp không tới được.
  2. Với 20 đồ thị × 50 cặp: so `cost_s` của Dijkstra và A* với `nx.dijkstra_path_length` trên `MultiDiGraph` cùng trọng số; so trường hợp `no_path` với `nx.NetworkXNoPath`.
  3. Kiểm tra tuyến: các cạnh nối tiếp nhau, đi đúng chiều, không dùng cạnh bị chặn.
- 📁 `tests/test_oracle_networkx.py`, `tests/helpers/random_graph.py`
- 📦 Test đối chứng.
- ✅ 1.000 truy vấn khớp với sai số `1e-9 · max(1, cost)`; chạy < 30 s trong CI.
- ▶ `pytest tests/test_oracle_networkx.py -q`
- 🧠 Vì sao so **chi phí** mà không so dãy node (có thể có nhiều tuyến cùng chi phí); test không phải chứng minh.

### T22 — Kiểm tra điều kiện heuristic trên dữ liệu
- 👤 Duy Anh · ⏱ 2 h · ⛓ T20, T12
- **Mục tiêu:** tính `c`, `v_max` và phát hiện dữ liệu làm heuristic sai.
- **Việc cần làm:** `compute_c(graph)` (DATA_MODEL mục 5.1); lệnh `python -m app.cli check-heuristic --graph <file>` in `v_max`, `c`, số cạnh có `length < haversine`, 5 cạnh tệ nhất; test với một fixture cố ý có cạnh ngắn hơn khoảng cách thẳng.
- 📁 `backend/app/algorithms/heuristics.py`, `backend/app/cli.py`, `tests/test_heuristics.py`
- 📦 Báo cáo heuristic.
- ✅ Fixture chuẩn cho `c = 1`; fixture lỗi cho `c < 1` và A* vẫn khớp Dijkstra khi dùng `c` đó.
- ▶ `pytest tests/test_heuristics.py -q`
- 🧠 Vì sao nhân `c` vẫn giữ consistency (bất đẳng thức tam giác).

---

## M3 — Dữ liệu thật trên bản đồ (song song)

### T30 — Chốt vùng và tải dữ liệu một lần
- 👤 Minh (Bảo hỗ trợ chọn tọa độ) · ⏱ 2–3 h · ⛓ T02
- **Mục tiêu:** có bản dữ liệu thô đóng băng cho mọi thực nghiệm.
- **Việc cần làm:**
  1. `data/config/areas.json`: tâm Bến Thành, nửa cạnh vùng tải 4,5 km + đệm 0,5 km **[Đề xuất]**, vùng demo nửa cạnh 2 km **[Đề xuất]**.
  2. `data/config/speeds.json` theo bảng DATA_MODEL mục 3.2.
  3. `python scripts/prepare_data.py download`: tải bbox vùng tải, lưu `data/raw/outer.graphml`, ghi `data/processed/raw_manifest.json` (ngày tải, bbox, phiên bản OSMnx, số node/cạnh, `sha256`).
- 📁 `data/config/areas.json`, `data/config/speeds.json`, `scripts/prepare_data.py`
- 📦 GraphML thô + manifest.
- ✅ Tải xong; số node/cạnh được ghi bằng số đo, không ước lượng.
- ▶ `python scripts/prepare_data.py download` · mở `raw_manifest.json`
- 🧠 Vì sao cần vùng đệm; vì sao đóng băng dữ liệu (tái lập kết quả).

### T31 — Chuyển GraphML thành `saigo-graph/1` và báo cáo kiểm tra
- 👤 Minh + Tiến · ⏱ 4 h (có thể 2 buổi) · ⛓ T01, T30
- **Mục tiêu:** đồ thị thật đọc được bằng `load_graph` của T01.
- **Việc cần làm:**
  1. `python scripts/prepare_data.py build --area demo`: cắt vùng (DATA_MODEL mục 8.2 bước 4), chuẩn hóa `way_ids`/`highway`, gán tốc độ, chọn SCC, đánh lại ID, xuất JSON + `manifest.json`.
  2. In báo cáo: số node/cạnh, % một chiều, cạnh song song, self-loop, kích thước SCC, số node ngoài SCC.
  3. Kiểm tra tay 2–3 đường một chiều đã biết ở Quận 1 (xem trên openstreetmap.org); ghi kết quả vào PROGRESS.md.
  4. Test (đánh dấu `realdata`, tự bỏ qua nếu không có file): `load_graph` đọc được, mọi ID hợp lệ.
- 📁 `scripts/prepare_data.py`, `data/processed/<dataset_id>.json` (gitignored), `data/processed/manifest.json` (commit), `tests/test_realdata.py`
- 📦 Đồ thị vùng demo.
- ✅ `load_graph` nạp được; báo cáo được dán vào PROGRESS.md; đường một chiều kiểm tra tay đúng chiều.
- ▶ `python scripts/prepare_data.py build --area demo` · `pytest -m realdata -q`
- 🧠 Simplify gộp nhiều đoạn thành một cạnh; `osmid` dạng list; SCC khác WCC thế nào; vì sao điểm ngoài SCC không được dùng.

### T32 — Vẽ mạng đường thật trên bản đồ
- 👤 Minh · ⏱ 3 h · ⛓ T31
- **Mục tiêu:** nhìn thấy đồ thị trên Leaflet, đo được tốc độ vẽ.
- **Việc cần làm:**
  1. Backend nạp Graph khi khởi động (đường dẫn qua biến môi trường `SAIGO_GRAPH`); `/api/health` báo `dataset_loaded: true`; `/api/network` trả GeoJSON có `edge_id`.
  2. Frontend: `preferCanvas: true`, vẽ lớp mạng đường, căn khung theo vùng; giữ ghi nguồn OSM; tile OSM nền chỉ khi có mạng.
  3. Đo thời gian tải + vẽ trên laptop demo; ghi vào PROGRESS.md.
- 📁 `backend/app/main.py`, `api/routes.py`, `api/schemas.py`, `frontend/src/main.ts`, `api.ts`, `layers.ts`, `tests/test_health.py`
- 📦 Bản đồ có mạng đường thật.
- ✅ Mạng đường hiện đúng vị trí trên nền OSM (không lệch, không đảo lat/lon); kéo/zoom không giật rõ rệt.
- ▶ Chạy backend + frontend, mở `http://localhost:5173`; `pytest tests/test_health.py -q`
- 🧠 Luồng dữ liệu server → GeoJSON → Leaflet; vì sao không tải tile hàng loạt.

---

## M4 — Hợp nhất: tìm đường trên dữ liệu thật

### T33 — Dijkstra/A* trên đồ thị thật + đối chứng 200 cặp
- 👤 Duy Anh + Tiến · ⏱ 3 h · ⛓ T22, T31
- **Mục tiêu:** xác nhận thuật toán đúng trên dữ liệu thật trước khi làm tiếp.
- **Việc cần làm:** chạy `check-heuristic` trên đồ thị thật (điều tra nếu `c < 0,999`); CLI `route --from-latlon ... --to-latlon ...`; test `realdata`: 200 cặp ngẫu nhiên (seed) trong SCC, so với NetworkX; đăng ký marker `realdata` trong `pyproject.toml`.
- 📁 `tests/test_realdata.py`, `pyproject.toml`
- 📦 Bằng chứng đúng trên dữ liệu thật + giá trị `c`, `v_max` ghi vào manifest.
- ✅ 200/200 cặp khớp; `reopened == 0` ở mọi truy vấn A*.
- ▶ `pytest -m realdata -q` · `python -m app.cli check-heuristic --graph data/processed/<id>.json`
- 🧠 Nếu `reopened > 0` thì heuristic có vấn đề gì.

---

## M5 — Ùn tắc và đóng đường

### T40 — Snapshot và luật ùn tắc theo vùng
- 👤 Tiến · ⏱ 3–4 h · ⛓ T10, T11
- **Mục tiêu:** chi phí thay đổi theo kịch bản mà đồ thị gốc không đổi.
- **Việc cần làm:** `Scenario`, `Snapshot`, `build_snapshot(graph, scenario, blocked)` theo DATA_MODEL mục 4; đọc `data/config/scenarios.json`; thay `baseline_snapshot` của T11; CLI thêm `--scenario` và `--block`.
- **Test bắt buộc** (trên fixture): vùng tâm A, r = 220 m, α = 2 → tuyến S→B→T, 100 s; α = 2 cho mọi cạnh → tuyến không đổi, 160 s; α < 1 bị từ chối; đồ thị gốc không đổi sau khi tạo snapshot.
- 📁 `backend/app/graph/scenario.py`, `tests/test_scenario.py`, `backend/app/cli.py`
- 📦 Snapshot.
- ✅ Test xanh.
- ▶ `pytest tests/test_scenario.py -q`
- 🧠 Vì sao nhân đều không đổi tuyến; vì sao lấy `max` thay vì tích; vì sao `α ≥ 1` giữ heuristic đúng.

### T41 — Đóng đường một chiều và hai chiều
- 👤 Tiến · ⏱ 2–3 h · ⛓ T40, T31
- **Mục tiêu:** đóng đúng cạnh, kể cả cạnh song song và cạnh đối.
- **Việc cần làm:** `reverse_twins(graph_meta)` (DATA_MODEL mục 4.2); kiểm tra `blocked_edge_ids` hợp lệ; test: đóng A→T → S→B→T; đóng A→T + B→T → `no_path`; đóng một trong hai cạnh song song thì cạnh còn lại vẫn đi được; tuyến mới không chứa cạnh đóng.
- 📁 `backend/app/graph/closures.py`, `tests/test_closures.py`
- 📦 Đóng đường.
- ✅ Test xanh; trên đồ thị thật, ghi số cạnh có/không có cạnh đối.
- ▶ `pytest tests/test_closures.py -q`
- 🧠 Một con đường hai chiều là hai cạnh có hướng; dual carriageway.

### T42 — Kịch bản ùn tắc cho demo
- 👤 Bảo (Tiến review) · ⏱ 2 h · ⛓ T40, T33
- **Mục tiêu:** có 2–3 kịch bản dễ nhận ra trên bản đồ và thực sự làm đổi tuyến.
- **Việc cần làm:** chọn 1–2 vùng quanh các trục đường quen thuộc ở Quận 1; ghi vào `data/config/scenarios.json` (`baseline`, `peak-center`, …); với 3 cặp điểm demo, chạy CLI với và không có kịch bản, ghi lại tuyến có đổi không.
- 📁 `data/config/scenarios.json`, PROGRESS.md
- 📦 File kịch bản đã thử.
- ✅ Ít nhất một cặp điểm có tuyến **đổi** dưới `peak-center`.
- ▶ `python -m app.cli route --graph ... --from-latlon ... --to-latlon ... --scenario peak-center --algo both`
- 🧠 Kịch bản là mô phỏng; nhãn "Cao điểm mô phỏng".

---

## M6 — Bản đồ tương tác

### T50 — Snap điểm về node
- 👤 Minh (Tiến hỗ trợ) · ⏱ 2 h · ⛓ T10, T31
- **Việc cần làm:** `nearest_node(graph, lat, lon, max_m=150)` chỉ trên node thuộc SCC; trả `node_id`, `snap_distance_m`; lỗi rõ ràng khi quá xa/ngoài vùng; test trên fixture.
- 📁 `backend/app/graph/snap.py`, `tests/test_snap.py`
- 📦 Hàm snap · ✅ Test xanh · ▶ `pytest tests/test_snap.py -q`
- 🧠 Vì sao node gần nhất có thể ở bên kia sông/cầu; ngưỡng 150 m là giả định.

### T51 — API `/api/route` và `/api/dataset`
- 👤 Tiến · ⏱ 3–4 h · ⛓ T33, T40, T41, T50
- **Việc cần làm:** schema Pydantic theo ARCHITECTURE mục 4; `services/routing.py` (snap → snapshot → chạy thuật toán → đo thời gian → gắn geometry); `costs_match`; lỗi 422 có thông báo tiếng Việt; test bằng TestClient với fixture.
- 📁 `backend/app/api/schemas.py`, `routes.py`, `backend/app/services/routing.py`, `tests/test_api_route.py`
- 📦 API tìm đường.
- ✅ Test: route bình thường, `no_path`, cạnh đóng không tồn tại → 422, điểm quá xa → 422.
- ▶ `pytest tests/test_api_route.py -q` · thử bằng `http://127.0.0.1:8000/docs`
- 🧠 Tách API / service / thuật toán; vì sao request không lưu trạng thái.

### T52 — UI: chọn hai điểm, vẽ hai tuyến, bảng so sánh
- 👤 Minh · ⏱ 4 h · ⛓ T51, T32
- **Việc cần làm:** click lần 1 = điểm đi, lần 2 = điểm đến; nút **Tìm đường**, **Đảo chiều**, **Xóa**; vẽ tuyến Dijkstra và A*; bảng: chi phí (s, phút), quãng đường (m), node mở rộng, thời gian tính (ms), "Chi phí trùng khớp: có/không"; hiển thị trạng thái đang tính/lỗi; bỏ qua response cũ nếu đã có request mới.
- 📁 `frontend/src/main.ts`, `panel.ts`, `layers.ts`, `api.ts`
- 📦 Tìm đường trên web.
- ✅ Checklist UI-1…UI-4 trong PROGRESS.md đạt.
- ▶ Thủ công theo checklist; `npm run build` không lỗi.
- 🧠 Hai nhãn thời gian khác nhau; vì sao phải bỏ response cũ.

### T53 — UI: lớp node mở rộng và kịch bản
- 👤 Minh (Tiến hỗ trợ) · ⏱ 3 h · ⛓ T52
- **Việc cần làm:** gửi `trace_limit`; vẽ chấm node mở rộng của từng thuật toán (bật/tắt), nhãn "K node mở rộng đầu tiên" khi bị cắt; dropdown kịch bản từ `/api/dataset`; vẽ vùng ùn tắc.
- 📁 `frontend/src/*.ts`
- 📦 Minh họa vùng tìm kiếm.
- ✅ Checklist UI-5, UI-6 đạt; với case demo chính, trace **không** bị cắt (chọn `trace_limit` đủ lớn).
- ▶ Thủ công.
- 🧠 Vì sao trace bị cắt có thể làm vùng Dijkstra trông nhỏ hơn thực tế.

### T54 — UI: đóng đoạn đường và báo không có đường
- 👤 Minh + Tiến · ⏱ 3 h · ⛓ T52, T41
- **Việc cần làm:** bấm vào một cạnh → popup "Đóng một chiều / Đóng đoạn (hai chiều)"; tô đỏ cạnh đóng; tự tìm lại; tuyến cũ hiện mờ "kế hoạch trước khi đóng đường"; khi `no_path` thì hiện thông báo, không vẽ đường; nút "Mở lại tất cả".
- 📁 `frontend/src/*.ts`
- 📦 Đóng đường trên web.
- ✅ Checklist UI-7, UI-8 đạt.
- ▶ Thủ công.
- 🧠 Chặn theo edge id, không theo tên đường.

### T55 — Case demo và kiểm thử thủ công
- 👤 Bảo · ⏱ 2–3 h · ⛓ T54
- **Việc cần làm:** `data/demo/cases.json` (cặp điểm, kịch bản, cạnh đóng) cho các bước 1–7 ở PROJECT_BRIEF mục 7; UI nạp case từ file (Minh hỗ trợ nếu cần); chạy toàn bộ checklist UI, chụp màn hình, ghi lỗi vào PROGRESS.md.
- 📁 `data/demo/cases.json`, `docs/PROGRESS.md`, `docs/img/` (ảnh)
- 📦 Bộ case demo + biên bản kiểm thử.
- ✅ Mọi case chạy được và cho kết quả như mô tả; lỗi (nếu có) được ghi rõ.
- ▶ Thủ công theo checklist.
- 🧠 Mỗi case minh họa điều gì (RQ nào).

---

## M7 — Benchmark và tăng quy mô

### T60 — Bộ chạy benchmark và 1.000 truy vấn vùng demo
- 👤 Tiến · ⏱ 4 h · ⛓ T33
- **Việc cần làm:** theo [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) mục 2–3: sinh cặp có seed và phân tầng; lưu `queries.csv` trước khi đo; warm-up; lặp R lần, đổi thứ tự thuật toán; ghi `measurements.csv` và `env.json`; tắt trace.
- 📁 `scripts/run_benchmarks.py`, `results/<run_id>/`
- 📦 CSV đo thật cho E2.
- ✅ 1.000 cặp chạy xong; 100% cặp khớp chi phí; file có đủ cột ở EXPERIMENT_PLAN mục 3.3.
- ▶ `python scripts/run_benchmarks.py --suite demo --pairs 1000 --seed 42`
- 🧠 Median và p95; vì sao không lấy trung bình các tỉ số.

### T61 — Cắt lồng nhau cho thí nghiệm tăng quy mô
- 👤 Minh (Tiến hỗ trợ) · ⏱ 3 h · ⛓ T31
- **Việc cần làm:** `scripts/make_crops.py`: từ `outer.graphml` cắt 4 hình vuông nửa cạnh 1 / 2 / 3 / 4,5 km **[Đề xuất]**; chọn SCC lồng nhau (DATA_MODEL mục 8.4); xuất JSON + manifest từng kích thước. Chạy pilot 20 truy vấn dài ở kích thước lớn nhất: nếu median Dijkstra > ~1 s thì bỏ hoặc giảm kích thước đó.
- 📁 `scripts/make_crops.py`, `data/processed/crop_*.json`
- 📦 4 đồ thị lồng nhau + bảng `|V|`, `|E|` đo được.
- ✅ Bảng kích thước dán vào EXPERIMENTS.md; xác nhận SCC nhỏ nằm trong SCC lớn.
- ▶ `python scripts/make_crops.py` · kiểm tra bảng in ra
- 🧠 Vì sao cắt từ một lần tải thay vì tải 4 lần; vì sao vẽ biểu đồ theo `|V|` đo được chứ không theo bán kính.

### T62 — Chạy thí nghiệm tăng quy mô
- 👤 Tiến · ⏱ 3 h · ⛓ T60, T61
- **Việc cần làm:** workload fixed trips (250 cặp dùng chung) + growing trips (250 cặp mỗi kích thước) theo EXPERIMENT_PLAN mục 6.
- 📁 `scripts/run_benchmarks.py`, `results/<run_id>/`
- 📦 CSV E3 · ✅ Đủ 4 kích thước (hoặc ghi rõ kích thước bị bỏ và lý do) · ▶ `python scripts/run_benchmarks.py --suite scaling --seed 42`
- 🧠 Fixed trips đo ảnh hưởng của bản đồ lớn hơn; growing trips đo cả bản đồ lớn hơn lẫn chuyến đi dài hơn.

### T63 — Thí nghiệm ùn tắc và đóng đường
- 👤 Tiến (Bảo chạy lại để kiểm tra) · ⏱ 3 h · ⛓ T60, T41, T42
- **Việc cần làm:** theo EXPERIMENT_PLAN mục 7: cùng tập cặp, chạy dưới từng kịch bản; đóng cạnh theo quy tắc cố định; ghi tính khả thi, chi phí, node mở rộng, thời gian.
- 📁 `scripts/run_benchmarks.py`, `results/<run_id>/`
- 📦 CSV E4 · ✅ Có cả case còn đường và case không còn đường · ▶ `python scripts/run_benchmarks.py --suite scenario --seed 42`
- 🧠 Vì sao cận dưới lỏng hơn khi có ùn tắc.

### T64 — Vẽ biểu đồ
- 👤 Bảo (Tiến hỗ trợ) · ⏱ 3 h · ⛓ T60 (định dạng CSV)
- **Việc cần làm:** `scripts/plot_results.py <run_dir>` vẽ các hình ở EXPERIMENT_PLAN mục 10; thử trước bằng CSV nhỏ sinh từ fixture (ghi rõ là dữ liệu thử, không đưa vào báo cáo).
- 📁 `scripts/plot_results.py`, `results/<run_id>/fig_*.png`
- 📦 Biểu đồ · ✅ Trục có đơn vị; chú thích ghi số cặp và dataset · ▶ `python scripts/plot_results.py results/<run_id>`
- 🧠 Đọc biểu đồ log–log; boxplot.

### G1 — Cổng MVP: quyết định tích hợp tour
- 👤 Tiến (cả nhóm họp) · ⏱ 1 h · ⛓ T33, T41, T55, T60, T62
- **Mục tiêu:** quyết định ngày 05/11 có làm M8b (tour trên API/UI) hay không.
- **Việc cần làm:** kiểm tra từng điều kiện ở [ROADMAP.md](ROADMAP.md) mục 3; ghi quyết định và lý do vào issue và PROGRESS.md.
- 📁 `docs/PROGRESS.md`
- 📦 Quyết định có ghi lại.
- ✅ Mọi điều kiện được đánh dấu đạt/không đạt kèm bằng chứng (link PR, `run_id`).
- ▶ Review biên bản họp.
- 🧠 Quản lý phạm vi: vì sao cắt bớt tốt hơn trễ hạn.

### T65 — Ghi kết quả vào EXPERIMENTS.md
- 👤 Tiến + cả nhóm · ⏱ 3 h · ⛓ T62, T63, T64
- **Việc cần làm:** điền bảng ở EXPERIMENT_PLAN mục 9 bằng số đo thật; mỗi bảng ghi `run_id`, `dataset_id`, máy đo; viết phần diễn giải và các trường hợp A* không có lợi.
- 📁 `docs/EXPERIMENTS.md`
- 📦 Kết quả cho essay · ✅ Mọi số có `run_id` truy ngược được · ▶ Review chéo: một người khác chạy lại một bảng và ra số cùng bậc
- 🧠 Phân biệt số đo với diễn giải.

---

## M8 — Tour (mở rộng E1)

### T70 — Tour trên ma trận: chi phí, NN, 2-opt có hướng
- 👤 Duy Anh · ⏱ 3–4 h · ⛓ T00 (không cần dữ liệu thật) · bắt đầu sau T22
- **Việc cần làm:** `tour_cost(D, order)` (kho cố định đầu/cuối); `nearest_neighbor(D)` với tie-break theo chỉ số; `two_opt(D, order)` tính lại **toàn bộ** chi phí cho mỗi ứng viên; chọn tour rẻ nhất trong {thứ tự nhập, NN, NN+2-opt}. Test: 1 điểm; ma trận bất đối xứng; một ma trận nhỏ tự dựng làm ví dụ phản chứng: công thức delta đối xứng dự đoán tour rẻ hơn nhưng chi phí tính lại toàn bộ lại đắt hơn (script proposal có ví dụ 17 → 13 → 20 ở backup slide B1, nhưng repo không có ma trận gốc nên phải dựng lại và kiểm tra); 2-opt không làm tăng chi phí; giữ đủ điểm.
- 📁 `backend/app/algorithms/tour.py`, `tests/test_tour.py`
- 📦 Thuật toán tour · ✅ Test xanh · ▶ `pytest tests/test_tour.py -q`
- 🧠 TSP bất đối xứng; vì sao 2-opt chỉ cho cực trị địa phương; vì sao đảo đoạn làm đảo chiều các chặng bên trong.

### T71 — Held–Karp làm đối chứng
- 👤 Duy Anh · ⏱ 2–3 h · ⛓ T70
- **Việc cần làm:** `held_karp(D)` cho n ≤ 10; test so với duyệt mọi hoán vị khi n ≤ 7; đo thời gian n = 4, 6, 8, 10.
- 📁 `backend/app/algorithms/tour.py`, `tests/test_tour.py`
- 📦 Lời giải tối ưu cho case nhỏ · ✅ Khớp duyệt toàn bộ · ▶ `pytest tests/test_tour.py -q`
- 🧠 Công thức `DP[S, j]`; độ phức tạp `O(2^n · n²)`.

### T72 — Ma trận chi phí từ đồ thị và `/api/tour` *(chỉ sau G1)*
- 👤 Tiến · ⏱ 3–4 h · ⛓ T70, T51, G1
- **Việc cần làm:** Dijkstra một nguồn tới nhiều đích (dừng khi đã pop đủ các đích) để xây từng hàng; kiểm tra mọi cặp hữu hạn, nếu không thì trả `infeasible_under_model` + danh sách điểm lỗi; ghép tuyến các chặng; endpoint `/api/tour`.
- 📁 `backend/app/services/tour.py`, `backend/app/api/*.py`, `tests/test_api_tour.py`
- 📦 API tour · ✅ Chi phí tour bằng tổng chi phí các chặng đã dựng · ▶ `pytest tests/test_api_tour.py -q`
- 🧠 Vì sao không dùng khoảng cách thẳng cho ma trận.

### T73 — UI tour tối giản
- 👤 Minh · ⏱ 3 h · ⛓ T72
- **Việc cần làm:** preset kho + 5 điểm từ `cases.json`; 3 thẻ Thứ tự nhập / NN / NN + 2-opt; marker đánh số theo thẻ được chọn.
- 📁 `frontend/src/*.ts` · 📦 Demo tour · ✅ Bước 9 của kịch bản demo chạy được · ▶ Thủ công
- 🧠 Hai tầng của bài toán giao hàng.

### T74 — Benchmark tour
- 👤 Tiến (Bảo chạy) · ⏱ 2–3 h · ⛓ T71, T72
- **Việc cần làm:** EXPERIMENT_PLAN mục 8.
- 📁 `scripts/run_benchmarks.py` · 📦 CSV E5 · ✅ Bảng improvement và gap có số đo · ▶ `python scripts/run_benchmarks.py --suite tour --seed 42`
- 🧠 Improvement % và gap %.

---

## M9 — Hoàn thiện

### T80 — Đóng băng tính năng và chạy trên máy thứ hai
- 👤 Bảo · ⏱ 2–3 h · ⛓ T54, T55, G1
- **Ghi chú:** nếu G1 quyết định làm M8b thì chờ thêm T73 (UI tour) xong mới đóng băng; phụ thuộc này không ghi ở dòng ⛓ vì M8b có thể không làm.
- **Việc cần làm:** 10/11 đóng băng tính năng; clone repo sạch trên máy khác, làm đúng theo README (tải dataset từ Release, kiểm tra hash), chạy demo; ghi mọi bước bị vướng.
- 📦 Biên bản chạy máy thứ hai · ✅ Chạy được mà không cần ai sửa tay; hoặc README đã được sửa · ▶ Thủ công
- 🧠 Tái lập là gì.

### T81 — Đồng bộ tài liệu
- 👤 Tiến · ⏱ 2 h · ⛓ T65
- **Việc cần làm:** cập nhật README (cách chạy, kết quả thật, giới hạn); cập nhật DEMO.md theo thứ tự demo mới; ghi trong TOPIC.md những điểm đã đổi (trỏ tới PROJECT_BRIEF mục 4); điền `docs/ALGORITHMS.md`.
- 📦 Tài liệu khớp code · ✅ Không còn mô tả chức năng chưa làm như đã làm · ▶ Review chéo
- 🧠 —

### T82 — Tập demo và quay video dự phòng
- 👤 Minh + Bảo · ⏱ 2 h · ⛓ T55, T80
- **Việc cần làm:** chạy kịch bản demo 3 lần với đồng hồ; quay màn hình bản tốt nhất; kiểm tra checklist DEMO.md mục 3.
- 📦 Video + checklist · ✅ Demo ≤ 4 phút · ▶ Thủ công
- 🧠 Mỗi bước demo trả lời câu hỏi nghiên cứu nào.

### T83 — Essay: phương pháp, kết quả, giới hạn
- 👤 Cả nhóm (Tiến điều phối) · ⏱ nhiều buổi · ⛓ T65
- **Việc cần làm:** theo khung TOPIC.md mục 21.1; mỗi người viết phần mình làm; mọi số liệu lấy từ EXPERIMENTS.md kèm `run_id`; chứng minh heuristic ở dạng phác thảo có trích dẫn.
- 📦 Bản nháp essay · ✅ 10 trang double spaced, có bìa đủ tên/MSSV · ▶ Review chéo
- 🧠 Toàn bộ.
