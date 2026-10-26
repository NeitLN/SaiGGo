"""Tour trên ma trận chi phí có hướng (docs/TOPIC.md mục 10, docs/TASKS.md T70).

Kho là chỉ số 0 và cố định ở đầu/cuối tour; `order = [0, …]` liệt kê kho một lần, hàm tự cộng
chặng quay về kho. Ma trận **bất đối xứng**: `D[i][j]` là chi phí có hướng, không dùng công thức
delta của 2-opt đối xứng vì đảo một đoạn còn đảo chiều các chặng bên trong (mục 10.5).
Đây là heuristic: kết quả là "lộ trình được cải thiện", không phải tối ưu toàn cục.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

Matrix = Sequence[Sequence[float]]

COST_EPS = 1e-9   # giây; chênh lệch nhỏ hơn mức này coi như bằng nhau (sai số số thực)


@dataclass(frozen=True)
class TourPlan:
    order: list[int]                # tour được chọn, khép kín: 0 → … → 0
    cost_s: float
    method: str                     # "input" | "nearest_neighbor" | "nearest_neighbor_2opt"
    candidates: dict[str, float]    # chi phí từng ứng viên, để phân tích improvement


def _check_matrix(D: Matrix) -> int:
    """Kiểm ma trận vuông, chi phí không âm (math.inf = không tới được); trả số điểm n."""
    n = len(D)
    if n == 0:
        raise ValueError("ma trận chi phí phải có ít nhất 1 hàng (kho)")
    for i, row in enumerate(D):
        if len(row) != n:
            raise ValueError(f"ma trận chi phí phải vuông: hàng {i} có {len(row)} phần tử, cần {n}")
        for j, w in enumerate(row):
            if not (isinstance(w, (int, float)) and not isinstance(w, bool) and w >= 0):
                raise ValueError(f"D[{i}][{j}] = {w!r} phải là chi phí không âm "
                                 "(math.inf nếu không đi được)")
    return n


def _check_order(n: int, order: Sequence[int]) -> list[int]:
    """Kiểm tour là hoán vị của 0..n−1, kho ở đầu; trả bản sao để không sửa đầu vào."""
    seq = list(order)
    if len(seq) != n:
        raise ValueError(f"tour phải có đúng {n} điểm (kể cả kho), nhận {len(seq)}")
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in seq):
        raise ValueError("tour phải là dãy chỉ số nguyên")
    if sorted(seq) != list(range(n)):
        raise ValueError(f"tour phải là hoán vị của 0..{n - 1}, nhận {seq}")
    if seq[0] != 0:
        raise ValueError("kho (chỉ số 0) phải ở đầu tour")
    return seq


def _closed_cost(D: Matrix, seq: Sequence[int]) -> float:
    """Tổng chi phí tour khép kín, đã kiểm dữ liệu (dùng trong vòng lặp)."""
    return float(sum(D[a][b] for a, b in zip(seq, seq[1:] + seq[:1])))


def tour_cost(D: Matrix, order: Sequence[int]) -> float:
    """Chi phí tour khép kín `0 → order[1] → … → order[-1] → 0`, đơn vị của `D` (giây)."""
    n = _check_matrix(D)
    return _closed_cost(D, _check_order(n, order))


def nearest_neighbor(D: Matrix) -> list[int]:
    """Tham lam từ kho: mỗi bước chọn điểm chưa phục vụ có `D[vị trí hiện tại][j]` nhỏ nhất.

    Hòa chi phí thì chọn chỉ số nhỏ hơn để tái lập được. Ma trận có `math.inf` vẫn trả một
    hoán vị; chi phí tour khi đó là `math.inf` (kiểm khả thi là việc của tầng dựng ma trận).
    """
    n = _check_matrix(D)
    order = [0]
    remaining = set(range(1, n))
    while remaining:
        cur = order[-1]
        nxt = min(remaining, key=lambda j: (D[cur][j], j))
        order.append(nxt)
        remaining.remove(nxt)
    return order


def two_opt(D: Matrix, order: Sequence[int]) -> list[int]:
    """2-opt cho ma trận có hướng: đảo một đoạn điểm giao, **tính lại toàn bộ** chi phí tour.

    Kho giữ ở đầu/cuối. Chỉ nhận khi chi phí giảm hơn `COST_EPS`, dừng khi không còn cải thiện
    (mỗi nước đi được nhận làm chi phí giảm thật, số tour hữu hạn nên vòng lặp luôn dừng).
    Không sửa `order` truyền vào. Không bảo đảm tối ưu toàn cục (chỉ là cực trị địa phương).
    """
    n = _check_matrix(D)
    best = _check_order(n, order)
    best_cost = _closed_cost(D, best)
    while True:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                cost = _closed_cost(D, candidate)   # đảo đoạn đổi chiều cả các chặng bên trong
                if cost < best_cost - COST_EPS:
                    best, best_cost = candidate, cost
                    improved = True
                    break
            if improved:
                break
        if not improved:
            return best


def choose_tour(D: Matrix, order: Sequence[int]) -> TourPlan:
    """Chọn tour rẻ nhất trong {thứ tự nhập, Nearest Neighbor, Nearest Neighbor + 2-opt}.

    Hòa chi phí thì giữ ứng viên đứng trước trong danh sách trên, nên không bao giờ thay thứ tự
    nhập bằng một lời giải tệ hơn (TOPIC 10.6). Lưu chi phí từng ứng viên để tính improvement.
    """
    n = _check_matrix(D)
    initial = _check_order(n, order)
    nn = nearest_neighbor(D)
    nn_opt = two_opt(D, nn)
    options = (
        ("input", initial),
        ("nearest_neighbor", nn),
        ("nearest_neighbor_2opt", nn_opt),
    )
    costs = {name: _closed_cost(D, seq) for name, seq in options}
    method, best = options[0]
    for name, seq in options[1:]:
        if costs[name] < costs[method]:        # hòa thì giữ ứng viên đứng trước
            method, best = name, seq
    return TourPlan(best, costs[method], method, costs)
