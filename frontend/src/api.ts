// Kiểu dữ liệu theo contract v1 (docs/ARCHITECTURE.md mục 4.1). Bản sau chỉ được thêm trường.

export interface HealthResponse {
  status: string
  dataset_loaded: boolean
  dataset_id?: string | null
}

export interface LatLon {
  lat: number
  lon: number
}

export type Algorithm = 'dijkstra' | 'astar'

export interface RouteRequest {
  source: LatLon
  target: LatLon
  algorithms?: Algorithm[]
}

export interface SnappedPoint {
  node_id: number
  lat: number
  lon: number
  snap_distance_m: number
}

export interface LineString {
  type: 'LineString'
  coordinates: [number, number][] // [lon, lat] theo GeoJSON
}

export interface AlgorithmResult {
  status: 'ok' | 'no_path'
  cost_s: number | null
  distance_m: number | null
  geometry: LineString
  expanded: number
  runtime_ms: number
}

export interface RouteResponse {
  dataset_id: string
  snapped: { source: SnappedPoint; target: SnappedPoint }
  results: Partial<Record<Algorithm, AlgorithmResult>>
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch('/api/health')
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// Lỗi từ API: FastAPI trả `detail` là chuỗi (503) hoặc danh sách lỗi kiểm tra dữ liệu (422).
function errorMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => (d as { msg?: string }).msg ?? JSON.stringify(d)).join('; ')
  }
  return `HTTP ${status}`
}

export async function postRoute(req: RouteRequest, signal?: AbortSignal): Promise<RouteResponse> {
  const res = await fetch('/api/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal,
  })
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new Error(errorMessage(res.status, body))
  return body as RouteResponse
}
