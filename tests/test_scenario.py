"""T40: kịch bản ùn tắc theo vùng, `build_snapshot`, `load_scenarios` (docs/DATA_MODEL.md mục 4.1, 4.3).

Chạy trên `tests/fixtures/mini.json`; đáp án lấy từ bảng ở DATA_MODEL mục 7 và
`tests/fixtures/mini_expected.json` (tính tay độc lập, T03).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from app.algorithms.dijkstra import dijkstra
from app.graph.geo import polyline_midpoint
from app.graph.model import node_by_name
from app.graph.scenario import (CongestionRule, CongestionZone, Scenario, baseline_snapshot,
                                build_snapshot, edge_multipliers, load_scenarios)
from mini_cases import edge_id, load_mini, path_names

SCENARIOS = Path(__file__).resolve().parent.parent / "data" / "config" / "scenarios.json"
SCENARIOS_MINI = Path(__file__).resolve().parent / "fixtures" / "scenarios_mini.json"


@pytest.fixture(scope="module")
def mini():
    return load_mini()


def scenario_around(mini, node: str, radius_m: float, alpha: float, *,
                    name: str = "test", highway: tuple[str, ...] | None = None) -> Scenario:
    """Kịch bản một vùng tròn quanh một node có tên của fixture."""
    graph, meta = mini
    i = node_by_name(meta, node)
    zone = CongestionZone(graph.node_lat[i], graph.node_lon[i], radius_m)
    return Scenario(name, "kịch bản dựng trong test", (CongestionRule(zone, alpha, highway),))


def route(mini, snap, src: str = "S", dst: str = "T"):
    graph, meta = mini
    return dijkstra(graph, snap, node_by_name(meta, src), node_by_name(meta, dst))


# --- Đáp án DATA_MODEL mục 7 ---

def test_zone_around_a_reroutes_to_s_b_t(mini):
    graph, meta = mini
    scenario = scenario_around(mini, "A", 220, 2.0)
    r = route(mini, build_snapshot(graph, meta, scenario))
    assert r.status == "ok"
    assert path_names(meta, r.node_ids) == ["S", "B", "T"]
    assert r.cost_s == pytest.approx(100.0)
    assert r.edge_ids == [edge_id(graph, meta, "S->B"), edge_id(graph, meta, "B->T")]


def test_zone_around_a_multiplies_only_edges_whose_midpoint_is_inside(mini):
    graph, meta = mini
    multipliers = edge_multipliers(graph, meta, scenario_around(mini, "A", 220, 2.0))
    # S→A và A→T có trung điểm cách A 200 m < 220 m; S→B, B→T có trung điểm cách A ~248 m.
    assert multipliers[edge_id(graph, meta, "S->A")] == 2.0
    assert multipliers[edge_id(graph, meta, "A->T")] == 2.0
    for name in ("S->B", "B->T", "S->C", "S->D", "T->B", "B->S"):
        assert multipliers[edge_id(graph, meta, name)] == 1.0


def test_uniform_alpha_keeps_route_and_only_scales_cost(mini):
    graph, meta = mini
    # Một vùng phủ toàn bộ fixture: mọi cạnh cùng nhân 2.
    scenario = scenario_around(mini, "S", 10_000_000.0, 2.0, name="un-tac-deu")
    snap = build_snapshot(graph, meta, scenario)
    assert snap.weights == [2.0 * w for w in graph.edge_base_time_s]
    r = route(mini, snap)
    assert path_names(meta, r.node_ids) == ["S", "A", "T"]   # tuyến không đổi
    assert r.cost_s == pytest.approx(160.0)


def test_alpha_below_one_rejected(mini):
    graph, _ = mini
    zone = CongestionZone(graph.node_lat[0], graph.node_lon[0], 220)
    with pytest.raises(ValueError, match="alpha"):
        CongestionRule(zone, 0.5)
    with pytest.raises(ValueError, match="alpha"):
        CongestionRule(zone, 0.999)
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="alpha"):
            CongestionRule(zone, bad)
    with pytest.raises(ValueError, match="alpha"):
        CongestionRule(zone, "2.0")
    assert CongestionRule(zone, 1.0).alpha == 1.0      # biên dưới hợp lệ


def test_graph_unchanged_after_building_snapshot(mini):
    graph, meta = mini

    def snapshot_of_state():
        return {
            "dataset_id": graph.dataset_id,
            "node_lat": list(graph.node_lat),
            "node_lon": list(graph.node_lon),
            "edge_u": list(graph.edge_u),
            "edge_v": list(graph.edge_v),
            "edge_length_m": list(graph.edge_length_m),
            "edge_speed_mps": list(graph.edge_speed_mps),
            "edge_base_time_s": list(graph.edge_base_time_s),
            "out_edges": [list(ids) for ids in graph.out_edges],
            "v_max_mps": graph.v_max_mps,
        }

    before = snapshot_of_state()
    snap = build_snapshot(graph, meta, scenario_around(mini, "A", 220, 2.0),
                          frozenset({edge_id(graph, meta, "B->T")}))
    assert snapshot_of_state() == before
    assert snap.weights is not graph.edge_base_time_s
    assert snap.weights[edge_id(graph, meta, "S->A")] == pytest.approx(80.0)
    assert math.isinf(snap.weights[edge_id(graph, meta, "B->T")])


# --- Luật áp dụng ---

def test_overlapping_rules_take_max_not_product(mini):
    graph, meta = mini
    i = node_by_name(meta, "A")
    zone_far = CongestionZone(graph.node_lat[i], graph.node_lon[i], 300)
    zone_near = CongestionZone(graph.node_lat[i], graph.node_lon[i], 210)
    scenario = Scenario("chong-nhau", "hai vùng chồng nhau",
                        (CongestionRule(zone_far, 1.5), CongestionRule(zone_near, 2.0)))
    multipliers = edge_multipliers(graph, meta, scenario)
    e = edge_id(graph, meta, "S->A")                   # trung điểm cách A 200 m: trong cả hai vùng
    assert multipliers[e] == 2.0                       # max(1,5; 2) = 2, không phải 1,5 × 2 = 3
    snap = build_snapshot(graph, meta, scenario)
    assert snap.weights[e] == pytest.approx(graph.edge_base_time_s[e] * 2.0)


def test_zone_boundary_is_inclusive(mini):
    graph, meta = mini
    e = edge_id(graph, meta, "S->A")
    lat, lon = polyline_midpoint(meta.edge_geometry[e])
    zone = CongestionZone(lat, lon, 0.0)               # tâm đúng trung điểm, bán kính 0
    scenario = Scenario("bien", "vùng bán kính 0", (CongestionRule(zone, 3.0),))
    assert edge_multipliers(graph, meta, scenario)[e] == 3.0


def test_highway_filter(mini):
    graph, meta = mini
    assert set(meta.edge_highway) == {"residential"}
    only_primary = scenario_around(mini, "A", 220, 2.0, highway=("primary",))
    assert all(a == 1.0 for a in edge_multipliers(graph, meta, only_primary))
    residential = scenario_around(mini, "A", 220, 2.0, highway=("residential", "primary"))
    assert edge_multipliers(graph, meta, residential)[edge_id(graph, meta, "S->A")] == 2.0


def test_empty_rule_list_is_baseline(mini):
    graph, meta = mini
    snap = build_snapshot(graph, meta, Scenario("baseline"))
    assert snap.weights == graph.edge_base_time_s
    assert snap.snapshot_id == baseline_snapshot(graph).snapshot_id


def test_snapshot_records_scenario_and_blocked(mini):
    graph, meta = mini
    scenario = scenario_around(mini, "A", 220, 2.0, name="un-tac-a")
    plain = build_snapshot(graph, meta, scenario)
    one_blocked = build_snapshot(graph, meta, scenario, {edge_id(graph, meta, "A->T")})
    assert plain.scenario_id == "un-tac-a" and plain.dataset_id == graph.dataset_id
    assert plain.snapshot_id != one_blocked.snapshot_id
    assert math.isinf(one_blocked.weights[edge_id(graph, meta, "A->T")])
    assert route(mini, one_blocked).cost_s == pytest.approx(100.0)


# --- File cấu hình ---

def test_load_scenarios_from_config_file(mini):
    graph, meta = mini
    scenarios = load_scenarios(SCENARIOS)          # file cấu hình thật của API/UI và T42
    assert "baseline" in scenarios
    assert scenarios["baseline"].rules == ()
    base = build_snapshot(graph, meta, scenarios["baseline"])
    assert base.weights == graph.edge_base_time_s


def test_load_scenarios_from_mini_fixture(mini):
    graph, meta = mini
    scenarios = load_scenarios(SCENARIOS_MINI)     # kịch bản thử, chỉ dùng cho mini.json
    assert list(scenarios) == ["baseline", "un-tac-tam-a"]
    r = route(mini, build_snapshot(graph, meta, scenarios["un-tac-tam-a"]))
    assert path_names(meta, r.node_ids) == ["S", "B", "T"]
    assert r.cost_s == pytest.approx(100.0)


@pytest.mark.parametrize("payload, match", [
    ({"format": "saigo-scenario/1", "scenarios": [{"id": "baseline", "rules": []}]}, "format"),
    ({"format": "saigo-scenarios/1", "scenarios": []}, "không rỗng"),
    ({"format": "saigo-scenarios/1", "scenarios": [{"id": "baseline", "rules": []},
                                                   {"id": "baseline", "rules": []}]}, "trùng"),
    ({"format": "saigo-scenarios/1", "scenarios": [{"id": "chi-co-mot", "rules": []}]}, "baseline"),
    ({"format": "saigo-scenarios/1", "scenarios": [
        {"id": "baseline", "rules": []},
        {"id": "x", "rules": [{"zone": {"lat": 10.7, "lon": 106.7, "radius_m": 100}, "alpha": 0.5}]}]},
     "alpha"),
    ({"format": "saigo-scenarios/1", "scenarios": [
        {"id": "baseline", "rules": []},
        {"id": "x", "rules": [{"zone": {"type": "polygon", "lat": 10.7, "lon": 106.7,
                                        "radius_m": 100}, "alpha": 1.5}]}]},
     "circle"),
    ({"format": "saigo-scenarios/1", "scenarios": [
        {"id": "baseline", "rules": []},
        {"id": "x", "rules": [{"zone": {"lat": 10.7, "lon": 106.7, "radius_m": -1}, "alpha": 1.5}]}]},
     "bán kính"),
    ({"format": "saigo-scenarios/1", "scenarios": [
        {"id": "baseline", "rules": []},
        {"id": "x", "rules": [{"alpha": 1.5}]}]},
     "zone"),
    ({"format": "saigo-scenarios/1", "scenarios": [
        {"id": "baseline", "rules": []},
        {"label": "thiếu id", "rules": []}]},
     "id kịch bản"),
])
def test_load_scenarios_rejects_bad_file(tmp_path, payload, match):
    path = tmp_path / "scenarios.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        load_scenarios(path)


def test_load_scenarios_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_scenarios(tmp_path / "khong-co.json")
