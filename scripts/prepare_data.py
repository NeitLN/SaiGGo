"""Tạo dataset snapshot từ OpenStreetMap (docs/TOPIC.md mục 7, docs/DATA_MODEL.md mục 8).

    python scripts/prepare_data.py --smoke     # T02: tải vùng ~500 m quanh Bến Thành để thử OSMnx

Cần cài nhóm thư viện `data` (OSMnx): `pip install -e ".[data]"`.
Dữ liệu tải về nằm trong data/raw/ và cache/ (đã có trong .gitignore).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

BEN_THANH = (10.7725, 106.6980)  # (lat, lon) chợ Bến Thành
SMOKE_HALF_SIDE_M = 250          # bbox 500 m × 500 m


def import_osmnx():
    try:
        import osmnx as ox
    except ImportError:
        sys.exit('chưa cài OSMnx: pip install -e ".[data]" (xem docs/team/start/MINH.md nếu pip lỗi)')
    ox.settings.cache_folder = str(ROOT / "cache")
    return ox


def first(value):
    """Sau simplify, OSMnx có thể gộp thuộc tính thành list; lấy phần tử đầu để thống kê."""
    return value[0] if isinstance(value, list) else value


def smoke() -> None:
    ox = import_osmnx()
    import networkx as nx

    G = ox.graph_from_point(BEN_THANH, dist=SMOKE_HALF_SIDE_M, dist_type="bbox", network_type="drive")
    oneway = sum(1 for _, _, d in G.edges(data=True) if d.get("oneway") is True)
    highways = Counter(first(d.get("highway")) for _, _, d in G.edges(data=True))

    print(f"graph: {type(G).__name__}, directed={G.is_directed()}")
    print(f"nodes={G.number_of_nodes()} edges={G.number_of_edges()} oneway_edges={oneway}")
    print("highway: " + ", ".join(f"{k}={v}" for k, v in highways.most_common()))
    print(f"strongly connected components: {nx.number_strongly_connected_components(G)}, "
          f"largest={len(max(nx.strongly_connected_components(G), key=len))} nodes")

    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "smoke.graphml"
    ox.save_graphml(G, out)
    print(f"đã lưu {out.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true", help="tải vùng nhỏ quanh Bến Thành để kiểm tra OSMnx")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
