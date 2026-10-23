# Theo dõi tiến độ SaiGo

## Xem ở đâu

| Muốn xem | Nơi xem |
|---|---|
| Bảng công việc (Todo / In Progress / In Review / Done), giờ ước lượng, tuần | [GitHub Project — SaiGo Delivery Plan](https://github.com/users/NeitLN/projects/3) |
| Burndown theo giờ, thống kê theo tuần và theo thành viên (cập nhật mỗi ngày) | Issue ghim có nhãn [`tracking`](https://github.com/NeitLN/SaiGGo/issues?q=label%3Atracking) |
| Tổng kết từng tuần | Bình luận tự động mỗi sáng thứ Hai trong issue `tracking` |
| Lịch sử số liệu burndown từng ngày | Branch [`tracking`](https://github.com/NeitLN/SaiGGo/tree/tracking), thư mục `history/` |
| Các mốc và hạn | [Milestones](https://github.com/NeitLN/SaiGGo/milestones) |
| Ai làm task nào | [Issues có nhãn `task`](https://github.com/NeitLN/SaiGGo/issues?q=label%3Atask), lọc theo Assignee |
| Review giữa các thành viên | [Pull requests](https://github.com/NeitLN/SaiGGo/pulls?q=is%3Apr) |
| Biên bản họp | [Issues có nhãn `meeting`](https://github.com/NeitLN/SaiGGo/issues?q=label%3Ameeting) |
| Đóng góp commit | [Insights → Contributors](https://github.com/NeitLN/SaiGGo/graphs/contributors) |
| Kế hoạch gốc và trạng thái kiểm chứng | [docs/ROADMAP.md](../ROADMAP.md), [docs/PROGRESS.md](../PROGRESS.md) |

## Burndown được tính thế nào

- Đơn vị: **giờ ước lượng** của từng task (mục "Ước lượng (giờ)" trong issue, lấy từ [docs/TASKS.md](../TASKS.md)).
- **Còn lại** ngày d = tổng giờ của các task đã tạo nhưng chưa đóng vào cuối ngày d (giờ Việt Nam).
- **Lý tưởng:** giảm đều từ tổng giờ ngày 23/10/2026 về 0 vào ngày 12/11/2026 (final ready).
- **Phạm vi:** tổng giờ của mọi task đã tạo. Khi nhóm thêm task, đường này đi lên; khi cắt task (close as not planned), phần giờ đó không còn trong "còn lại" và được ghi là cắt phạm vi.
- Task chỉ được tính là xong khi issue đóng, thường do PR được merge. Không tính phần trăm hoàn thành dở dang.
- Giờ của task có nhiều người phụ trách được chia đều.

Mọi số được [`scripts/tracking/burndown.py`](../../scripts/tracking/burndown.py) tính từ dữ liệu GitHub. Workflow [`tracking.yml`](../../.github/workflows/tracking.yml) chạy mỗi ngày và mỗi khi có issue đóng/mở lại. Backlog được lập ngày **23/10/2026**; dữ liệu trước ngày này (đăng ký đề tài, proposal 02/10) không được dựng lại trên burndown.

Chạy tại máy:

```powershell
pip install matplotlib
python scripts/tracking/burndown.py --out build/tracking
```

## Bảo trì backlog

| Việc | Lệnh |
|---|---|
| Thêm/sửa task | Sửa `docs/TASKS.md` + `docs/tracking/schedule.csv`, rồi `python scripts/tracking/create_backlog.py --create` (thêm mới) hoặc `--sync` (cập nhật nội dung, nhãn, người được giao) |
| Đồng bộ trường trên Project (Hours, Start, Due, Week; issue đã đóng → Done) | `python scripts/tracking/setup_project.py --sync` |
| Giao task cho thành viên mới vào repo | `--sync` sẽ tự giao khi tài khoản đã là collaborator |

## Thiết lập một lần trên giao diện GitHub (API không làm được)

Trong [Project](https://github.com/users/NeitLN/projects/3):

1. **Views:** tạo các view sau.
   - *Board*: layout Board, nhóm theo Status.
   - *Theo mốc*: layout Table, nhóm theo Milestone, hiện cột Assignees, Hours, Due.
   - *Theo người*: layout Table, nhóm theo Assignees, tính tổng Hours.
   - *Roadmap*: layout Roadmap, dùng Start và Due.
2. **Workflows** (menu ⋯ → Workflows): bật *Item closed → Done*, *Pull request merged → Done*, *Auto-add to project* với bộ lọc `is:issue label:task`.
3. **Insights:** tạo biểu đồ *Burn up* có sẵn của GitHub, để đối chiếu với burndown theo giờ.
