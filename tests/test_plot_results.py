"""T64: biểu đồ từ `measurements.csv` — test bằng **CSV giả sinh trong `tmp_path`** (dữ liệu THỬ,
không phải số đo thật; không ảnh/CSV nào được ghi vào repo).
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parent.parent / "scripts" / "plot_results.py"
_spec = importlib.util.spec_from_file_location("plot_results", _path)
plot = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = plot          # dataclass cần thấy module trong sys.modules khi exec
_spec.loader.exec_module(plot)

# Chép nguyên văn danh sách cột của docs/EXPERIMENT_PLAN.md mục 3.3 (không lấy từ script) để test
# bắt được nếu script lệch tài liệu.
COLUMNS = [
    "run_id", "suite", "dataset_id", "size_label", "n_nodes", "n_edges", "query_id", "workload",
    "stratum", "source", "target", "hav_m", "algo", "scenario_id", "blocked_count", "status",
    "cost_s", "distance_m", "expanded", "unique_expanded", "reopened", "relaxations", "pushes",
    "max_frontier", "runtime_ns_median", "runtime_ns_min", "repeats",
]

needs_matplotlib = pytest.mark.skipif(
    importlib.util.find_spec("matplotlib") is None,
    reason="cần matplotlib (extra 'bench') để vẽ hình",
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def make_row(**values) -> dict[str, str]:
    """Một dòng CSV đủ 27 cột với giá trị mặc định hợp lệ; `values` ghi đè cột cần đổi."""
    row = dict.fromkeys(COLUMNS, "")
    row.update({
        "run_id": "20261101-0900-demo-abc1234",
        "suite": "demo",
        "dataset_id": "demo-hcm",
        "size_label": "4.5km",
        "n_nodes": "1000",
        "n_edges": "2000",
        "query_id": "q1",
        "workload": "fixed trips",
        "stratum": "short",
        "source": "10",
        "target": "20",
        "hav_m": "500",
        "algo": "dijkstra",
        "scenario_id": "baseline",
        "blocked_count": "0",
        "status": "ok",
        "cost_s": "12.5",
        "distance_m": "1200",
        "expanded": "10",
        "unique_expanded": "9",
        "reopened": "0",
        "relaxations": "20",
        "pushes": "15",
        "max_frontier": "8",
        "runtime_ns_median": "1000000",
        "runtime_ns_min": "900000",
        "repeats": "5",
    })
    row.update({key: str(value) for key, value in values.items()})
    return row


def write_csv(run_dir: Path, rows: list[dict[str, str]], columns: list[str] | None = None) -> Path:
    """Ghi measurements.csv (dữ liệu thử) vào `run_dir` và trả đường dẫn file."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "measurements.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns or COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def demo_rows(run_id: str = "20261101-0900-demo-abc1234",
              offset: int = 0) -> list[dict[str, str]]:
    """E2 giả: 4 chuyến × 3 tầng × 2 thuật toán; `offset` dịch `expanded` cho lần chạy thứ hai."""
    rows: list[dict[str, str]] = []
    for stratum in ("dai", "ngan", "trung_binh"):        # cố ý xáo: hình phải tự sắp lại
        for index in range(4):
            for algo, expanded in (("dijkstra", 10 + index + offset),
                                   ("astar", 4 + index + offset)):
                rows.append(make_row(run_id=run_id, query_id=f"{stratum}-{index}",
                                     stratum=stratum, algo=algo, expanded=expanded))
    return rows


def scaling_rows(sizes: tuple[int, ...] = (1200, 4800, 10800),
                 run_id: str = "20261102-1000-scaling-def5678") -> list[dict[str, str]]:
    """E3 giả: mỗi kích thước 2 chuyến dùng lại y hệt, chỉ workload "fixed trips"."""
    rows: list[dict[str, str]] = []
    for size in sizes:
        for index in range(2):
            for algo, expanded in (("dijkstra", size // 10), ("astar", size // 25)):
                rows.append(make_row(run_id=run_id, suite="scaling",
                                     dataset_id="hcm-scaling", size_label=f"{size}",
                                     n_nodes=size, query_id=f"trip-{index}", algo=algo,
                                     expanded=expanded, runtime_ns_median=1000000 + size))
    return rows


def assert_png(path: Path) -> None:
    """File tồn tại, nằm đúng thư mục, là PNG thật (đọc chữ ký 8 byte đầu)."""
    assert path.is_file()
    assert path.stat().st_size > 1000
    assert path.read_bytes()[:8] == PNG_MAGIC


# --- Đọc CSV ---

def test_read_measurements_parses_numbers_and_units(tmp_path):
    write_csv(tmp_path, [make_row(expanded=42, runtime_ns_median=2500000, n_nodes=1234)])
    rows = plot.read_measurements(tmp_path)
    assert len(rows) == 1
    row = rows[0]
    assert row.expanded == 42 and row.n_nodes == 1234
    assert row.runtime_ms == pytest.approx(2.5)          # ns → ms
    assert row.suite == "demo" and row.algo == "dijkstra"


def test_missing_column_is_rejected(tmp_path):
    columns = [c for c in COLUMNS if c != "expanded"]
    write_csv(tmp_path, [make_row()], columns=columns)
    with pytest.raises(ValueError, match="thiếu cột.*expanded"):
        plot.read_measurements(tmp_path)


def test_non_numeric_cell_is_rejected(tmp_path):
    write_csv(tmp_path, [make_row(expanded="không-phải-số")])
    with pytest.raises(ValueError, match="expanded.*không phải số"):
        plot.read_measurements(tmp_path)


def test_pair_ratios_skips_zero_and_incomplete_pairs(tmp_path):
    write_csv(tmp_path, [
        make_row(query_id="q0", algo="dijkstra", expanded=0),            # mẫu số 0: bỏ
        make_row(query_id="q0", algo="astar", expanded=5),
        make_row(query_id="q1", algo="dijkstra", expanded=10),           # thiếu A*: bỏ
        make_row(query_id="q2", algo="dijkstra", expanded=10),
        make_row(query_id="q2", algo="astar", expanded=5),
    ])
    rows = plot.read_measurements(tmp_path)
    ratios = plot.pair_ratios(rows, ("run_id", "workload", "n_nodes", "query_id"))
    assert ratios == {("20261101-0900-demo-abc1234", "fixed trips", 1000, "q2"): 0.5}


# --- Vẽ hình ---

@needs_matplotlib
def test_demo_run_creates_both_e2_figures(tmp_path):
    write_csv(tmp_path, demo_rows())
    report = plot.plot_run(tmp_path)
    assert set(report.created) == {"fig_e2_expanded_box.png", "fig_e2_expanded_scatter.png"}
    for name, path in report.created.items():
        assert path.parent == tmp_path
        assert_png(path)
        caption = report.captions[name]
        assert "run_id: 20261101-0900-demo-abc1234" in caption
        assert "số cặp: 12" in caption                      # 3 tầng × 4 chuyến
        assert "dataset_id: demo-hcm" in caption


@needs_matplotlib
def test_three_sizes_create_both_scaling_figures(tmp_path):
    write_csv(tmp_path, scaling_rows())
    report = plot.plot_run(tmp_path)
    assert set(report.created) == {"fig_e3_expanded_runtime.png", "fig_e3_ratio_by_size.png"}
    for name, path in report.created.items():
        assert_png(path)
        assert "số cặp: 6" in report.captions[name]          # 3 kích thước × 2 chuyến
        assert "dataset_id: hcm-scaling" in report.captions[name]
    assert "suite demo" in report.skipped["fig_e2_expanded_box.png"]
    assert "suite scenario" in report.skipped["fig_e4_ratio_by_scenario.png"]


@needs_matplotlib
def test_single_size_skips_line_charts_with_reason(tmp_path):
    write_csv(tmp_path, scaling_rows(sizes=(1200,)))
    report = plot.plot_run(tmp_path)
    assert report.created == {}
    for name in ("fig_e3_expanded_runtime.png", "fig_e3_ratio_by_size.png"):
        reason = report.skipped[name]
        assert "1 kích thước" in reason and "ít nhất 2" in reason


@needs_matplotlib
def test_three_scaling_runs_merge_into_e3_figures(tmp_path):
    # T60 đo một đồ thị mỗi lần chạy: 3 kích thước = 3 thư mục, mỗi thư mục 1 giá trị |V|.
    runs = []
    for size in (1200, 4800, 10800):
        run_id = f"20261102-1000-scaling-{size:05d}"
        write_csv(tmp_path / run_id, scaling_rows(sizes=(size,), run_id=run_id))
        runs.append(tmp_path / run_id)
    out = tmp_path / "figs"
    report = plot.plot_run(runs, out)
    assert set(report.created) == {"fig_e3_expanded_runtime.png", "fig_e3_ratio_by_size.png"}
    for name, path in report.created.items():
        assert path.parent == out and path.is_file()        # ghi vào --out, không vào 1 run_dir
        assert_png(path)
        caption = report.captions[name]
        assert "số cặp: 6" in caption                       # 3 kích thước × 2 chuyến
        for run_id in (f"20261102-1000-scaling-{s:05d}" for s in (1200, 4800, 10800)):
            assert run_id in caption                        # chú thích ghi mọi run_id đã gộp
    assert out.is_dir()


@needs_matplotlib
def test_two_demo_runs_with_same_query_ids_are_not_merged(tmp_path):
    # run_benchmarks.py đánh query_id từ 0 mỗi lần chạy: gộp hai lần chạy thì query_id trùng nhau.
    first, second = tmp_path / "run-a", tmp_path / "run-b"
    write_csv(first, demo_rows(run_id="20261107-0800-demo-aaaaaaa"))
    write_csv(second, demo_rows(run_id="20261107-0900-demo-bbbbbbb", offset=100))
    out = tmp_path / "figs"
    report = plot.plot_run([first, second], out)
    for name in ("fig_e2_expanded_box.png", "fig_e2_expanded_scatter.png"):
        assert_png(out / name)
        caption = report.captions[name]
        assert "số cặp: 24" in caption                       # 12 cặp mỗi lần chạy, không ghi đè
        assert "20261107-0800-demo-aaaaaaa" in caption
        assert "20261107-0900-demo-bbbbbbb" in caption


def test_pair_ratios_keeps_pairs_of_two_runs_with_same_size(tmp_path):
    runs = ("20261107-1000-scaling-aaaaaaa", "20261107-1100-scaling-bbbbbbb")
    for run_id in runs:
        write_csv(tmp_path / run_id, scaling_rows(sizes=(4800,), run_id=run_id))
    rows: list[plot.Row] = []
    for run_id in runs:
        rows.extend(plot.read_measurements(tmp_path / run_id))
    ratios = plot.pair_ratios(rows, ("run_id", "workload", "n_nodes", "query_id"))
    assert len(ratios) == 4                                  # 2 lần chạy × 2 chuyến, không trộn
    assert {key[0] for key in ratios} == set(runs)


@needs_matplotlib
def test_two_scaling_runs_same_size_count_all_pairs(tmp_path):
    # Hai lần chạy cùng |V| cộng một kích thước khác: hình E3 phải đếm đủ cặp của cả ba.
    runs = (("20261107-1000-scaling-aaaaaaa", 4800), ("20261107-1100-scaling-bbbbbbb", 4800),
            ("20261107-1200-scaling-ccccccc", 9600))
    for run_id, size in runs:
        write_csv(tmp_path / run_id, scaling_rows(sizes=(size,), run_id=run_id))
    out = tmp_path / "figs"
    report = plot.plot_run([tmp_path / run_id for run_id, _ in runs], out)
    for name in ("fig_e3_expanded_runtime.png", "fig_e3_ratio_by_size.png"):
        assert_png(out / name)
        assert "số cặp: 6" in report.captions[name]          # (2 + 2 + 2) cặp


def test_stratum_order_is_fixed_and_unknown_last():
    assert plot.order_strata(["dai", "ngan", "khac", "trung_binh"]) == [
        "ngan", "trung_binh", "dai", "khac"]
    assert plot.order_strata(["trung_binh", "ngan", "trung_binh"]) == ["ngan", "trung_binh"]
    assert plot.stratum_label("ngan") == "ngắn (δ<0,2)"
    assert plot.stratum_label("dai") == "dài (δ≥0,5)"
    assert plot.stratum_label("khac") == "khac"             # tầng lạ giữ nguyên giá trị CSV


@needs_matplotlib
def test_scenario_run_creates_ratio_box(tmp_path):
    rows = [make_row(run_id="20261103-0800-scenario-aaa1111", suite="scenario",
                     dataset_id="demo-hcm", workload="", stratum="", scenario_id=scenario,
                     query_id=f"trip-{index}", algo=algo, expanded=expanded)
            for scenario in ("baseline", "peak-center")
            for index in range(2)
            for algo, expanded in (("dijkstra", 20), ("astar", 12))]
    write_csv(tmp_path, rows)
    report = plot.plot_run(tmp_path)
    assert set(report.created) == {"fig_e4_ratio_by_scenario.png"}
    caption = report.captions["fig_e4_ratio_by_scenario.png"]
    assert "số cặp: 4" in caption and "run_id: 20261103-0800-scenario-aaa1111" in caption


@needs_matplotlib
def test_header_only_csv_skips_all_figures_without_error(tmp_path):
    write_csv(tmp_path, [])
    report = plot.plot_run(tmp_path)
    assert report.created == {}
    assert len(report.skipped) == 5                       # E2 ×2, E3 ×2, E4; không có E5
    assert all(report.skipped.values())


# --- CLI ---

@needs_matplotlib
def test_cli_reports_created_and_skipped(tmp_path, capsys):
    write_csv(tmp_path, demo_rows())
    code = plot.main([str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "đã tạo" in out and "fig_e2_expanded_box.png" in out
    assert "bỏ qua fig_e3_expanded_runtime.png" in out and "suite scaling" in out


@needs_matplotlib
def test_cli_out_dir_receives_merged_figures(tmp_path, capsys):
    runs = []
    for size in (1200, 4800, 10800):
        run_id = f"20261102-1000-scaling-{size:05d}"
        write_csv(tmp_path / run_id, scaling_rows(sizes=(size,), run_id=run_id))
        runs.append(str(tmp_path / run_id))
    out = tmp_path / "figs"
    code = plot.main([*runs, "--out", str(out)])
    printed = capsys.readouterr().out
    assert code == 0
    assert (out / "fig_e3_expanded_runtime.png").is_file()
    assert (out / "fig_e3_ratio_by_size.png").is_file()
    assert "số cặp: 6" in printed


def test_cli_requires_out_when_merging_many_dirs(tmp_path, capsys):
    first, second = tmp_path / "run-a", tmp_path / "run-b"
    write_csv(first, scaling_rows(sizes=(1200,)))
    write_csv(second, scaling_rows(sizes=(4800,)))
    code = plot.main([str(first), str(second)])
    assert code == 2
    assert "--out" in capsys.readouterr().err

    with pytest.raises(ValueError, match="--out"):           # cùng luật ở tầng hàm
        plot.plot_run([first, second])
    assert not list(first.glob("fig_*.png")) and not list(second.glob("fig_*.png"))


def test_cli_rejects_wrong_usage_and_missing_file(tmp_path, capsys):
    assert plot.main([]) == 2
    assert "cách dùng" in capsys.readouterr().err

    assert plot.main(["--out"]) == 2                          # thiếu giá trị
    assert "--out" in capsys.readouterr().err

    missing = tmp_path / "khong-co"
    assert plot.main([str(missing)]) == 1
    assert "không thấy" in capsys.readouterr().err


@needs_matplotlib
def test_single_dir_still_accepts_str_and_writes_beside_csv(tmp_path):
    write_csv(tmp_path, demo_rows())
    report = plot.plot_run(str(tmp_path))                     # một str vẫn chạy như cũ
    assert report.created
    assert all(path.parent == tmp_path for path in report.created.values())
