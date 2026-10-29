# T34 — Đưa dữ liệu thô lên Release và kiểm hash trên 2 máy

Tuần mục tiêu: 2 (26/10) · Giao cho: Minh · Nhánh: `t34-release-data` · Review: Tiến · Người tích hợp: Tiến
Phụ thuộc: — · Ước lượng: 2 giờ (gồm merge các PR đang chờ)

## Mục tiêu
Cả nhóm dùng **đúng một** bản dữ liệu thô: `outer.graphml` tải lúc 03:13 ngày 24/10, sha256 `24a283275b0f65836bd51d7efc7110a566b658ff3a6a5bccef1a0db576ed5398`. Tải lại từ OSM một ngày sau đã ra dữ liệu khác (12.130 node so với 12.131), nên không ai được tải lại để thay thế.

## Việc cần làm
1. Merge theo thứ tự **#46 → #47 → #53**. Trước mỗi lần merge bấm *Update branch*; nếu approve bị hủy thì nhờ approve lại.
   - Trước khi merge #53: trong `tests/test_realdata.py::test_load_graph_reads_file`, đổi `g = model.load_graph(...)` thành `g, _ = model.load_graph(...)`. `load_graph` (T01, đã merge) trả về cặp `(Graph, GraphMeta)`; để nguyên thì test sẽ lỗi trên máy có dữ liệu (CI không có dữ liệu nên không thấy).
2. Tạo Release chứa file thô (13,4 MB):
   ```powershell
   gh release create data-raw-20261024 data\raw\outer.graphml --title "Dữ liệu OSM thô 24/10/2026" --notes "outer.graphml, sha256 24a283275b0f65836bd51d7efc7110a566b658ff3a6a5bccef1a0db576ed5398. © OpenStreetMap contributors, ODbL."
   ```
3. Thêm mục **"Tải dữ liệu"** vào `docs/team/ONBOARDING.md`: lệnh `gh release download data-raw-20261024 -D data\raw`, cách kiểm `Get-FileHash data\raw\outer.graphml -Algorithm SHA256`, rồi chạy `python scripts/prepare_data.py build --area demo`.
4. Sửa thông báo lỗi trong `prepare_data.py build` khi thiếu file: ghi đúng tên Release.

## Sở hữu (chỉ task này được tạo/sửa)
- Release `data-raw-20261024`
- Mục "Tải dữ liệu" trong `docs/team/ONBOARDING.md`
- Thông báo lỗi trong `scripts/prepare_data.py`

## Dùng (chỉ đọc)
- `data/processed/raw_manifest.json`, `data/processed/manifest.json`

## Tiêu chí chấp nhận
- [ ] #46, #47, #53 đã merge; CI xanh trên `main`.
- [ ] **Tiến** (máy thứ hai) tải từ Release ra đúng sha256 `24a28327…`, chạy `build --area demo` ra `sha256 928c1f8b…` như PR #53. Nếu sha256 của file JSON khác, ghi lại trên issue: việc này chỉ cho biết **tái lập chưa khớp**; nguyên nhân (Python 3.14 / 3.11, phiên bản thư viện, …) phải kiểm thêm, chưa được kết luận ngay.
- [ ] Lệnh kiểm: `gh release view data-raw-20261024` có file `outer.graphml`.

## Ngoài phạm vi
Tải lại dữ liệu; đổi vùng tải; xử lý dữ liệu đã build.

## Khi xong
Ghi bằng chứng (sha256 trên cả hai máy) vào PR và các dòng T30, T31, T34 trong PROGRESS.
