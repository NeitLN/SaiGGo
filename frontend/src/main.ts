import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import './style.css'
import { getHealth } from './api'

const app = document.querySelector<HTMLDivElement>('#app')!
app.innerHTML = `
  <header class="topbar">
    <strong>SaiGo</strong>
    <span class="subtitle">Lập kế hoạch lộ trình giao hàng</span>
    <span id="server-status" class="status">Đang kiểm tra server…</span>
  </header>
  <main class="layout">
    <aside class="panel">
      <p>Khung giao diện ban đầu. Mạng đường, điểm giao và lộ trình sẽ được thêm sau khi có dataset.</p>
    </aside>
    <div id="map"></div>
  </main>
`

// Tâm tạm thời quanh trung tâm TP.HCM; phạm vi chính thức lấy từ /api/dataset khi có.
const map = L.map('map').setView([10.776, 106.7], 14)

// Chưa có nền bản đồ offline: lớp mạng đường sẽ được vẽ từ GeoJSON của dataset.
// Chỉ giữ ghi nguồn OpenStreetMap theo yêu cầu giấy phép.
map.attributionControl.addAttribution(
  'Dữ liệu © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
)

const statusEl = document.querySelector<HTMLSpanElement>('#server-status')!
getHealth()
  .then((h) => {
    statusEl.textContent = h.dataset_loaded ? 'Server sẵn sàng' : 'Server chạy, chưa nạp dataset'
  })
  .catch(() => {
    statusEl.textContent = 'Không kết nối được server'
  })
