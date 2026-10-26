## 📉 Burndown SaiGo

_Tự động cập nhật 11:36 26/10/2026 (giờ VN) bởi workflow `tracking.yml` từ trạng thái issue/PR thật. Số những ngày đã qua được chốt cuối ngày và không bị sửa lại; số hôm nay là tạm tính. Cách tính ở đầu file `scripts/tracking/burndown.py`._

![Burndown](https://raw.githubusercontent.com/NeitLN/SaiGGo/tracking/burndown.png?v=40269894417)

- **Phạm vi hiện tại:** 139 giờ ước lượng, 46 task
- **Đã đóng:** 39 giờ — có bằng chứng (PR/commit) 39 giờ · **Còn lại:** 100 giờ, 33 task mở
- **Đường lý tưởng hôm nay:** 105.4 giờ → nhanh hơn kế hoạch 5.4 giờ
- Mốc: cổng G1 05/11 · final ready 12/11 · thuyết trình 19/11 · nộp 22/11

### Theo tuần

| Tuần | Giờ đến hạn | Giờ hoàn thành | Task xong | Còn lại cuối tuần | PR merge | Lượt review |
|---|---:|---:|---:|---:|---:|---:|
| Tuần 1 · 19–25/10 | 27 | 10 | 3 | 129 | 2 | 6 |
| Tuần 2 · 26/10–01/11 | 47 | 29 | 10 | 100 | 13 | 19 |
| Tuần 3 · 02–08/11 | 48 | 0 | 0 | — | 0 | 0 |
| Tuần 4 · 09–15/11 | 17 | 0 | 0 | — | 0 | 0 |

### Theo thành viên

| Thành viên | Giờ được giao | Giờ hoàn thành có bằng chứng | Task xong | Đóng tay | Task mở | PR đã merge | PR đã review (có nội dung) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bảo (@dobaovlu) | 19.2 | 2.0 | 1 | 0 | 8 | 1 | 8 |
| Duy Anh (@anh7032) | 16.8 | 3.0 | 1 | 0 | 6 | 4 | 6 |
| Minh (@Jayson135724) | 32.8 | 0.0 | 0 | 0 | 14 | 0 | 7 |
| Tiến (@NeitLN) | 70.2 | 34.0 | 11 | 0 | 15 | 10 | 4 |

### Đóng trong 7 ngày qua

- 26/10 · #48 T06 · Bộ nhớ dự án, quyết định đắt nếu đổi, hàng rào kỹ thuật (3 h, qua PR)
- 26/10 · #17 T41 · Đóng đường một chiều và hai chiều (3 h, qua PR)
- 26/10 · #16 T40 · Snapshot và luật ùn tắc theo vùng (4 h, qua PR)
- 26/10 · #10 T21 · Đối chứng NetworkX trên đồ thị ngẫu nhiên (3 h, qua PR)
- 26/10 · #9 T20 · A* với heuristic địa lý (3 h, qua PR)
- 26/10 · #7 T11 · Dijkstra và SearchResult (4 h, qua PR)
- 26/10 · #6 T10 · Hàm địa lý (2 h, qua PR)
- 26/10 · #5 T03 · Bảng kết quả tính tay cho đồ thị mẫu (2 h, qua PR)
- 26/10 · #3 T01 · Chốt định dạng đồ thị, tạo fixture mẫu và bộ nạp Graph (3 h, qua PR)
- 26/10 · #2 T00 · Dựng môi trường và xác nhận khung chạy (2 h, qua PR)
- 25/10 · #44 T05 · Hướng dẫn bắt đầu cho từng thành viên (3 h, qua PR)
- 24/10 · #42 T04 · Sửa hệ thống theo dõi sau review (3 h, qua PR)
- 23/10 · #1 T-PLAN · Lập kế hoạch triển khai và hệ thống theo dõi (4 h, qua commit)

### Ghi chú

- Backlog ban đầu (40 task, ước lượng giờ) do Tiến lập từ `docs/TASKS.md` bằng script ngày 23/10/2026; trạng thái sau đó do từng thành viên cập nhật. Không dựng lại dữ liệu trước ngày này.
- Ước lượng lấy cận trên của khoảng trong TASKS.md (ví dụ "2–3 h" → 3); "nhiều buổi" (essay) được giả định là 10 giờ.
- #1 đóng bằng commit trực tiếp trước khi bật bảo vệ branch `main`; từ đó mọi thay đổi phải qua PR có review.
- Số liệu từng ngày: [`daily.csv`](https://github.com/NeitLN/SaiGGo/blob/tracking/daily.csv) trên branch `tracking`.
