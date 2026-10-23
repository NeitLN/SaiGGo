"""Tạo dataset snapshot từ OpenStreetMap (docs/TOPIC.md mục 7, docs/DATA_MODEL.md mục 8).

    python scripts/prepare_data.py --smoke     # T02: tải vùng ~500 m quanh Bến Thành để thử OSMnx
    python scripts/prepare_data.py download    # T30: tải vùng tải một lần → data/raw/outer.graphml + raw_manifest.json

Cần cài nhóm thư viện `data` (OSMnx): `pip install -e ".[data]"`.
Dữ liệu tải về nằm trong data/raw/ và cache/ (đã có trong .gitignore).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
CONFIG = ROOT / "data" / "config"
VN = timezone(timedelta(hours=7))
ATTRIBUTION = "© OpenStreetMap contributors, dữ liệu theo giấy phép ODbL (https://www.openstreetmap.org/copyright)"

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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(force: bool) -> None:
    """Tải vùng tải (nửa cạnh + đệm) một lần rồi đóng băng; các bước sau chỉ đọc file này."""
    out = RAW / "outer.graphml"
    manifest_path = PROCESSED / "raw_manifest.json"
    if out.exists() and not force:
        sys.exit(f"{out.relative_to(ROOT)} đã có; dữ liệu thô đã đóng băng. Dùng --force nếu thật sự muốn tải lại.")

    ox = import_osmnx()
    import networkx as nx

    areas = json.loads((CONFIG / "areas.json").read_text(encoding="utf-8"))
    center = (areas["center"]["lat"], areas["center"]["lon"])
    dist = areas["download"]["half_side_m"] + areas["download"]["buffer_m"]
    west, south, east, north = ox.utils_geo.bbox_from_point(center, dist)

    downloaded_at = datetime.now(VN)
    G = ox.graph_from_bbox((west, south, east, north), network_type=areas["network_type"],
                           simplify=True, retain_all=True)
    RAW.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, out)

    manifest = {
        "dataset_id": f"hcmc-benthanh-{downloaded_at:%Y%m%d}",
        "downloaded_at": downloaded_at.isoformat(timespec="seconds"),
        "center": areas["center"],
        "half_side_m": areas["download"]["half_side_m"],
        "buffer_m": areas["download"]["buffer_m"],
        "bbox": {"west": west, "south": south, "east": east, "north": north},
        "network_type": areas["network_type"],
        "simplify": True,
        "retain_all": True,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "oneway_edge_count": sum(1 for _, _, d in G.edges(data=True) if d.get("oneway") is True),
        "weak_components": nx.number_weakly_connected_components(G),
        "file": out.relative_to(ROOT).as_posix(),
        "file_bytes": out.stat().st_size,
        "sha256": sha256(out),
        "dependencies": {"python": platform.python_version(), "osmnx": ox.__version__, "networkx": nx.__version__},
        "attribution": ATTRIBUTION,
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"nodes={manifest['node_count']} edges={manifest['edge_count']} oneway_edges={manifest['oneway_edge_count']}")
    print(f"đã lưu {manifest['file']} ({manifest['file_bytes'] / 1e6:.1f} MB, sha256 {manifest['sha256'][:12]}…)")
    print(f"đã ghi {manifest_path.relative_to(ROOT).as_posix()}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", choices=["download"], help="download: tải vùng tải và ghi manifest")
    ap.add_argument("--smoke", action="store_true", help="tải vùng nhỏ quanh Bến Thành để kiểm tra OSMnx")
    ap.add_argument("--force", action="store_true", help="download: tải lại dù đã có dữ liệu thô")
    a = ap.parse_args()
    if a.smoke:
        smoke()
    elif a.command == "download":
        download(a.force)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
