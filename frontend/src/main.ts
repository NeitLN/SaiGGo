import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import './style.css'
import { getHealth, postRoute, type LatLon, type RouteResponse } from './api'

const app = document.querySelector<HTMLDivElement>('#app')!
app.innerHTML = `
  <header class="topbar">
    <strong>SaiGo</strong>
    <span class="subtitle">Lập kế hoạch lộ trình giao hàng</span>
    <span id="server-status" class="status">Đang kiểm tra server…</span>
  </header>
  <main class="layout">
    <aside class="panel">
      <p id="hint" class="hint">Bấm lên bản đồ để chọn <strong>điểm đi</strong>.</p>
      <dl id="result" class="result" hidden>
        <dt>Thời gian di chuyển ước tính (theo kịch bản)</dt><dd id="cost">—</dd>
        <dt>Quãng đường</dt><dd id="distance">—</dd>
        <dt>Số node mở rộng</dt><dd id="expanded">—</dd>
        <dt>Thời gian tính toán</dt><dd id="runtime">—</dd>
        <dt>Điểm đi / điểm đến đã gắn vào node</dt><dd id="snapped">—</dd>
      </dl>
      <p id="message" class="message" hidden></p>
    </aside>
    <div id="map"></div>
  </main>
`

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T

// Tâm quanh chợ Bến Thành (cùng tâm với data/config/areas.json).
const map = L.map('map').setView([10.7725, 106.7], 16)

// Nền tile OSM chỉ để xem tương tác, không tải hàng loạt (docs/ARCHITECTURE.md mục 6).
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: 'Dữ liệu © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
}).addTo(map)

const marks = L.layerGroup().addTo(map)
const routeLayer = L.layerGroup().addTo(map)

let source: LatLon | null = null
let pending: AbortController | null = null
let requestId = 0

function show(el: HTMLElement, text: string | null) {
  el.hidden = text === null
  if (text !== null) el.textContent = text
}

function pointMarker(p: LatLon, label: string, color: string) {
  return L.circleMarker([p.lat, p.lon], { radius: 7, color, weight: 2, fillColor: '#fff', fillOpacity: 1 })
    .bindTooltip(label, { permanent: true, direction: 'top', offset: [0, -6] })
}

function reset() {
  pending?.abort()
  pending = null
  requestId++
  source = null
  marks.clearLayers()
  routeLayer.clearLayers()
  $('result').hidden = true
  show($('message'), null)
}

function render(res: RouteResponse) {
  const r = res.results.dijkstra
  const { source: s, target: t } = res.snapped
  $('snapped').textContent = `node ${s.node_id} (cách ${s.snap_distance_m.toFixed(0)} m) → node ${t.node_id} (cách ${t.snap_distance_m.toFixed(0)} m)`
  if (!r) {
    show($('message'), 'API không trả kết quả cho Dijkstra.')
    return
  }
  $('expanded').textContent = String(r.expanded)
  $('runtime').textContent = `${r.runtime_ms.toFixed(2)} ms`
  $('result').hidden = false
  if (r.status === 'no_path') {
    // Không vẽ đường thẳng nối hai điểm khi không có đường.
    $('cost').textContent = '—'
    $('distance').textContent = '—'
    show($('message'), 'Không có đường đi giữa hai điểm này.')
    return
  }
  $('cost').textContent = `${r.cost_s!.toFixed(1)} s`
  $('distance').textContent = `${r.distance_m!.toFixed(0)} m`
  // GeoJSON là [lon, lat]; Leaflet cần [lat, lon].
  const latlngs = r.geometry.coordinates.map(([lon, lat]) => L.latLng(lat, lon))
  L.polyline(latlngs, { color: '#1c7ed6', weight: 5, opacity: 0.85 }).addTo(routeLayer)
}

async function findRoute(src: LatLon, dst: LatLon) {
  const id = ++requestId
  pending?.abort()
  pending = new AbortController()
  show($('hint'), 'Đang tìm đường… Bấm lần nữa để chọn lại điểm đi.')
  try {
    const res = await postRoute({ source: src, target: dst, algorithms: ['dijkstra'] }, pending.signal)
    if (id !== requestId) return // đã có request mới hơn
    render(res)
  } catch (err) {
    if (id !== requestId || (err as Error).name === 'AbortError') return
    show($('message'), `Lỗi từ API: ${(err as Error).message}`)
  }
  if (id === requestId) $('hint').innerHTML = 'Bấm lên bản đồ để chọn <strong>điểm đi</strong> mới.'
}

// Lần 1: điểm đi · lần 2: điểm đến và tìm đường · lần 3: bắt đầu lại.
map.on('click', (e: L.LeafletMouseEvent) => {
  const p = { lat: e.latlng.lat, lon: e.latlng.lng }
  if (source === null) {
    reset()
    source = p
    pointMarker(p, 'Đi', '#2f9e44').addTo(marks)
    $('hint').innerHTML = 'Bấm để chọn <strong>điểm đến</strong>.'
  } else {
    pointMarker(p, 'Đến', '#e03131').addTo(marks)
    const src = source
    source = null
    void findRoute(src, p)
  }
})

const statusEl = $('server-status')
getHealth()
  .then((h) => {
    statusEl.textContent = h.dataset_loaded ? `Server sẵn sàng · dataset ${h.dataset_id ?? ''}` : 'Server chạy, chưa nạp dataset'
  })
  .catch(() => {
    statusEl.textContent = 'Không kết nối được server'
  })
