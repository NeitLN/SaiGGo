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

## 6. Kế hoạch tuần 2 (26/10–01/11) — **[Đề xuất, nhóm duyệt ở buổi họp]**

Mục tiêu tuần: **walking skeleton chạy trên 2 máy (29/10)** và **Dijkstra/A* khớp NetworkX trên dữ liệu thật (31/10)**. Người tích hợp: **Tiến**. Chỉ người tích hợp sửa STATUS.md/ROADMAP.md; người làm ghi bằng chứng trong PR của mình.

Mức chặn của phụ thuộc:
- **bắt đầu**: phải có contract/tiền đề trước khi viết code;
- **tích hợp**: code trước được với fixture/contract, chờ bên kia xong mới ghép;
- **chấp nhận**: chỉ được tính xong sau khi kiểm chung.

| Người | Task theo thứ tự (ID, ngày mục tiêu) | Phụ thuộc và mức chặn | Review |
|---|---|---|---|
| Duy Anh | T01 (26, *trễ từ 24/10*) → T10 (26) → T11 (27) → T20 (28) → T21, T22 (29–30) → T33 cùng Tiến (31) | T11 ← T01 *bắt đầu*, ← T03 *chấp nhận* · T20 ← T11 *bắt đầu* · T33 ← T22, T31 *bắt đầu* | Tiến |
| Minh | Merge #46, #47 + đưa `outer.graphml` lên Release (26) → T31 cùng Tiến (26–27) → T14 (27–28) → T32 (29–30) → T50 (31–01/11) | T31 ← T30 *bắt đầu*, ← T01 *tích hợp* (viết theo đặc tả DATA_MODEL mục 2, ghép khi `load_graph` có) · T14 ← contract v1 *bắt đầu*, ← T13 *tích hợp* · T32 ← T31 *tích hợp* (vẽ `mini.json` trước) | Tiến; T31 do Duy Anh review |
| Bảo | T03 (26, *trễ từ 24/10*) → review PR tài liệu → T15 (29) → T42 (30–31) | T15 ← T13, T14 *bắt đầu* · T42 ← T40 *bắt đầu*, ← T33 *chấp nhận* | Duy Anh (T03), Tiến |
| Tiến | Merge #45 → #46 → #47 (26) → T00 (26) → T12 (27) → T13 (27–28) → T40 (29–30) → T41 (30–31) · tích hợp và kiểm chung mỗi lần merge | T13 ← T11 *tích hợp* · T40 ← T10 *bắt đầu*, ← T11 *tích hợp* | Duy Anh; T33 do Minh review |

Dời việc so với `schedule.csv`: T01, T03 trễ 2 ngày (chưa bắt đầu); T70/T71 (tour, Duy Anh) dời sang tuần 3 vì tuần 2 của Duy Anh đã kín.
Sau khi nhóm duyệt: cập nhật ⛓ trong TASKS.md và `schedule.csv`, chạy `create_backlog.py --sync` và `setup_project.py --sync`.
