"""Kiểm tra script tổng hợp kết quả benchmark (T65, issue #31).

Tiêu chuẩn: docs/EXPERIMENT_PLAN.md mục 3.2, 3.3 và 9 — bảng E2/E3/E4 bằng Markdown, r và s tính
từng cặp rồi mới lấy median, gộp nhiều lần chạy theo `run_id`, mỗi bảng có dòng nguồn.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import summarize_results as summary

RUN_ID = "20261029-1552-demo-abc1234"


def make_row(*, algo: str, expanded: int, runtime_ms: float, query_id: str = "0",
             stratum: str = "", suite: str = "demo", run_id: str = RUN_ID,
             status: str = "ok", cost_s: float | None = 100.0, source: int = 10,
             target: int = 20, n_nodes: int = 1000, n_edges: int = 2000,
             dataset_id: str = "demo-hcm", size_label: str = "demo",
             workload: str = "demo", scenario_id: str = "baseline") -> dict[str, str]:
    """Một dòng measurements.csv giả với đủ 27 cột (dữ liệu thử, không phải kết quả thật)."""
    return {
        "run_id": run_id,
        "suite": suite,
        "dataset_id": dataset_id,
        "size_label": size_label,
        "n_nodes": str(n_nodes),
        "n_edges": str(n_edges),
        "query_id": str(query_id),
        "workload": workload,
        "stratum": stratum,
        "source": str(source),
        "target": str(target),
        "hav_m": "250.0",
        "algo": algo,
        "scenario_id": scenario_id,
        "blocked_count": "0",
        "status": status,
        "cost_s": "" if cost_s is None else str(cost_s),
        "distance_m": "800.0",
        "expanded": str(expanded),
        "unique_expanded": str(expanded),
        "reopened": "0",
        "relaxations": "0",
        "pushes": "0",
        "max_frontier": "0",
        "runtime_ns_median": str(int(round(runtime_ms * 1e6))),
        "runtime_ns_min": "0",
        "repeats": "5",
    }


def write_run(run_dir: Path, rows: list[dict[str, str]], *, run_id: str = RUN_ID,
              python: str = "3.14.4 (main, Oct 2026)", commit: str = "abc1234",
              dirty: bool = False) -> Path:
    """Ghi một thư mục kết quả tối thiểu: measurements.csv + env.json + config.json."""
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "measurements.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=summary.MEASUREMENT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (run_dir / "env.json").write_text(json.dumps({
        "python_version": python, "git_commit": commit, "git_dirty": dirty,
    }), encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps({
        "run_id": run_id, "suite": "demo",
    }), encoding="utf-8")
    return run_dir


def demo_rows(run_id: str = RUN_ID) -> list[dict[str, str]]:
    """3 cặp E2 (mỗi tầng một cặp) với số tính tay được.

    Dijkstra: expanded 10/20/40, ms 1/2/4 · A*: expanded 5/10/30, ms 0,5/1/3.
    """
    rows: list[dict[str, str]] = []
    spec = (("ngan", 10, 5, 1.0, 0.5), ("trung_binh", 20, 10, 2.0, 1.0),
            ("dai", 40, 30, 4.0, 3.0))
    for index, (stratum, exp_d, exp_a, ms_d, ms_a) in enumerate(spec):
        rows.append(make_row(algo="dijkstra", expanded=exp_d, runtime_ms=ms_d,
                             query_id=str(index), stratum=stratum, run_id=run_id,
                             source=10 + index, target=20 + index))
        rows.append(make_row(algo="astar", expanded=exp_a, runtime_ms=ms_a,
                             query_id=str(index), stratum=stratum, run_id=run_id,
                             source=10 + index, target=20 + index))
    return rows


def cells_by_key(section: summary.Section) -> dict[tuple[str, str], tuple[str, ...]]:
    """Bảng E2 → {(thuật toán, tầng): các ô còn lại} để kiểm từng ô."""
    assert section.table is not None, section.skipped
    return {(row[0], row[1]): row[2:] for row in section.table.rows}


def single_table_row(section: summary.Section) -> tuple[str, ...]:
    assert section.table is not None, section.skipped
    assert len(section.table.rows) == 1, section.table.rows
    return section.table.rows[0]


# --- E2 ---

def test_e2_table_cells_hand_computed(tmp_path):
    run = write_run(tmp_path / "run", demo_rows())
    rows = summary.read_rows(run)
    section = summary.e2_section(rows, [summary.read_meta(run)])

    cells = cells_by_key(section)
    assert cells[("Dijkstra", "ngắn (δ<0,2)")] == ("1", "1", "10", "—")
    assert cells[("A*", "ngắn (δ<0,2)")] == ("0,5", "0,5", "5", "100,0 %")
    assert cells[("Dijkstra", "trung bình")] == ("2", "2", "20", "—")
    assert cells[("A*", "trung bình")] == ("1", "1", "10", "100,0 %")
    assert cells[("Dijkstra", "tất cả")] == ("2", "3,8", "20", "—")       # p95 của [1, 2, 4]
    assert cells[("A*", "tất cả")] == ("1", "2,8", "10", "100,0 %")       # p95 của [0,5; 1; 3]

    assert section.table.headers == ("Thuật toán", "Tầng", "Median ms", "p95 ms",
                                     "Median expanded", "Khớp chi phí")
    assert RUN_ID in section.source
    assert "demo-hcm" in section.source
    assert "· 3 cặp" in section.source
    assert "Python 3.14.4" in section.source
    assert "git abc1234" in section.source and "dirty: false" in section.source


def test_e2_cost_mismatch_is_reported(tmp_path):
    rows = demo_rows()
    for row in rows:
        if row["algo"] == "astar" and row["query_id"] == "2":
            row["cost_s"] = "200.0"                    # lệch hẳn so với Dijkstra 100.0
    run = write_run(tmp_path / "run", rows)
    section = summary.e2_section(summary.read_rows(run), [summary.read_meta(run)])
    cells = cells_by_key(section)
    assert cells[("A*", "dài (δ≥0,5)")][3] == "0,0 %"
    assert cells[("A*", "tất cả")][3] == "66,7 %"       # 2/3 cặp khớp


# --- E3 ---

def scaling_rows() -> list[dict[str, str]]:
    """2 cặp cùng |V|: r = 0,5 và 0,25 → median 0,375 (không phải 5/15 = 0,333)."""
    common = {"suite": "scaling", "size_label": "1 km", "n_nodes": 1000, "n_edges": 2000,
              "cost_s": 10.0}
    return [
        make_row(algo="dijkstra", expanded=10, runtime_ms=2.0, query_id="0", **common),
        make_row(algo="astar", expanded=5, runtime_ms=1.0, query_id="0", **common),
        make_row(algo="dijkstra", expanded=20, runtime_ms=3.0, query_id="1", **common),
        make_row(algo="astar", expanded=5, runtime_ms=1.5, query_id="1", **common),
    ]


def test_e3_ratio_is_median_of_pair_ratios(tmp_path):
    run = write_run(tmp_path / "run", scaling_rows())
    section = summary.e3_section(summary.read_rows(run), [summary.read_meta(run)])
    row = single_table_row(section)
    assert row == ("1 km", "1000", "2000", "demo", "0,375", "2", "2,5", "1,25")
    assert section.table.headers == ("Kích thước", "|V|", "|E|", "Workload", "Median r",
                                     "Median s", "Median ms Dijkstra", "Median ms A*")
    assert "| Kích thước | \\|V\\| | \\|E\\| |" in section.table.to_markdown()
    # Tứ phân vị của r = [0,25; 0,5] là [0,3125; 0,4375] (nội suy tuyến tính)
    assert any("0,3125; 0,4375" in note for note in section.table.notes)


def test_e3_skips_pairs_with_zero_expanded_dijkstra(tmp_path):
    rows = scaling_rows()
    rows[0]["expanded"] = "0"                          # cặp 0: expanded_D = 0 → loại khỏi r
    run = write_run(tmp_path / "run", rows)
    section = summary.e3_section(summary.read_rows(run), [summary.read_meta(run)])
    row = single_table_row(section)
    assert row[4] == "0,25"                            # chỉ còn r của cặp 1
    assert any("Bỏ 1 cặp có expanded_D = 0" in note for note in section.table.notes)


# --- Gộp nhiều lần chạy ---

def test_two_runs_with_same_query_ids_are_merged(tmp_path):
    first = write_run(tmp_path / "a", demo_rows("20261029-1552-demo-aaaaaaa"),
                      run_id="20261029-1552-demo-aaaaaaa")
    second_rows = demo_rows("20261029-1600-demo-bbbbbbb")
    for row in second_rows:                            # dịch số để phát hiện ghi đè
        row["expanded"] = str(int(row["expanded"]) + 100)
    second = write_run(tmp_path / "b", second_rows, run_id="20261029-1600-demo-bbbbbbb")

    rows = summary.read_rows(first) + summary.read_rows(second)
    metas = [summary.read_meta(first), summary.read_meta(second)]
    section = summary.e2_section(rows, metas)
    cells = cells_by_key(section)
    assert "· 6 cặp" in section.source
    assert "20261029-1552-demo-aaaaaaa" in section.source
    assert "20261029-1600-demo-bbbbbbb" in section.source
    assert cells[("Dijkstra", "tất cả")][2] == "75"     # median của 10/20/40 và 110/120/140


# --- E4 ---

def e4_rows() -> list[dict[str, str]]:
    """2 cặp có baseline 100/200, kịch bản 150/300 → tăng 50 %; r = 0,8."""
    rows: list[dict[str, str]] = []
    for index, (base, cost) in enumerate(((100.0, 150.0), (200.0, 300.0))):
        common = {"query_id": str(index), "source": 30 + index, "target": 40 + index}
        rows.append(make_row(algo="dijkstra", expanded=10, runtime_ms=2.0, cost_s=base, **common))
        rows.append(make_row(algo="astar", expanded=5, runtime_ms=1.0, cost_s=base, **common))
        rows.append(make_row(algo="dijkstra", expanded=10, runtime_ms=3.0, cost_s=cost,
                             suite="scenario", scenario_id="peak-center", **common))
        rows.append(make_row(algo="astar", expanded=8, runtime_ms=2.0, cost_s=cost,
                             suite="scenario", scenario_id="peak-center", **common))
    return rows


def test_e4_uses_baseline_for_cost_increase(tmp_path):
    run = write_run(tmp_path / "run", e4_rows())
    section = summary.e4_section(summary.read_rows(run), [summary.read_meta(run)])
    row = single_table_row(section)
    assert row == ("peak-center", "—", "50,0 %", "0,8", "100,0 %")
    assert section.table.headers == ("Kịch bản", "% đổi tuyến", "Median % tăng chi phí",
                                     "Median r", "Tỉ lệ còn đường")
    assert any("% đổi tuyến" in note for note in section.table.notes)


def test_e4_without_baseline_leaves_cost_increase_empty(tmp_path):
    rows = [row for row in e4_rows() if row["suite"] == "scenario"]
    run = write_run(tmp_path / "run", rows)
    section = summary.e4_section(summary.read_rows(run), [summary.read_meta(run)])
    row = single_table_row(section)
    assert row[2] == "—"
    assert any("không có mốc `baseline`" in note for note in section.table.notes)


# --- Lỗi dữ liệu và CLI ---

def test_read_rows_rejects_missing_column_bad_number_and_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="measurements.csv"):
        summary.read_rows(tmp_path / "khong-co")

    run = write_run(tmp_path / "thieu-cot", demo_rows())
    csv_path = run / "measurements.csv"
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    csv_path.write_text("\n".join(line.replace(",expanded,", ",") for line in lines) + "\n",
                        encoding="utf-8")
    with pytest.raises(ValueError, match="thiếu cột expanded"):
        summary.read_rows(run)

    broken = write_run(tmp_path / "hong-so", demo_rows())
    text = (broken / "measurements.csv").read_text(encoding="utf-8")
    (broken / "measurements.csv").write_text(
        text.replace(",1000,2000,", ",khong-phai-so,2000,", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="không phải số"):
        summary.read_rows(broken)

    bad_env = write_run(tmp_path / "env-hong", demo_rows())
    (bad_env / "env.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="object JSON"):
        summary.read_meta(bad_env)


def test_missing_suites_are_skipped_with_reason(tmp_path):
    run = write_run(tmp_path / "run", demo_rows())
    rows = summary.read_rows(run)
    metas = [summary.read_meta(run)]
    e3 = summary.e3_section(rows, metas)
    e4 = summary.e4_section(rows, metas)
    assert e3.table is None and "suite scaling" in e3.skipped
    assert e4.table is None and "suite scenario" in e4.skipped
    text = summary.render(rows, metas)
    assert "Bỏ qua: không có dòng nào thuộc suite scaling (E3)." in text
    assert "Bỏ qua: không có dòng nào thuộc suite scenario (E4)." in text


def test_cli_prints_markdown_and_exit_codes(tmp_path, capsys):
    run = write_run(tmp_path / "run", demo_rows())
    assert summary.main([str(run)]) == 0
    out = capsys.readouterr().out
    assert "# Tổng hợp kết quả benchmark" in out
    assert "## E2 — A* vs Dijkstra trên vùng demo" in out
    assert "| Thuật toán | Tầng | Median ms | p95 ms | Median expanded | Khớp chi phí |" in out
    assert f"Nguồn: run_id `{RUN_ID}`" in out

    assert summary.main([]) == 2
    assert "cách dùng" in capsys.readouterr().err
    assert summary.main(["--khong-phai-thu-muc"]) == 2
    assert summary.main([str(tmp_path / "thieu")]) == 1
    assert "không thấy" in capsys.readouterr().err
    assert summary.main(["--help"]) == 0
    assert "summarize_results.py" in capsys.readouterr().out


def test_duplicate_directory_argument_is_counted_once(tmp_path, capsys):
    run = write_run(tmp_path / "run", demo_rows())
    assert summary.main([str(run), str(run)]) == 0
    assert capsys.readouterr().out.count("· 3 cặp") == 1


def test_duplicate_run_id_warns_on_stderr(tmp_path, capsys):
    # run_id chỉ có phút nên hai lần chạy trong cùng phút dễ trùng: phải cảnh báo, không im lặng
    first = write_run(tmp_path / "a", demo_rows())
    second = write_run(tmp_path / "b", demo_rows())
    assert summary.main([str(first), str(second)]) == 0
    err = capsys.readouterr().err
    assert "cảnh báo" in err and RUN_ID in err
