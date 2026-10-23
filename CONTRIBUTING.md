# Quy trình làm việc của nhóm SaiGo

Áp dụng cho cả 4 thành viên. Mọi thay đổi vào `main` đều đi qua Pull Request có review; `main` được bảo vệ, không push trực tiếp.

## 1. Vòng đời một task

```text
Issue (Todo) ──► nhận việc, tạo branch (In Progress) ──► mở PR "Closes #n" (In Review)
            ──► 1 người khác review + CI xanh ──► Squash and merge ──► issue tự đóng (Done)
```

1. **Nhận việc:** chọn issue có nhãn `task` được giao cho mình, chuyển Status trên [Project](https://github.com/users/NeitLN/projects/3) sang **In Progress**. Nếu chưa làm được vì task khác chưa xong, gắn nhãn `blocked` và bình luận lý do.
2. **Branch:** tạo từ `main` mới nhất, đặt tên `<mã-task>-<mô-tả-ngắn>`, ví dụ `t11-dijkstra`, `t31-adapter-osm`.
3. **Commit:** nhỏ, mỗi commit một ý. Message bắt đầu bằng mã task, viết tiếng Việt, ví dụ:
   - `T11: thêm Dijkstra với lazy deletion`
   - `T11: test cạnh song song chọn đúng edge id`
4. **Pull Request:** dùng template có sẵn; dòng đầu `Closes #<số issue>`; điền cách kiểm tra (lệnh + kết quả) và giờ thực tế. Chuyển Status sang **In Review**.
5. **Review:** GitHub tự yêu cầu review theo `.github/CODEOWNERS`; người review đề xuất cũng có trong issue. Cần **ít nhất 1 approve** của người khác và **CI xanh** mới merge được. Người approve phải khác người push commit cuối cùng; nếu reviewer tự sửa giúp rồi push, cần một người khác approve.
6. **Merge:** tác giả PR bấm **Squash and merge** sau khi được approve. Issue tự đóng và burndown tự cập nhật. Status trên Project chuyển **Done** nhờ workflow của Project (nếu đã bật) hoặc lệnh `python scripts/tracking/setup_project.py --sync`.

Cả 4 thành viên có quyền write trên Project để tự chuyển Status. Issue đóng tay (không qua PR) vẫn giảm burndown nhưng bị ghi "đóng tay, chưa có PR" và không được tính vào giờ hoàn thành của người đó.

## 2. Review

Người review:

- Đọc diff, đối chiếu với mục "Hoàn thành khi" và "Kiểm tra" của issue.
- Chạy lệnh kiểm tra nếu chạy nhanh (thường là `pytest` của module đó).
- Bình luận cụ thể theo dòng code; chọn **Approve** hoặc **Request changes**, không chỉ để lại "LGTM".
- Trả lời trong vòng **24 giờ** kể từ khi được yêu cầu. Nếu bận, báo trong nhóm để đổi người review.

Mỗi thành viên review ít nhất một module của người khác (TOPIC.md mục 20.1).

## 3. Definition of Done (chung cho mọi task)

- [ ] Code/tài liệu đã merge vào `main` qua PR có review.
- [ ] Lệnh kiểm tra trong issue chạy đạt; CI xanh.
- [ ] `docs/PROGRESS.md` ghi trạng thái, bằng chứng (lệnh, kết quả) và lỗi còn lại.
- [ ] Người phụ trách giải thích được phần 🧠 "Kiến thức cần hiểu" cho nhóm.

## 4. Ước lượng và burndown

- Giờ ước lượng nằm ở mục **Ước lượng (giờ)** của issue, lấy từ `docs/TASKS.md`.
- **Không sửa ước lượng sau khi đã bắt đầu làm.** Nếu làm lâu hơn, ghi giờ thực tế trong PR; nhóm dùng chênh lệch này để rút kinh nghiệm.
- **Không viết ghi chú vào nội dung issue task.** Nội dung được sinh lại từ `docs/TASKS.md` mỗi lần sync, nên ghi chú, tiến độ và câu hỏi phải viết bằng **bình luận**. Checkbox đã tick và nhãn như `blocked` thì được giữ.
- Task bị cắt khỏi phạm vi: đóng issue với lý do **Close as not planned** và ghi lý do. Burndown tính phần đó là cắt phạm vi, không tính là đã làm.
- Task mới phát sinh: thêm vào `docs/TASKS.md` + `docs/tracking/schedule.csv`, chạy `python scripts/tracking/create_backlog.py --create` và `python scripts/tracking/setup_project.py --sync`. Phạm vi tăng sẽ hiện trên burndown.

Cách xem burndown: [docs/tracking/README.md](docs/tracking/README.md).

## 5. Họp nhóm

- Họp tuần **[Đề xuất: tối Chủ nhật, 30–45 phút, online]**. Mỗi buổi tạo một issue từ template **Biên bản họp** ngay trong hoặc sau buổi họp.
- Quyết định về phạm vi/thiết kế phải nằm trong biên bản họp hoặc bình luận issue, không chỉ trong tin nhắn riêng.

## 6. Quy tắc kỹ thuật

- Không commit dữ liệu lớn (`data/raw/`, `data/processed/*.json`, `*.graphml` đã nằm trong `.gitignore`).
- Không hard-code tuyến demo hay số benchmark; mọi số trong tài liệu phải có `run_id`.
- Không dùng hàm shortest path của thư viện trong sản phẩm; NetworkX chỉ dùng trong test.
- Chạy `pytest -q` trước khi mở PR.
