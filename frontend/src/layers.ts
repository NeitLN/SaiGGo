// Các lớp vẽ trên bản đồ: điểm đi/đến, tuyến Dijkstra và A* (docs/DEMO.md mục 1.2).
import L from 'leaflet'
import type { AlgorithmResult, LatLon, RouteResponse } from './api'

export const COLORS = { dijkstra: '#1c7ed6', astar: '#f08c00', source: '#2f9e44', target: '#e03131' }

// GeoJSON là [lon, lat]; Leaflet cần [lat, lon].
export function toLatLngs(coords: [number, number][]): L.LatLng[] {
  return coords.map(([lon, lat]) => L.latLng(lat, lon))
}

function sameRoute(a?: AlgorithmResult, b?: AlgorithmResult): boolean {
  if (!a || !b || a.status !== 'ok' || b.status !== 'ok') return false
  if (a.edge_ids && b.edge_ids) return a.edge_ids.join(',') === b.edge_ids.join(',')
  return JSON.stringify(a.geometry.coordinates) === JSON.stringify(b.geometry.coordinates)
}

export class MapLayers {
  private points = L.layerGroup()
  private routes = L.layerGroup()

  constructor(map: L.Map) {
    this.routes.addTo(map)
    this.points.addTo(map)
  }

  private marker(p: LatLon, label: string, color: string, tooltip?: string) {
    return L.circleMarker([p.lat, p.lon], { radius: 7, color, weight: 3, fillColor: '#fff', fillOpacity: 1 })
      .bindTooltip(tooltip ? `${label} · ${tooltip}` : label, { permanent: true, direction: 'top', offset: [0, -6] })
      .addTo(this.points)
  }

  // Điểm người dùng bấm, trước khi có kết quả.
  setPoints(source: LatLon | null, target: LatLon | null) {
    this.points.clearLayers()
    if (source) this.marker(source, 'Đi', COLORS.source)
    if (target) this.marker(target, 'Đến', COLORS.target)
  }

  // Sau khi có kết quả: marker đặt tại node đã snap, tooltip ghi khoảng cách snap.
  setSnapped(res: RouteResponse) {
    this.points.clearLayers()
    const { source: s, target: t } = res.snapped
    this.marker(s, 'Đi', COLORS.source, `cách ${s.snap_distance_m.toFixed(0)} m`)
    this.marker(t, 'Đến', COLORS.target, `cách ${t.snap_distance_m.toFixed(0)} m`)
  }

  // Trả về các polyline đã vẽ theo thuật toán, để lớp khác (đóng đường) gắn sự kiện.
  drawRoutes(res: RouteResponse): L.Polyline[] {
    this.routes.clearLayers()
    const d = res.results.dijkstra
    const a = res.results.astar
    const drawn: L.Polyline[] = []
    if (sameRoute(d, a)) {
      // Hai tuyến trùng nhau: một nét có viền (ARCHITECTURE mục 6).
      const latlngs = toLatLngs(d!.geometry.coordinates)
      L.polyline(latlngs, { color: COLORS.astar, weight: 10, opacity: 0.9 }).addTo(this.routes)
      drawn.push(L.polyline(latlngs, { color: COLORS.dijkstra, weight: 5 }).bindTooltip('Dijkstra = A*').addTo(this.routes))
      return drawn
    }
    if (d?.status === 'ok') {
      drawn.push(L.polyline(toLatLngs(d.geometry.coordinates), { color: COLORS.dijkstra, weight: 6, opacity: 0.8 })
        .bindTooltip('Dijkstra').addTo(this.routes))
    }
    if (a?.status === 'ok') {
      drawn.push(L.polyline(toLatLngs(a.geometry.coordinates), { color: COLORS.astar, weight: 4, dashArray: '8 6' })
        .bindTooltip('A*').addTo(this.routes))
    }
    return drawn
  }

  clearRoutes() {
    this.routes.clearLayers()
  }

  clear() {
    this.points.clearLayers()
    this.routes.clearLayers()
  }
}
