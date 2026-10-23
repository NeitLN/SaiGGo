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
