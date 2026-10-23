# Kịch bản demo

Kịch bản demo local và web. Đề xuất: [TOPIC.md](TOPIC.md) mục 13 (giao diện) và mục 19 (demo).

Bố cục dưới đây tham khảo một mockup giao diện tìm đường (bản đồ tối, so sánh lộ trình đỏ/xanh, popup khi đổi tuyến),
nhưng chỉ giữ phần trình bày. Mọi số hiển thị đều lấy từ response của backend, đúng phạm vi ở TOPIC.md mục 5.

## 1. Bố cục giao diện

```
┌──────────────┬──────────────────────────────────┬────────────────┐
│ Bảng điều    │                                  │ Kết quả        │
│ khiển        │          Bản đồ Leaflet          │ đo được        │
│              │                                  │                │
│ Chế độ       │  kho, điểm giao đánh số,         │ Thẻ so sánh    │
│ Case demo    │  tour, đoạn chặn, trace          │ tour           │
│ Kịch bản     │                                  │                │
│ Thuật toán   │                                  │ Dijkstra / A*  │
│ Điểm giao    │                                  │                │
│ [Lập kế      │                                  │ Nhật ký        │
│  hoạch]      │                                  │ snapshot       │
└──────────────┴──────────────────────────────────┴────────────────┘
```

### 1.1. Cột trái — bảng điều khiển

- Chế độ: **Lập kế hoạch giao** / **Tìm đường hai điểm**.
- Case demo chọn sẵn: "Kho + 5 điểm giao", "Có đoạn chặn", "Không còn đường".
- Kịch bản: Bình thường (α = 1) / Cao điểm mô phỏng (α = 1.5).
- Thuật toán tìm đường: Dijkstra / A*.
- Danh sách điểm giao: thêm, xóa, kéo thả thứ tự nhập.
- Nút chính **Lập kế hoạch giao**.

### 1.2. Giữa — bản đồ

| Thành phần | Cách hiển thị |
|---|---|
| Kho | Marker riêng, khác màu điểm giao |
| Điểm giao | Marker đánh số theo **thứ tự giao của tour đang chọn** |
| Tour hiện tại | Đường xanh, có mũi tên chỉ hướng đi (thể hiện đường một chiều) |
| Tour cũ / baseline | Đường xám mờ, nét đứt |
| Đoạn chặn | Đỏ, nét đứt; tooltip "Đoạn đường bị chặn do người dùng đánh dấu" |
| Trace tìm kiếm | Các nút đã mở rộng hiện dần khi bấm **Phát lại trace** |

Không vẽ đường thẳng nối hai điểm khi không có đường (TOPIC.md mục 11.4).

### 1.3. Cột phải — kết quả đo được

**Thẻ so sánh tour** (trả lời RQ2), mỗi thẻ một phương án, thẻ được chọn tô xanh:

| Thẻ | Nội dung |
|---|---|
| Thứ tự nhập | Thời gian di chuyển ước tính, quãng đường |
| Nearest Neighbor | Như trên + mức cải thiện so với thứ tự nhập |
| NN + 2-opt | Như trên + số bước 2-opt được chấp nhận |

**Khối Dijkstra / A\*** cho một chặng đang chọn (trả lời RQ1): chi phí, số nút mở rộng, thời gian tính toán,
và dòng "Chi phí trùng khớp: có/không".

**Nhật ký snapshot** thay cho bản tin giao thông: mỗi dòng là một sự kiện thật của backend, ví dụ
"Tạo snapshot", "Chặn cạnh (u, v, key)", "Tính lại ma trận chi phí", "2-opt dừng sau k bước".

### 1.4. Popup sau khi lập lại lộ trình

Hiện trên bản đồ sau thao tác chặn đường:

- Còn tour đầy đủ: "Đã chặn 1 đoạn. Tour mới: … s (… so với tour cũ)."
- Không còn tour đầy đủ: "Không có tour đầy đủ: không tới được điểm …" — liệt kê điểm lỗi, không hiện tour thiếu.

### 1.5. Nhãn bắt buộc

Theo TOPIC.md mục 8.3 và 13.2:

- Tách **Thời gian di chuyển ước tính theo kịch bản** và **Thời gian tính toán**; không có nhãn "Time" chung.
- Kịch bản cao điểm ghi "Cao điểm mô phỏng".
- Ghi tên thuật toán cụ thể (A*, NN, 2-opt), không dùng nhãn chung chung.

### 1.6. Không đưa vào

- Số liệu không do hệ thống đo (độ tin cậy dự báo, % giảm ùn tắc, …).
- Giao thông thời gian thực, điều khiển đèn tín hiệu, bản tin giao thông, điều khiển giọng nói.
- Lộ trình chỉ một điểm đi một điểm đến làm chế độ chính; chế độ chính là tour có quay về kho.

## 2. Kịch bản demo khoảng 4 phút

Bám theo TOPIC.md mục 19.1. Mọi case phải chạy thử trước và được ghi rõ là case minh họa.

| Bước | Thao tác | Giao diện hiển thị | Người xem hiểu |
|---|---|---|---|
| 1 | Chọn case "Kho + 5 điểm giao" | Kho và 5 marker trên bản đồ | Bài toán và phạm vi |
| 2 | Bấm **Lập kế hoạch giao**, chọn thẻ Thứ tự nhập | Tour xám, marker đánh số 1–5 theo thứ tự nhập | Baseline có thể đi vòng |
| 3 | Chọn thẻ NN + 2-opt | Tour xanh, số thứ tự đổi; thẻ hiện mức cải thiện | Thứ tự đổi, chi phí trước/sau (RQ2) |
| 4 | Chọn một chặng, bấm **Phát lại trace** với Dijkstra rồi A* | Vùng nút mở rộng; khối Dijkstra/A* với "Chi phí trùng khớp" | Cùng cost tối ưu, lượng tìm kiếm có thể khác (RQ1) |
| 5 | Chặn một đoạn trên tour | Đoạn đỏ, tour cũ mờ, tour mới xanh, popup, dòng nhật ký mới | Kế hoạch cũ mất hợp lệ, hệ thống tính lại (RQ3) |
| 6 | Chọn case "Không còn đường" | Popup liệt kê điểm không tới được | Hệ thống báo đúng giới hạn |

Ở bước 5, nêu rõ hai so sánh của TOPIC.md mục 11.3: giữ thứ tự cũ và cho phép đổi thứ tự.

## 3. Checklist trước buổi demo

- [ ] Ba case demo đã chạy trên đúng snapshot sẽ dùng và cho kết quả như kịch bản.
- [ ] Số trên thẻ và khối Dijkstra/A* khớp với response API, không có số viết tay.
- [ ] Animation trace tắt được và không chạy trong benchmark.
- [ ] Ghi nguồn © OpenStreetMap contributors hiển thị trên bản đồ.
- [ ] Có bản quay màn hình dự phòng nếu máy demo lỗi.
