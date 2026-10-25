# T20 — A* với heuristic địa lý

Tuần mục tiêu: 2 (30–31/10) · Giao cho: Tiến (thay Duy Anh) · Nhánh: `t20-astar` · Issue: [#9](https://github.com/NeitLN/SaiGGo/issues/9)
Review: Minh · Người tích hợp: Tiến
Phụ thuộc: T11 và T10 (**bắt đầu**) · Ước lượng: 3 giờ

## Mục tiêu
A* cho **cùng chi phí** với Dijkstra nhưng mở rộng ít node hơn trên fixture. Đây là lõi của RQ1.

## Interface
```python
def make_geo_heuristic(graph: Graph, target: int, c: float = 1.0) -> Callable[[int], float]:
    """h(n) = c · haversine_m(n, target) / v_max_mps  (DATA_MODEL mục 5)"""

def zero_heuristic(_: int) -> float: ...

def astar(graph: Graph, snap: Snapshot, source: int, target: int,
          heuristic: Callable[[int], float], *, trace_limit: int = 0) -> SearchResult: ...
```

## Việc cần làm
1. **`algorithms/heuristics.py`:** hai hàm heuristic, dùng `geo.haversine_m` của T10.
2. **`algorithms/astar.py`:** ưu tiên `g + h`; cho phép mở lại node; đếm `reopened`; cùng quy tắc heap và dừng như T11.
3. **`tests/test_astar.py`:**
   - chi phí bằng Dijkstra ở cả 6 tình huống;
   - S→T cơ sở cho `expanded = 2` (S, A);
   - dùng `zero_heuristic` thì `expanded` giống hệt Dijkstra;
   - `reopened == 0`;
   - khi `no_path`, A* duyệt hết các node đi tới được (5 node).

## Sở hữu (chỉ task này được tạo/sửa)
- `backend/app/algorithms/heuristics.py`, `astar.py`
- `tests/test_astar.py`

## Dùng (chỉ đọc)
- `geo.py` (T10), `dijkstra.py`, `result.py` và `graph/scenario.py` (T11)
- `mini_expected.json` (T03)

## Tiêu chí chấp nhận
- [ ] `pytest tests/test_astar.py -q` → PASS
- [ ] Bằng chứng trong PR: bảng `expanded` Dijkstra/A* cho 6 tình huống, khớp bảng tính tay của Bảo

## Ngoài phạm vi
Tính hệ số `c` từ dữ liệu thật (T22); đưa A* vào API (tuần 3, T51).

## Kiến thức cần giải thích được
- `f = g + h`; heuristic consistent nên không phải mở lại node (DATA_MODEL mục 5.2).
- Với ùn tắc đều α = 2, A* mở rộng **4** node thay vì 2 (đáp án T03, đã kiểm độc lập). Lý do: chi phí thật tăng gấp đôi nhưng `h` vẫn tính theo `v_max` cơ sở, nên cận dưới lỏng hơn. Đây là minh họa nhỏ cho giả thuyết H3 trong EXPERIMENT_PLAN mục 7.1.
