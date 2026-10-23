# Buổi họp khởi động (30–45 phút)

Mục tiêu: cả nhóm hiểu kế hoạch, xác nhận phân công và cam kết làm việc trước khi bắt đầu tuần 2. Ghi biên bản bằng issue template **Biên bản họp** ngay trong buổi.

## Chuẩn bị trước buổi họp (mỗi người)

- [ ] Đã làm mục 1–3 của [ONBOARDING.md](ONBOARDING.md): `scripts\setup_dev.ps1` chạy tới dòng `==> Xong`.
- [ ] Đã đọc phiếu bắt đầu của mình và mục 7 của [DATA_MODEL.md](../DATA_MODEL.md).
- [ ] Ghi sẵn câu hỏi hoặc chỗ chưa đồng ý về task của mình.

## Chương trình

| Thời lượng | Nội dung | Người dẫn |
|---|---|---|
| 5 phút | Phạm vi và mốc: MVP trước 05/11, final 12/11, thuyết trình 19/11 ([PROJECT_BRIEF.md](../PROJECT_BRIEF.md) mục 2–3, [ROADMAP.md](../ROADMAP.md)) | Tiến |
| 10 phút | Đi qua ví dụ 6 node: Dijkstra mở rộng 5 node, A* mở rộng 2 node; vì sao heuristic không đánh giá quá cao | Duy Anh |
| 5 phút | Hai track song song tuần này: thuật toán (Duy Anh) và dữ liệu (Minh); định dạng `saigo-graph/1` hai bên cùng dùng | Minh |
| 10 phút | Từng người xác nhận task tuần 1–2 của mình, ước lượng giờ có hợp lý không, ai review ai | Cả nhóm |
| 5 phút | Thống nhất cam kết làm việc ([TEAM.md](TEAM.md)): review trong 24 giờ, giờ họp tuần, kênh liên lạc | Tiến |
| 5 phút | Thử quy trình: mỗi người mở PR đầu tiên hoặc review một PR | Cả nhóm |

## Quyết định cần ghi vào biên bản

- [ ] Giờ họp tuần cố định (đề xuất: tối Chủ nhật).
- [ ] Kênh liên lạc nhanh và quy tắc: quyết định quan trọng phải được ghi lại trên issue.
- [ ] Có điều chỉnh người phụ trách hoặc ước lượng nào không. Nếu có, Tiến sửa `docs/TASKS.md` qua PR rồi chạy `create_backlog.py --sync`.
- [ ] Ai review PR #43 (T04) và PR onboarding (T05).
