# SaiGo — Roadmap

Lập ngày 23/10/2026. Mốc của giảng viên (tentative, theo Project_Intructions_261.pdf): **12/11 final ready · 19/11 thuyết trình 15 phút · 22/11 nộp ETC**.

Nguyên tắc:

- Mỗi mốc kết thúc bằng **một kết quả chạy được** và một lệnh/thao tác để chứng minh.
- Hai track song song từ ngày đầu, gặp nhau ở M4:
  - **Track A (thuật toán):** đồ thị mẫu tính tay được → Dijkstra → A*.
  - **Track D (dữ liệu):** cài OSMnx trên Windows → tải dữ liệu thật → hiện lên bản đồ.
- Định dạng đồ thị `saigo-graph/1` ([DATA_MODEL.md](DATA_MODEL.md) mục 2) được chốt ở T01, nên hai track cùng nhắm một định dạng.
- Ngày trong bảng là **[Đề xuất]**. Mỗi mốc chừa thời gian dự phòng, vì cài đặt và gỡ lỗi thường lâu hơn dự kiến.

## 1. Tổng quan

```text
Ngày     23 24 25 26 27 28 29 30 31 01 02 03 04 05 06 07 08 09 10 11 12
Track A  M0 M1 M1 M2 M2 M2
Track D  M0 M3 M3 M3 M3 M3
Skeleton             MW MW MW                      (thêm 25/10: nối mọi tầng trên mini.json trước khi có dữ liệu thật)
Chung                   M4 M4 M5 M5 M6 M6 M6 M6
Bench                                  M7 M7 M7 M7 M7
Tour E1                 M8a(thuật toán trên ma trận)     │ M8b tích hợp
Hoàn thiện                                                  M9 M9 M9 M9 M9
Cổng                                             G1(05/11)          Freeze(10/11) Final(12/11)
```

## 2. Các mốc

| Mốc | Thời gian | Kết quả chạy được | Lệnh / cách chứng minh | Task |
|---|---|---|---|---|
| **M0** Nền móng | 23–24/10 | Khung chạy trên Windows; fixture `mini.json` nạp được; OSMnx tải được một vùng nhỏ | `pytest -q` xanh; `python scripts/prepare_data.py --smoke` in số node/cạnh | T00–T03 |
| **M1** Dijkstra trên đồ thị mẫu | 24–26/10 | CLI tìm đường trên `mini.json`, in tuyến, chi phí, số node mở rộng khớp bảng tính tay | `python -m app.cli route --graph tests/fixtures/mini.json --from S --to T --algo dijkstra` → `cost 80.0 s, expanded 5` | T10–T12 |
| **MW** Walking skeleton *(thêm 25/10)* | 27–29/10 | Bấm 2 điểm trên bản đồ → `/api/route` → Dijkstra trên `mini.json` → vẽ tuyến; chạy được trên máy thứ hai | `pytest tests/test_api_route.py`; thao tác ✅ của T14 trên máy Tiến và máy Bảo | T13–T15 |
| **M2** A* + đối chứng | 26–28/10 | A* cho cùng chi phí, ít node hơn; test ngẫu nhiên khớp NetworkX | `pytest tests/test_astar.py tests/test_oracle_networkx.py -q` xanh; CLI `--algo astar` → `expanded 2` | T20–T22 |
| **M3** Dữ liệu thật trên bản đồ *(song song M0–M2)* | 23–28/10 | File JSON vùng demo + manifest; trình duyệt vẽ mạng đường thật | `python scripts/prepare_data.py` sinh `data/processed/*.json`; mở `http://localhost:5173` thấy mạng đường | T30–T32 |
| **M4** Tìm đường trên dữ liệu thật | 28–29/10 | CLI chạy Dijkstra/A* trên đồ thị thật; 200 cặp khớp NetworkX; báo cáo heuristic (`c`, `v_max`) | `python -m app.cli route --graph data/processed/<id>.json --from-latlon ... --to-latlon ...`; `pytest -m realdata` | T33 |
| **M5** Ùn tắc & đóng đường | 29–31/10 | Snapshot với vùng ùn tắc và cạnh đóng; CLI cho thấy tuyến đổi, `no_path` khi cần | `pytest tests/test_scenario.py -q`; CLI `--scenario peak-center --block 123` | T40–T42 |
| **M6** Bản đồ tương tác | 31/10–04/11 | Bấm 2 điểm → 2 tuyến + bảng so sánh + chấm node mở rộng; chọn kịch bản; bấm để đóng đoạn; báo không có đường | Checklist thủ công UI-1…UI-8 trong [PROGRESS.md](PROGRESS.md); `pytest tests/test_api_route.py` | T50–T55 |
| **M7** Benchmark & tăng quy mô | 02–06/11 | CSV đo thật + biểu đồ: 1.000 cặp vùng demo, 4 kích thước đồ thị, thí nghiệm ùn tắc/đóng đường | `python scripts/run_benchmarks.py --suite all`; `python scripts/plot_results.py results/<run_id>` | T60–T65 |
| **G1** Cổng MVP | **05/11** | Quyết định có tích hợp tour vào API/UI hay không | Đủ điều kiện ở mục 3 | — |
| **M8** Tour (E1) | a) 29/10–02/11 · b) 05–08/11 | a) NN, 2-opt có hướng, Held–Karp chạy trên ma trận; b) `/api/tour`, preset kho + 5 điểm, benchmark tour | a) `pytest tests/test_tour.py`; b) `python scripts/run_benchmarks.py --suite tour` | T70–T74 |
| **M9** Hoàn thiện | 08–12/11 | Đóng băng tính năng 10/11; chạy lại trên máy thứ hai theo README; video demo dự phòng; số liệu vào essay | Checklist ở T80–T83 | T80–T83 |

Sau 12/11: 13–18/11 làm slide và tập dượt; 19/11 thuyết trình; 20–22/11 nộp theo thông báo cuối.

## 3. Cổng G1 (05/11) — điều kiện để tích hợp tour

Chỉ tích hợp tour vào API/UI (M8b) khi **tất cả** điều kiện sau đạt:

- [ ] Dijkstra và A* khớp NetworkX trên fixture, trên đồ thị ngẫu nhiên và trên 200 cặp dữ liệu thật.
- [ ] Đóng đường không bao giờ dùng cạnh bị đóng (có test); `no_path` hiển thị đúng.
- [ ] Demo M6 chạy trọn checklist trên laptop demo.
- [ ] Benchmark 1.000 cặp và ít nhất 2 kích thước của thí nghiệm tăng quy mô đã có CSV thật.

Nếu chưa đạt: dừng M8b, dồn người vào phần còn thiếu, và giữ tour ở mức thuật toán + benchmark CLI (nếu M8a đã xong). Ghi quyết định vào PROGRESS.md.

## 4. Đường găng và rủi ro

| Rủi ro | Phát hiện sớm ở | Phương án |
|---|---|---|
| OSMnx không cài được trên Windows | T02 (ngày 23–24/10) | Môi trường conda-forge riêng cho bước dữ liệu; app không cần OSMnx |
| Đảo lat/lon, sai đơn vị → A* sai | T22, T31 (`c < 0,999`) | Test đặt tên trường; điều tra cạnh vi phạm |
| Vẽ mạng đường quá chậm | T32 | Thu nhỏ vùng demo; Canvas renderer |
| Python quá chậm ở đồ thị lớn | T61 (pilot) | Dừng ở kích thước có median Dijkstra ≈ 1 s; chỉ báo cáo các kích thước đã đo |
| Một người làm chính cả hai track | Lịch M0–M3 | Track A do Duy Anh làm chính, Track D do Minh làm chính; Tiến review và hỗ trợ khi bị chặn |
| Trễ sau 05/11 | G1 | Thứ tự cắt ở PROJECT_BRIEF mục 3.2 |

## 5. Quyết định đắt nếu đổi

Đổi những quyết định này sau khi đã có code hoặc số liệu dựa trên chúng thì phải làm lại nhiều task. Mỗi mục phải chốt **trước task đầu tiên** cần nó, kể cả khi chưa tới tuần đó. Trạng thái và bằng chứng của từng mục cập nhật ở [STATUS.md](STATUS.md).

| # | Quyết định | Việc phải chờ (chốt trước việc này) | Hạn chốt | Nếu thiếu bằng chứng thì kiểm bằng | Trạng thái |
|---|---|---|---|---|---|
| Q1 | Định dạng `saigo-graph/1` và cách đánh ID cạnh `(u, v, key)` ([DATA_MODEL](DATA_MODEL.md) mục 2) | T11 (bắt đầu), T31 (bắt đầu), T41, T51 | 24/10 | `mini.json` nạp được bằng `load_graph` (T01) | **Trễ**: chờ T01 |
| Q2 | Bản dữ liệu thô dùng chung (sha256 `24a28327…`) và nơi lưu cho cả nhóm | T31, T61, mọi benchmark | 26/10 | Hai máy tải từ Release ra cùng sha256 | Đã tải (PR #47); chưa chia sẻ |
| Q3 | Vùng demo (nửa cạnh 2 km) và các kích thước của thí nghiệm tăng quy mô | T31, T61, T62 | 27/10 (T61 chốt sau pilot) | Pilot T61: đo median Dijkstra ở kích thước lớn nhất | **[Đề xuất]**, chờ họp |
| Q4 | Bảng tốc độ `speeds.json` (cũng quyết định `v_max`) | T22, T33, T60 | 28/10 | `check-heuristic` trên đồ thị thật (T22) | **[Giả định]**, chờ họp |
| Q5 | Mô hình ùn tắc (`max α`, trung điểm cạnh) và cách đóng đoạn (cạnh đối) ([DATA_MODEL](DATA_MODEL.md) mục 4) | T40, T41, T63 | 29/10 | Test trên `mini.json`: vùng ùn tắc đổi tuyến, nhân đều không đổi | Đã ghi trong DATA_MODEL; chưa có code |
| Q6 | Contract `/api/route` (request/response, [ARCHITECTURE](ARCHITECTURE.md) mục 4) | T51 và T52 (T52 code trước được với contract này) | 30/10 | Test API với fixture (T51) | Đã ghi trong ARCHITECTURE; chưa có code |
| Q7 | Môi trường đo: phiên bản Python và thư viện được khóa; quy trình đo ([EXPERIMENT_PLAN](EXPERIMENT_PLAN.md) mục 3) | T60, T62, T63 | 01/11 | Chạy lại một bộ nhỏ trên máy thứ hai ra cùng chi phí | **Mở**: chưa khóa phiên bản |
| Q8 | Có tích hợp tour vào API/UI hay không (cổng G1) | T72, T73, T74 | 05/11 | Điều kiện ở mục 3 | Chưa tới hạn |

## 6. Kế hoạch tuần 2 (26/10–01/11) — **[Đề xuất, nhóm duyệt ở buổi họp 26/10]**

Chương trình họp: [team/meetings/2026-10-26-agenda.md](team/meetings/2026-10-26-agenda.md) · Đề xuất đổi phạm vi: [proposals/2026-10-26-pham-vi.md](proposals/2026-10-26-pham-vi.md) · Phiếu giao việc từng task: [tasks/](tasks/).

**Điều kiện của tuần:** Duy Anh **không tham gia** tuần 2. **Đã chốt 26/10 (Tiến):** T01, T10, T11, T20 của Duy Anh chuyển sang Tiến để kịp tiến độ. Mọi phép tính dưới đây coi sức làm của Duy Anh là 0 cho tới khi có ngày cụ thể. Sức làm: Tiến ~15 giờ (kiêm người tích hợp), Minh ~11 giờ, Bảo ~11 giờ. Review, tích hợp và họp đều được tính vào số giờ này.

### 6.1. Mục tiêu tuần (mỗi mục kiểm được bằng lệnh hoặc thao tác)

1. **Walking skeleton (MW) chạy trên 2 máy trước hết 29/10:** bấm 2 điểm → `/api/route` → Dijkstra trên `mini.json` → vẽ tuyến; Bảo làm lại được trên máy mình từ code đã merge.
2. **M1 + M2 trên đồ thị mẫu:** Dijkstra và A* khớp đáp án tính tay của T03; CLI chạy được cả hai thuật toán.
3. **Dữ liệu đóng băng dùng chung (thay cho M3 cũ):** `outer.graphml` lên Release, hai máy kiểm cùng sha256; đồ thị vùng demo của T31 được `load_graph` (T01) đọc được.
4. **Buổi họp chốt** 3 quyết định phạm vi và các quyết định Q1–Q5, Q7 (xem chương trình họp).

Không thuộc tuần 2, đã dời sang tuần 3: vẽ mạng đường thật (T32), snap có ngưỡng (T50), đối chứng NetworkX trên dữ liệu thật (T22, T33), ùn tắc và đóng đường (T40–T42).

### 6.2. Phân công và ngân sách giờ

| Người | Task (giờ, ngày mục tiêu) | Review cho người khác, họp, tích hợp | Dự phòng | Tổng |
|---|---|---|---|---:|
| **Tiến** | [T01](tasks/T01-graph-format.md) định dạng + fixture + `load_graph` 3 (26–27, *trễ*) · [T10](tasks/T10-geo.md) hàm địa lý 2 (26–27, *trễ*) · [T11](tasks/T11-dijkstra.md) Dijkstra 4 (27–28) · [T13](tasks/T13-api-skeleton.md) API skeleton 3 (28–29) · [T20](tasks/T20-astar.md) A* 3 (30–31) | 5: họp; review #54, T14, T12, T34; merge, sync, STATUS | 0 | **20** ⚠️ |
| **Minh** | [T34](tasks/T34-release-data.md) Release + merge #46→#47→#53 2 (26) · [T14](tasks/T14-map-skeleton.md) bản đồ skeleton 3 (27–28) | 2: họp; review T13, T20 | 1 | 8 (trống 3) |
| **Bảo** | [T15](tasks/T15-second-machine.md) chạy MW trên máy thứ hai 2 (29) · [T12](tasks/T12-cli.md) CLI có cả A* 2 (30–31) | 2: họp; review T01, T10, T11 | 3: chỉ dùng cho [T21](tasks/T21-oracle.md) (31/10–01/11) **khi MW đã đạt và T20 đã có** | 9 (trống 2) |
| Duy Anh | — | — | — | 0 |

**⚠️ Tiến đang được giao 20 giờ, vượt sức làm 15 giờ.** Đề xuất giảm tải, nhóm chốt ở buổi họp:
1. Chuyển **T13** (API skeleton, 3 giờ) sang **Minh**, người đang trống đúng 3 giờ. Minh khi đó làm trọn lát dọc của skeleton (API + bản đồ), Tiến review.
2. Chuyển **T12** (CLI) sang Bảo, như đã ghi ở bảng trên.

Làm cả hai thì Tiến còn khoảng 17 giờ; muốn xuống 15 giờ thì T20 có thể dời sang 02/11 (đầu tuần 3).

### 6.3. Phụ thuộc và mức chặn

Mức chặn:
- **bắt đầu**: phải có tiền đề trước khi viết code;
- **tích hợp**: code trước được theo interface/contract, chờ bên kia merge mới ghép;
- **chấp nhận**: chỉ được tính xong sau khi kiểm chung.

| Task | Phụ thuộc (mức chặn) |
|---|---|
| T01 | Interface `Graph`/`GraphMeta` được duyệt ở buổi họp (bắt đầu) |
| T10 | — |
| T11 | T01 (tích hợp: code theo interface đã duyệt, ghép khi T01 merge) · T03/#54 (chấp nhận) |
| T13 | T11 (tích hợp) · T10 (tích hợp: tạm dùng hàm nội bộ, đổi sang `geo.haversine_m` khi T10 merge) |
| T14 | Contract `/api/route` v1 (bắt đầu, đã chốt) · T13 (tích hợp) |
| T15 | T13 và T14 đã merge (bắt đầu) |
| T20 | T11 và T10 (bắt đầu) |
| T12 | T11 (bắt đầu) · T20 (chấp nhận: phải gọi được cả A* mới tính là xong) |
| T21 | T20 (bắt đầu) |
| T34 | — |

### 6.4. Ai sở hữu file nào trong tuần 2

Hai task song song không sửa cùng một file. Khi cần sửa file của người khác, ghi vào PR: "cần đổi X ở file Y, nhờ <chủ file>".

| File / tài nguyên | Chủ sở hữu tuần 2 | Ghi chú |
|---|---|---|
| `backend/app/graph/model.py`, `tests/fixtures/mini.json` | Tiến (T01) | Minh và Bảo chỉ đọc |
| `backend/app/graph/geo.py` | Tiến (T10) | |
| `backend/app/algorithms/*`, `backend/app/graph/scenario.py` | Tiến (T11, T20) | `Snapshot` chỉ có **một** định nghĩa, trong `graph/scenario.py` (T11 tạo cùng `baseline_snapshot()`); T40 (tuần 3) thêm `Scenario` và `build_snapshot` vào cùng file, không tạo kiểu mới |
| `backend/app/main.py`, `api/*`, `services/routing.py` | Tiến (T13) | Snap tạm là hàm `nearest_node_naive()` trong `services/routing.py`; T50 (tuần 3) thay đúng hàm này |
| `backend/app/cli.py` | Bảo (T12) | Sang tuần 3, T22 rồi T40 lần lượt sửa |
| `frontend/src/*` | Minh (T14) | Thứ tự tiếp theo: T14 → T52 → T54 |
| Release `data-raw-20261024`, `data/processed/*manifest.json` | Minh (T34) | Không ai tải lại OSM để thay thế |
| `docs/STATUS.md`, `ROADMAP.md`, `TASKS.md`, `tracking/schedule.csv` | Tiến (người tích hợp) | Người làm ghi bằng chứng trong PR; chỉ sửa dòng PROGRESS của task mình |

### 6.5. Các mốc kiểm trong tuần

| Ngày | Phải có | Ai kiểm | Nếu không đạt |
|---|---|---|---|
| **26/10** (họp) | 3 quyết định phạm vi được chốt; interface `Graph`/`Snapshot`/`SearchResult` được duyệt; Release có file, Tiến tải về ra đúng sha256 `24a28327…`; hàng chờ PR (#46, #47, #53, #52, #55) được merge; #54 được review | Tiến | Ghi vào biên bản, dời việc phụ thuộc |
| **27/10** tối | T01 merge; `load_graph` đọc được `mini.json` và đồ thị vùng demo của T31 | Bảo (review), Tiến | Tiến và Minh gỡ ngay sáng 28/10; T11 vẫn code theo interface |
| **28/10** tối | Đường mỏng API → UI chạy được trên máy Tiến (dù test chưa đủ) | Tiến, Minh | Thu gọn T14: chỉ vẽ tuyến, chưa hiện bảng |
| **29/10** tối | T13 + T14 merge; Bảo làm lại thao tác ✅ của T14 trên máy mình (T15) | Bảo | Ghi lỗi thành issue *Lỗi*; MW chưa đạt thì T21 không bắt đầu |
| **01/11** (họp tuần) | T20 có bằng chứng (`expanded = 2` trên `mini.json`); T12 chạy được cả hai thuật toán; xem lại ngân sách tuần 3; xác nhận Duy Anh có quay lại không, từ ngày nào, bao nhiêu giờ | Cả nhóm | Kích hoạt phương án cắt đã duyệt ([đề xuất phạm vi](proposals/2026-10-26-pham-vi.md) mục 4) |

**Quy tắc merge tuần 2:** PR có approve **còn hiệu lực** và CI xanh thì tác giả merge ngay trong ngày. Với PR xếp chồng: sau khi PR bên dưới merge, bấm *Update branch*; nếu approve bị hủy thì nhờ approve lại ngay, không để qua ngày.

### 6.6. Dời việc so với `schedule.csv`

| Task | Tuần gốc | Đề xuất | Lý do |
|---|---|---|---|
| T01, T10 | 1 (Duy Anh) | 2 (Tiến, **đã chuyển 26/10**) | Duy Anh không tham gia tuần 2; giữ hạn gốc trên GitHub để thấy là trễ |
| T11, T20 | 2 (Duy Anh) | 2 (Tiến, **đã chuyển 26/10**) | Như trên |
| T21 | 2 (Duy Anh) | 2 nếu Bảo còn dự phòng, không thì 3 | Không để T21 chiếm phần dự phòng sửa lỗi |
| T22, T33 | 2 | 3 (02–03/11) | Phụ thuộc T20 và dữ liệu đóng băng |
| T32, T50 | 2 | 3 | Không đủ sức của Minh; T13 đã nạp đồ thị khi khởi động |
| T40, T41, T42 | 2 | 3 | Phụ thuộc T11; Tiến đã kín |
| T70–T74 (tour) | 2–3 | **Đề xuất cắt khỏi phạm vi cam kết** | Xem đề xuất phạm vi |

Sau khi nhóm duyệt, Tiến:
1. sửa ⛓, người phụ trách và ngày trong `TASKS.md` và `tracking/schedule.csv`;
2. thêm T34;
3. chạy `create_backlog.py --sync` và `setup_project.py --sync`.
