# Thuật toán

Công thức, pseudocode và điều kiện đúng cho Dijkstra, A*, Nearest Neighbor, 2-opt.
Đặc tả gốc: [TOPIC.md](TOPIC.md) mục 9–10. Cập nhật tài liệu này khi từng module được cài và kiểm thử.

## Chạy tay trên đồ thị mẫu

Đồ thị 6 node ở [DATA_MODEL.md](DATA_MODEL.md) mục 7, tính trên mặt phẳng mét. Đáp án ghi ở [`tests/fixtures/mini_expected.json`](../tests/fixtures/mini_expected.json).

Quy ước (theo DATA_MODEL mục 6.3):

- Heap chứa `(priority, counter, node)`; hai entry cùng priority thì entry push trước ra trước. Cột "Heap sau bước" viết `(priority, node)` theo thứ tự pop.
- Giả định cạnh ra của S theo thứ tự S→A, S→B, S→C, S→D (thứ tự trong bảng cạnh ở mục 7). Thứ tự này chỉ quyết định C hay D ra trước; số node mở rộng không đổi.
- Lazy deletion: entry có `g` lớn hơn `g[node]` hiện tại bị bỏ qua trước khi kiểm tra đích.
- Dừng khi **pop** đích. `expanded` = số lần pop entry hợp lệ rồi duyệt cạnh ra, không tính lần pop đích.
- Ùn tắc: cạnh khớp luật khi trung điểm nằm trong vùng (khoảng cách ≤ bán kính); trọng số = thời gian cơ sở × α.

Trong cả 6 tình huống không có entry lỗi thời: không node nào được push hai lần, vì mỗi lần tìm được `g` mới cho một node thì node đó chưa có `g` nào trước đó. Cột "Bỏ qua vì lỗi thời?" vì vậy luôn là "không".

### Dijkstra — 1. Cơ sở, S → T

| Bước | Pop (node, g) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0 | (0, S) |
| 1 | (S, 0) | không | S→A, S→B, S→C, S→D | g[A] = 40, g[B] = 50, g[C] = 30, g[D] = 30 | (30, C) (30, D) (40, A) (50, B) |
| 2 | (C, 30) | không | — (ngõ cụt) | — | (30, D) (40, A) (50, B) |
| 3 | (D, 30) | không | — (ngõ cụt) | — | (40, A) (50, B) |
| 4 | (A, 40) | không | A→T | g[T] = 80 | (50, B) (80, T) |
| 5 | (B, 50) | không | B→T: 100 ≥ 80 · B→S: 100 ≥ 0 | — | (80, T) |
| 6 | (T, 80) | không | đích → dừng | — | — |

Kết quả: S→A→T, **80 s**, `expanded` = 5 (S, C, D, A, B). C và D bị pop trước A vì `g` của chúng (30) nhỏ hơn, dù chúng nằm ngược hướng đích: Dijkstra chỉ nhìn `g`.

### Dijkstra — 2. Cơ sở, T → S

| Bước | Pop (node, g) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[T] = 0 | (0, T) |
| 1 | (T, 0) | không | T→B | g[B] = 50 | (50, B) |
| 2 | (B, 50) | không | B→T: 100 ≥ 0 · B→S | g[S] = 100 | (100, S) |
| 3 | (S, 100) | không | đích → dừng | — | — |

Kết quả: T→B→S, **100 s**, `expanded` = 2. Không có cạnh T→A (A→T một chiều), nên chiều về phải vòng qua B.

### Dijkstra — 3. Ùn tắc vòng tròn tâm A, r = 220 m, α = 2

Khoảng cách từ trung điểm từng cạnh tới A (400, 0):

| Cạnh | Trung điểm | Khoảng cách tới A (m) | Khớp? | Trọng số (s) |
|---|---|---:|---|---:|
| S→A | (200, 0) | 200 | có | 80 |
| A→T | (600, 0) | 200 | có | 80 |
| S→B, B→S | (200, 150) | 250 | không | 50 |
| B→T, T→B | (600, 150) | 250 | không | 50 |
| S→C | (−150, 0) | 550 | không | 30 |
| S→D | (0, −150) | ≈ 427,2 | không | 30 |

| Bước | Pop (node, g) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0 | (0, S) |
| 1 | (S, 0) | không | S→A, S→B, S→C, S→D | g[A] = 80, g[B] = 50, g[C] = 30, g[D] = 30 | (30, C) (30, D) (50, B) (80, A) |
| 2 | (C, 30) | không | — | — | (30, D) (50, B) (80, A) |
| 3 | (D, 30) | không | — | — | (50, B) (80, A) |
| 4 | (B, 50) | không | B→T · B→S: 100 ≥ 0 | g[T] = 100 | (80, A) (100, T) |
| 5 | (A, 80) | không | A→T: 160 ≥ 100 | — | (100, T) |
| 6 | (T, 100) | không | đích → dừng | — | — |

Kết quả: S→B→T, **100 s**, `expanded` = 5 (S, C, D, B, A).

### Dijkstra — 4. Ùn tắc đều α = 2 cho mọi cạnh

| Bước | Pop (node, g) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0 | (0, S) |
| 1 | (S, 0) | không | S→A, S→B, S→C, S→D | g[A] = 80, g[B] = 100, g[C] = 60, g[D] = 60 | (60, C) (60, D) (80, A) (100, B) |
| 2 | (C, 60) | không | — | — | (60, D) (80, A) (100, B) |
| 3 | (D, 60) | không | — | — | (80, A) (100, B) |
| 4 | (A, 80) | không | A→T | g[T] = 160 | (100, B) (160, T) |
| 5 | (B, 100) | không | B→T: 200 ≥ 160 · B→S: 200 ≥ 0 | — | (160, T) |
| 6 | (T, 160) | không | đích → dừng | — | — |

Kết quả: S→A→T (không đổi), **160 s** = 2 × 80, `expanded` = 5. Mọi tuyến cùng nhân 2 nên thứ tự giữa các tuyến không đổi.

### Dijkstra — 5. Đóng A→T

| Bước | Pop (node, g) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0 | (0, S) |
| 1 | (S, 0) | không | S→A, S→B, S→C, S→D | g[A] = 40, g[B] = 50, g[C] = 30, g[D] = 30 | (30, C) (30, D) (40, A) (50, B) |
| 2 | (C, 30) | không | — | — | (30, D) (40, A) (50, B) |
| 3 | (D, 30) | không | — | — | (40, A) (50, B) |
| 4 | (A, 40) | không | A→T bị đóng, không duyệt | — | (50, B) |
| 5 | (B, 50) | không | B→T · B→S: 100 ≥ 0 | g[T] = 100 | (100, T) |
| 6 | (T, 100) | không | đích → dừng | — | — |

Kết quả: S→B→T, **100 s**, `expanded` = 5.

### Dijkstra — 6. Đóng A→T và B→T

| Bước | Pop (node, g) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0 | (0, S) |
| 1 | (S, 0) | không | S→A, S→B, S→C, S→D | g[A] = 40, g[B] = 50, g[C] = 30, g[D] = 30 | (30, C) (30, D) (40, A) (50, B) |
| 2 | (C, 30) | không | — | — | (30, D) (40, A) (50, B) |
| 3 | (D, 30) | không | — | — | (40, A) (50, B) |
| 4 | (A, 40) | không | A→T bị đóng | — | (50, B) |
| 5 | (B, 50) | không | B→T bị đóng · B→S: 100 ≥ 0 | — | rỗng |

Heap rỗng mà chưa pop T → **`no_path`**, `expanded` = 5 (mọi node đi tới được từ S).

### A*: giá trị heuristic

`h(n)` = khoảng cách thẳng từ n tới đích / 10 m/s. Với đích T (800, 0):

| Node | Tọa độ | Khoảng cách tới T (m) | h (s) |
|---|---|---:|---:|
| S | (0, 0) | 800 | 80 |
| A | (400, 0) | 400 | 40 |
| B | (400, 300) | 500 | 50 |
| C | (−300, 0) | 1100 | 110 |
| D | (0, −300) | √730000 ≈ 854,4 | 85,44 |
| T | (800, 0) | 0 | 0 |

Với đích S (tình huống T → S): h(T) = 80, h(B) = 50, h(S) = 0.

Ùn tắc và đóng đường không đổi `h`: `h` dùng `v_max` cơ sở (DATA_MODEL mục 5.3).

Fixture `mini.json` dùng lat/lon và haversine nên `h` lệch rất ít so với bảng này. Ở các bước có hai `f` gần nhau, chênh lệch nhỏ nhất là 4,56 s (D 145,44 so với B 150 ở tình huống 4), lớn hơn nhiều so với độ lệch đó, nên thứ tự pop không đổi.

### A* — 1. Cơ sở, S → T

Heap sắp theo `f = g + h`. Cột "Heap sau bước" viết `(f, node)`.

| Bước | Pop (node, g, f) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g, h, f | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0, h = 80, f = 80 | (80, S) |
| 1 | (S, 0, 80) | không | S→A, S→B, S→C, S→D | A: 40 + 40 = 80 · B: 50 + 50 = 100 · C: 30 + 110 = 140 · D: 30 + 85,44 = 115,44 | (80, A) (100, B) (115,44, D) (140, C) |
| 2 | (A, 40, 80) | không | A→T | T: 80 + 0 = 80 | (80, T) (100, B) (115,44, D) (140, C) |
| 3 | (T, 80, 80) | không | đích → dừng | — | — |

Kết quả: S→A→T, **80 s**, `expanded` = 2 (S, A). A* không pop C và D vì `f(C) = 140` và `f(D) = 115,44` đều lớn hơn chi phí tối ưu 80; khi T được pop với f = 80 thì thuật toán đã dừng.

### A* — 2. Cơ sở, T → S

| Bước | Pop (node, g, f) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g, h, f | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[T] = 0, h = 80, f = 80 | (80, T) |
| 1 | (T, 0, 80) | không | T→B | B: 50 + 50 = 100 | (100, B) |
| 2 | (B, 50, 100) | không | B→T: 100 ≥ 0 · B→S | S: 100 + 0 = 100 | (100, S) |
| 3 | (S, 100, 100) | không | đích → dừng | — | — |

Kết quả: T→B→S, **100 s**, `expanded` = 2.

### A* — 3. Ùn tắc vòng tròn tâm A

| Bước | Pop (node, g, f) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g, h, f | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0, f = 80 | (80, S) |
| 1 | (S, 0, 80) | không | S→A, S→B, S→C, S→D | A: 80 + 40 = 120 · B: 50 + 50 = 100 · C: 30 + 110 = 140 · D: 30 + 85,44 = 115,44 | (100, B) (115,44, D) (120, A) (140, C) |
| 2 | (B, 50, 100) | không | B→T · B→S: 100 ≥ 0 | T: 100 + 0 = 100 | (100, T) (115,44, D) (120, A) (140, C) |
| 3 | (T, 100, 100) | không | đích → dừng | — | — |

Kết quả: S→B→T, **100 s**, `expanded` = 2 (S, B).

### A* — 4. Ùn tắc đều α = 2

| Bước | Pop (node, g, f) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g, h, f | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0, f = 80 | (80, S) |
| 1 | (S, 0, 80) | không | S→A, S→B, S→C, S→D | A: 80 + 40 = 120 · B: 100 + 50 = 150 · C: 60 + 110 = 170 · D: 60 + 85,44 = 145,44 | (120, A) (145,44, D) (150, B) (170, C) |
| 2 | (A, 80, 120) | không | A→T | T: 160 + 0 = 160 | (145,44, D) (150, B) (160, T) (170, C) |
| 3 | (D, 60, 145,44) | không | — (ngõ cụt) | — | (150, B) (160, T) (170, C) |
| 4 | (B, 100, 150) | không | B→T: 200 ≥ 160 · B→S: 200 ≥ 0 | — | (160, T) (170, C) |
| 5 | (T, 160, 160) | không | đích → dừng | — | — |

Kết quả: S→A→T, **160 s**, `expanded` = 4 (S, A, D, B), so với 2 ở trạng thái cơ sở. Chi phí thật tăng gấp đôi nhưng `h` giữ nguyên, nên cận dưới lỏng hơn và A* phải mở thêm D, B. Đây là ví dụ nhỏ cho giả thuyết ở DATA_MODEL mục 5.3. Bảng ở DATA_MODEL mục 7 để trống ô này.

### A* — 5. Đóng A→T

| Bước | Pop (node, g, f) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g, h, f | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0, f = 80 | (80, S) |
| 1 | (S, 0, 80) | không | S→A, S→B, S→C, S→D | A: 80 · B: 100 · C: 140 · D: 115,44 | (80, A) (100, B) (115,44, D) (140, C) |
| 2 | (A, 40, 80) | không | A→T bị đóng | — | (100, B) (115,44, D) (140, C) |
| 3 | (B, 50, 100) | không | B→T · B→S: 100 ≥ 0 | T: 100 + 0 = 100 | (100, T) (115,44, D) (140, C) |
| 4 | (T, 100, 100) | không | đích → dừng | — | — |

Kết quả: S→B→T, **100 s**, `expanded` = 3 (S, A, B).

### A* — 6. Đóng A→T và B→T

| Bước | Pop (node, g, f) | Bỏ qua vì lỗi thời? | Cạnh được xét | Cập nhật g, h, f | Heap sau bước |
|---|---|---|---|---|---|
| 0 | — | — | — | g[S] = 0, f = 80 | (80, S) |
| 1 | (S, 0, 80) | không | S→A, S→B, S→C, S→D | A: 80 · B: 100 · C: 140 · D: 115,44 | (80, A) (100, B) (115,44, D) (140, C) |
| 2 | (A, 40, 80) | không | A→T bị đóng | — | (100, B) (115,44, D) (140, C) |
| 3 | (B, 50, 100) | không | B→T bị đóng · B→S: 100 ≥ 0 | — | (115,44, D) (140, C) |
| 4 | (D, 30, 115,44) | không | — | — | (140, C) |
| 5 | (C, 30, 140) | không | — | — | rỗng |

Kết quả: **`no_path`**, `expanded` = 5. Khi không có đường, A* cũng phải duyệt hết mọi node đi tới được, giống Dijkstra.

### Tổng hợp

| # | Tình huống | Tuyến | Chi phí | Dijkstra `expanded` | A* `expanded` |
|---|---|---|---:|---:|---:|
| 1 | Cơ sở, S → T | S→A→T | 80 s | 5 | 2 |
| 2 | Cơ sở, T → S | T→B→S | 100 s | 2 | 2 |
| 3 | Ùn tắc tâm A, r = 220 m, α = 2 | S→B→T | 100 s | 5 | 2 |
| 4 | Ùn tắc đều α = 2 | S→A→T | 160 s | 5 | 4 |
| 5 | Đóng A→T | S→B→T | 100 s | 5 | 3 |
| 6 | Đóng A→T và B→T | — | `no_path` | 5 | 5 |

Đối chiếu với DATA_MODEL mục 7: chi phí, tuyến và số node mở rộng khớp ở mọi ô bảng đó đã điền. Bốn ô bảng đó để trống được điền thêm ở đây: tình huống 2 (Dijkstra 2, A* 2) và tình huống 4 (Dijkstra 5, A* 4).
