import json
import urllib.request
import urllib.parse

# ── OpenChargeMap API key (pon la tuya aquí o en variable de entorno)
import os
OCM_API_KEY = os.environ.get('OCM_API_KEY', 'your-api-key-here')
OCM_URL     = 'https://api.openchargemap.io/v3/poi'


# ── HTML embebido ────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EV Charge Map</title>
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #080c10; --surface: #0d1318; --card: #111820; --border: #1e2d3d;
      --accent: #00e5ff; --accent2: #39ff14; --text: #c8d8e8; --muted: #4a6070; --danger: #ff4444;
    }
    body { background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; min-height: 100vh; overflow-x: hidden; }
    body::before {
      content: ''; position: fixed; inset: 0;
      background-image: linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
      background-size: 40px 40px; pointer-events: none; z-index: 0;
    }
    body::after {
      content: ''; position: fixed; top: -200px; left: 50%; transform: translateX(-50%);
      width: 800px; height: 400px;
      background: radial-gradient(ellipse, rgba(0,229,255,0.08) 0%, transparent 70%);
      pointer-events: none; z-index: 0;
    }
    header {
      position: relative; z-index: 1; padding: 32px 40px 24px;
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between; gap: 24px; flex-wrap: wrap;
    }
    .logo { display: flex; align-items: baseline; gap: 12px; }
    .logo-title { font-family: 'Bebas Neue', sans-serif; font-size: 2.6rem; letter-spacing: 4px; color: #fff; line-height: 1; }
    .logo-title span { color: var(--accent); }
    .logo-sub { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: var(--muted); letter-spacing: 3px; text-transform: uppercase; border: 1px solid var(--border); padding: 3px 8px; }
    .header-meta { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: var(--muted); text-align: right; }
    #status-indicator { display: inline-flex; align-items: center; gap: 6px; color: var(--accent2); }
    #status-indicator::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: var(--accent2); animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.8)} }

    /* ── Search bar ── */
    .search-wrap {
      position: relative; z-index: 1; padding: 20px 40px;
      border-bottom: 1px solid var(--border);
      display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
    }
    .search-input {
      flex: 1; min-width: 200px;
      font-family: 'DM Mono', monospace; font-size: 0.85rem; letter-spacing: 1px;
      background: var(--card); border: 1px solid var(--border); color: var(--text);
      padding: 10px 16px; outline: none; transition: border-color .2s;
    }
    .search-input:focus { border-color: var(--accent); }
    .search-input::placeholder { color: var(--muted); }
    .btn-search {
      font-family: 'DM Mono', monospace; font-size: 0.75rem; letter-spacing: 2px; text-transform: uppercase;
      background: var(--accent); border: none; color: var(--bg);
      padding: 10px 24px; cursor: pointer; transition: opacity .2s; white-space: nowrap;
    }
    .btn-search:hover { opacity: .85; }
    .btn-search:disabled { opacity: .4; cursor: not-allowed; }
    .search-hint { font-family: 'DM Mono', monospace; font-size: 0.65rem; color: var(--muted); letter-spacing: 1px; }

    /* ── Controls ── */
    .controls {
      position: relative; z-index: 1; padding: 16px 40px;
      display: flex; align-items: center; gap: 16px; border-bottom: 1px solid var(--border); flex-wrap: wrap;
    }
    .stat-chip { font-family: 'DM Mono', monospace; font-size: .72rem; padding: 6px 14px; border: 1px solid var(--border); color: var(--muted); letter-spacing: 1px; }
    .stat-chip strong { color: var(--accent); font-weight: 500; }
    .view-toggle { display: flex; border: 1px solid var(--border); overflow: hidden; }
    .view-btn { font-family: 'DM Mono', monospace; font-size: .72rem; letter-spacing: 1.5px; text-transform: uppercase; background: transparent; border: none; color: var(--muted); padding: 7px 16px; cursor: pointer; transition: all .2s; }
    .view-btn.active { background: var(--accent); color: var(--bg); }
    .view-btn:not(.active):hover { background: var(--border); color: var(--text); }

    /* ── Map ── */
    #map-wrap { position: relative; z-index: 1; height: 520px; border-bottom: 1px solid var(--border); }
    #map { width: 100%; height: 100%; filter: brightness(.85) saturate(.6) hue-rotate(185deg); }
    .leaflet-popup-content-wrapper { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 0 !important; color: var(--text) !important; box-shadow: 0 8px 32px rgba(0,0,0,.6) !important; }
    .leaflet-popup-tip { background: var(--card) !important; }
    .leaflet-popup-close-button { color: var(--muted) !important; }
    .popup-op { font-family: 'DM Mono', monospace; font-size: .6rem; letter-spacing: 2px; text-transform: uppercase; color: var(--accent); margin-bottom: 4px; }
    .popup-title { font-size: .9rem; font-weight: 500; color: #e8f0f8; margin-bottom: 2px; }
    .popup-addr { font-family: 'DM Mono', monospace; font-size: .68rem; color: var(--muted); margin-bottom: 10px; }
    .popup-badges { display: flex; gap: 6px; flex-wrap: wrap; }

    /* ── Cards ── */
    .grid { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1px; background: var(--border); }
    .card { background: var(--card); padding: 28px; position: relative; overflow: hidden; transition: background .2s; opacity: 0; transform: translateY(20px); animation: fadeUp .4s forwards; cursor: pointer; }
    .card:hover { background: #141e28; }
    .card::before { content: ''; position: absolute; top: 0; left: 0; width: 3px; height: 100%; background: var(--accent); opacity: 0; transition: opacity .2s; }
    .card:hover::before { opacity: 1; }
    @keyframes fadeUp { to { opacity: 1; transform: translateY(0); } }
    .card-index { font-family: 'Bebas Neue', sans-serif; font-size: 4rem; line-height: 1; color: rgba(0,229,255,.06); position: absolute; top: 12px; right: 20px; letter-spacing: 2px; pointer-events: none; }
    .card-operator { font-family: 'DM Mono', monospace; font-size: .65rem; letter-spacing: 2px; text-transform: uppercase; color: var(--accent); margin-bottom: 8px; }
    .card-title { font-size: 1rem; font-weight: 500; color: #e8f0f8; margin-bottom: 4px; line-height: 1.3; }
    .card-address { font-size: .8rem; color: var(--muted); margin-bottom: 20px; font-family: 'DM Mono', monospace; }
    .card-divider { height: 1px; background: var(--border); margin-bottom: 16px; }
    .card-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-size: .8rem; }
    .card-label { color: var(--muted); font-family: 'DM Mono', monospace; font-size: .7rem; letter-spacing: 1px; text-transform: uppercase; }
    .card-value { color: var(--text); font-weight: 500; }
    .badge { font-family: 'DM Mono', monospace; font-size: .65rem; padding: 3px 8px; letter-spacing: 1px; text-transform: uppercase; }
    .badge-green { background: rgba(57,255,20,.1); color: var(--accent2); border: 1px solid rgba(57,255,20,.3); }
    .badge-blue  { background: rgba(0,229,255,.1); color: var(--accent);  border: 1px solid rgba(0,229,255,.3); }
    .badge-red   { background: rgba(255,68,68,.1); color: var(--danger);  border: 1px solid rgba(255,68,68,.3); }
    .connections { margin-top: 14px; display: flex; flex-direction: column; gap: 6px; }
    .conn-item { display: flex; align-items: center; gap: 8px; font-size: .75rem; color: var(--muted); font-family: 'DM Mono', monospace; }
    .conn-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
    .conn-power { margin-left: auto; color: var(--accent2); font-size: .7rem; }

    /* ── Loader / Error ── */
    .loader-wrap { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; gap: 20px; }
    .loader { width: 48px; height: 48px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .loader-text { font-family: 'DM Mono', monospace; font-size: .75rem; color: var(--muted); letter-spacing: 3px; text-transform: uppercase; animation: blink 1.2s infinite; }
    @keyframes blink { 50%{opacity:.3} }
    .error-wrap { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; gap: 16px; text-align: center; padding: 40px; }
    .error-code { font-family: 'Bebas Neue', sans-serif; font-size: 5rem; color: var(--danger); opacity: .3; }
    .error-msg { font-family: 'DM Mono', monospace; font-size: .8rem; color: var(--muted); max-width: 400px; }

    footer { position: relative; z-index: 1; padding: 24px 40px; border-top: 1px solid var(--border); font-family: 'DM Mono', monospace; font-size: .65rem; color: var(--muted); letter-spacing: 1px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }

    @media (max-width: 600px) {
      header, .search-wrap, .controls, footer { padding: 16px 20px; }
      .logo-title { font-size: 2rem; }
      .grid { grid-template-columns: 1fr; }
      #map-wrap { height: 360px; }
    }
  </style>
</head>
<body>

<header>
  <div class="logo">
    <span class="logo-title">EV<span>CHARGE</span></span>
    <span class="logo-sub">MAP</span>
  </div>
  <div class="header-meta">
    <div id="status-indicator">CONECTADO</div>
    <div style="margin-top:6px">FUENTE: OPENCHARGEMAP API</div>
  </div>
</header>

<!-- Buscador -->
<div class="search-wrap">
  <input class="search-input" id="city-input" type="text" placeholder="Escribe una ciudad… ej: Madrid, Barcelona, Sevilla" value="Valencia" />
  <button class="btn-search" id="btn-search" onclick="searchCity()">⚡ BUSCAR</button>
  <span class="search-hint">30 estaciones más cercanas al centro de la ciudad</span>
</div>

<!-- Stats + toggle -->
<div class="controls" id="controls" style="display:none">
  <div class="stat-chip">TOTAL: <strong id="stat-total">—</strong></div>
  <div class="stat-chip">OPERATIVAS: <strong id="stat-op">—</strong></div>
  <div class="stat-chip">CONECTORES: <strong id="stat-conn">—</strong></div>
  <div class="view-toggle">
    <button class="view-btn active" id="btn-map"  onclick="showView('map')">🗺 MAPA</button>
    <button class="view-btn"        id="btn-list" onclick="showView('list')">☰ LISTA</button>
  </div>
</div>

<!-- Mapa -->
<div id="map-wrap">
  <div id="map"></div>
</div>

<!-- Cards -->
<main id="main">
  <div class="loader-wrap">
    <div class="loader"></div>
    <div class="loader-text">Cargando estaciones…</div>
  </div>
</main>

<footer>
  <span>DATA: OPEN CHARGE MAP — CC BY 4.0 · MAPAS: LEAFLET + OPENSTREETMAP</span>
  <span id="footer-time"></span>
</footer>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
  // Apunta al mismo API Gateway — la ruta /stations es la Lambda
  const API_BASE = window.location.pathname.split('/').slice(0, 2).join('/');

  let leafletMap = null;
  let currentView = 'map';

  /* ── Icon ── */
  function makeIcon(op) {
    const color = op ? '#39ff14' : '#ff4444';
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="38" viewBox="0 0 28 38">
      <defs><filter id="g"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <path d="M14 0C6.27 0 0 6.27 0 14c0 10.5 14 24 14 24S28 24.5 28 14C28 6.27 21.73 0 14 0z" fill="#0d1318" stroke="${color}" stroke-width="2" filter="url(#g)"/>
      <circle cx="14" cy="14" r="6" fill="${color}" opacity=".9" filter="url(#g)"/>
    </svg>`;
    return L.divIcon({ html: svg, className: '', iconSize: [28,38], iconAnchor: [14,38], popupAnchor: [0,-38] });
  }

  /* ── Toggle vistas ── */
  function showView(view) {
    currentView = view;
    document.getElementById('btn-map').classList.toggle('active',  view === 'map');
    document.getElementById('btn-list').classList.toggle('active', view === 'list');
    document.getElementById('map-wrap').style.display = view === 'map'  ? 'block' : 'none';
    document.getElementById('main').style.display     = view === 'list' ? 'block' : 'none';
    if (view === 'map' && leafletMap) setTimeout(() => leafletMap.invalidateSize(), 50);
  }

  /* ── Buscar ciudad ── */
  function searchCity() {
    const city = document.getElementById('city-input').value.trim();
    if (!city) return;
    fetchStations(city);
  }

  // Enter en el input
  document.getElementById('city-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') searchCity();
  });

  /* ── Fetch ── */
  async function fetchStations(city = 'Valencia') {
    document.getElementById('btn-search').disabled = true;
    document.getElementById('controls').style.display = 'none';
    document.getElementById('map-wrap').style.display = 'none';
    document.getElementById('main').style.display = 'block';
    document.getElementById('main').innerHTML = `
      <div class="loader-wrap">
        <div class="loader"></div>
        <div class="loader-text">Buscando en ${city}…</div>
      </div>`;

    try {
      const url = `${API_BASE}/stations?city=${encodeURIComponent(city)}&maxresults=30`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      const stations = extractStations(json);
      if (!stations || stations.length === 0) throw new Error('Sin resultados para ' + city);
      renderAll(stations, city);
    } catch (err) {
      document.getElementById('main').innerHTML = `
        <div class="error-wrap">
          <div class="error-code">ERR</div>
          <div class="error-msg">${err.message}</div>
        </div>`;
    }
    document.getElementById('btn-search').disabled = false;
  }

  function extractStations(json) {
    if (Array.isArray(json)) return json;
    if (Array.isArray(json.data)) return json.data;
    if (typeof json.body === 'string') {
      try { const p = JSON.parse(json.body); return Array.isArray(p) ? p : (Array.isArray(p.data) ? p.data : null); } catch(e) {}
    }
    if (json.body && Array.isArray(json.body)) return json.body;
    return null;
  }

  /* ── Render ── */
  function renderAll(stations, city) {
    document.getElementById('controls').style.display = 'flex';
    document.getElementById('stat-total').textContent = stations.length;
    document.getElementById('stat-op').textContent = stations.filter(s => s.StatusType?.IsOperational).length;
    document.getElementById('stat-conn').textContent = stations.reduce((a, s) =>
      a + (s.Connections || []).reduce((b, c) => b + (c.Quantity || 1), 0), 0);

    renderMap(stations);
    renderList(stations);
    showView('map');

    document.getElementById('footer-time').textContent =
      city.toUpperCase() + ' · ' + new Date().toLocaleString('es-ES', { hour12: false });
  }

  function renderMap(stations) {
    const pts = stations.filter(s => s.AddressInfo?.Latitude != null);

    if (!leafletMap) {
      leafletMap = L.map('map');
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO &copy; OSM contributors',
        subdomains: 'abcd', maxZoom: 19
      }).addTo(leafletMap);
    } else {
      leafletMap.eachLayer(l => { if (l instanceof L.Marker) leafletMap.removeLayer(l); });
    }

    if (!pts.length) return;
    const bounds = [];

    pts.forEach(s => {
      const addr = s.AddressInfo;
      const isOp = s.StatusType?.IsOperational;
      const conns = s.Connections || [];

      const popup = `
        <div style="min-width:200px">
          <div class="popup-op">${s.OperatorInfo?.Title || 'Desconocido'}</div>
          <div class="popup-title">${addr.Title || 'Sin nombre'}</div>
          <div class="popup-addr">${addr.AddressLine1 || ''}, ${addr.Town || ''}</div>
          <div class="popup-badges">
            ${isOp ? '<span class="badge badge-green">Operativa</span>' : '<span class="badge badge-red">Fuera de servicio</span>'}
            ${(s.UsageType?.Title||'').toLowerCase().includes('public') ? '<span class="badge badge-blue">Público</span>' : '<span class="badge badge-red">Membresía</span>'}
          </div>
          ${conns.length ? `<div style="margin-top:8px;font-family:'DM Mono',monospace;font-size:.65rem;color:var(--muted)">${conns.map(c=>`${c.ConnectionType?.Title||'—'} ×${c.Quantity||1}${c.PowerKW?' · '+c.PowerKW+' kW':''}`).join('<br>')}</div>` : ''}
        </div>`;

      L.marker([addr.Latitude, addr.Longitude], { icon: makeIcon(isOp) })
        .bindPopup(popup, { maxWidth: 280 })
        .addTo(leafletMap);
      bounds.push([addr.Latitude, addr.Longitude]);
    });

    leafletMap.fitBounds(bounds, { padding: [40, 40] });
  }

  function renderList(stations) {
    const grid = document.createElement('div');
    grid.className = 'grid';

    stations.forEach((s, i) => {
      const addr  = s.AddressInfo || {};
      const isOp  = s.StatusType?.IsOperational;
      const usage = s.UsageType?.Title || '—';
      const conns = s.Connections || [];

      const card = document.createElement('div');
      card.className = 'card';
      card.style.animationDelay = `${i * 50}ms`;
      card.innerHTML = `
        <div class="card-index">${String(i+1).padStart(2,'0')}</div>
        <div class="card-operator">${s.OperatorInfo?.Title || 'Desconocido'}</div>
        <div class="card-title">${addr.Title || 'Sin nombre'}</div>
        <div class="card-address">${addr.AddressLine1||''}, ${addr.Town||''} ${addr.Postcode||''}</div>
        <div class="card-divider"></div>
        <div class="card-row">
          <span class="card-label">Estado</span>
          ${isOp ? '<span class="badge badge-green">Operativa</span>' : '<span class="badge badge-red">Fuera de servicio</span>'}
        </div>
        <div class="card-row">
          <span class="card-label">Acceso</span>
          ${usage.toLowerCase().includes('public') ? '<span class="badge badge-blue">Público</span>' : '<span class="badge badge-red">Membresía</span>'}
        </div>
        <div class="card-row">
          <span class="card-label">Puntos</span>
          <span class="card-value">${s.NumberOfPoints || '—'}</span>
        </div>
        ${conns.length ? `<div class="card-divider" style="margin-top:16px"></div>
        <div class="connections">${conns.map(c=>`<div class="conn-item"><span class="conn-dot"></span><span>${c.ConnectionType?.Title||'—'} ×${c.Quantity||1}</span><span class="conn-power">${c.PowerKW?c.PowerKW+' kW':''}</span></div>`).join('')}</div>` : ''}
      `;

      if (addr.Latitude && addr.Longitude) {
        card.title = 'Ver en mapa';
        card.addEventListener('click', () => {
          showView('map');
          setTimeout(() => {
            leafletMap.setView([addr.Latitude, addr.Longitude], 15);
            leafletMap.eachLayer(l => {
              if (l instanceof L.Marker) {
                const ll = l.getLatLng();
                if (Math.abs(ll.lat - addr.Latitude) < 0.0001 && Math.abs(ll.lng - addr.Longitude) < 0.0001)
                  l.openPopup();
              }
            });
          }, 80);
        });
      }
      grid.appendChild(card);
    });

    const main = document.getElementById('main');
    main.innerHTML = '';
    main.appendChild(grid);
  }

  // Carga inicial: Valencia
  fetchStations('Valencia');
</script>
</body>
</html>"""


# ── Lambda handler ────────────────────────────────────────────────────────────
def lambda_handler(event, context):
    path = event.get('path') or event.get('rawPath') or '/'

    # ── GET /web  →  devuelve el HTML
    if path == '/web':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
                'Cache-Control': 'no-cache',
            },
            'body': HTML,
        }

    # ── GET /stations  →  geocodifica ciudad y llama a OpenChargeMap
    if path == '/stations':
        params     = event.get('queryStringParameters') or {}
        city       = params.get('city', 'Valencia')
        maxresults = params.get('maxresults', '30')
        distance   = params.get('distance', '10')   # km de radio

        # 1️⃣  Geocoding: ciudad → lat/lng  (Nominatim, gratuito, sin key)
        nominatim_params = urllib.parse.urlencode({
            'q':              city,
            'format':         'json',
            'limit':          1,
            'addressdetails': 0,
        })
        geo_req = urllib.request.Request(
            f'https://nominatim.openstreetmap.org/search?{nominatim_params}',
            headers={'User-Agent': 'EVChargeMap/1.0'}
        )
        try:
            with urllib.request.urlopen(geo_req, timeout=8) as resp:
                geo_data = json.loads(resp.read())
        except Exception as e:
            return _json_response(502, {'error': f'Geocoding error: {e}'})

        if not geo_data:
            return _json_response(404, {'error': f'Ciudad no encontrada: {city}'})

        lat = geo_data[0]['lat']
        lng = geo_data[0]['lon']

        # 2️⃣  OpenChargeMap por coordenadas + radio
        ocm_params = urllib.parse.urlencode({
            'output':     'json',
            'latitude':   lat,
            'longitude':  lng,
            'distance':   distance,
            'distanceunit': 'km',
            'maxresults': maxresults,
            'compact':    'false',
            'verbose':    'false',
            'key':        OCM_API_KEY,
        })
        ocm_req = urllib.request.Request(
            f'{OCM_URL}?{ocm_params}',
            headers={'User-Agent': 'EVChargeMap/1.0'}
        )
        try:
            with urllib.request.urlopen(ocm_req, timeout=10) as resp:
                data = resp.read()
        except Exception as e:
            return _json_response(502, {'error': f'OCM error: {e}'})

        return {
            'statusCode': 200,
            'headers': _cors_headers({'Content-Type': 'application/json'}),
            'body': data.decode('utf-8'),
        }

    # ── 404 para cualquier otra ruta
    return _json_response(404, {'error': f'Ruta no encontrada: {path}'})


# ── Helpers ──────────────────────────────────────────────────────────────────
def _cors_headers(extra=None):
    headers = {
        'Access-Control-Allow-Origin':  '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    if extra:
        headers.update(extra)
    return headers


def _json_response(status, body):
    return {
        'statusCode': status,
        'headers': _cors_headers({'Content-Type': 'application/json'}),
        'body': json.dumps(body),
    }