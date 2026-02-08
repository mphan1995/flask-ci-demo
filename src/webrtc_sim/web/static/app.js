const state = {
  peers: [],
  lastUpdated: null,
};

const el = {
  tableBody: document.querySelector('#peer-table tbody'),
  peerCount: document.querySelector('#peer-count'),
  health: document.querySelector('#health-badge'),
  mode: document.querySelector('#mode-badge'),
  lastUpdated: document.querySelector('#last-updated'),
  log: document.querySelector('#log'),
  refresh: document.querySelector('#refresh'),
  stopAll: document.querySelector('#stop-all'),
  clearLog: document.querySelector('#clear-log'),
};

async function api(path, options = {}) {
  try {
    const res = await fetch(path, options);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) return await res.json();
    return await res.text();
  } catch (err) {
    log(`Error: ${err.message}`, 'error');
    throw err;
  }
}

function log(message, level = 'info') {
  const entry = document.createElement('div');
  entry.className = 'entry';
  entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  if (level === 'error') entry.style.color = '#ff9c9c';
  el.log.prepend(entry);
  const max = 100;
  while (el.log.children.length > max) {
    el.log.removeChild(el.log.lastChild);
  }
  flashBadge();
}

function updateBadges() {
  el.peerCount.textContent = `Peers: ${state.peers.length}`;
  el.lastUpdated.textContent = state.lastUpdated
    ? `Cập nhật: ${state.lastUpdated.toLocaleTimeString()}`
    : 'Cập nhật: —';
}

function flashBadge() {
  el.peerCount.classList.remove('pulse');
  void el.peerCount.offsetWidth; // restart animation
  el.peerCount.classList.add('pulse');
}

// ---------- SVG orb field (DOM + SVG + Events) ----------
let orbState = { width: 0, height: 0, circles: [], mouseX: 0, mouseY: 0, raf: null };

function initOrbField() {
  const svg = document.getElementById('orb-field');
  const container = document.getElementById('orb-field-container');
  if (!svg || !container) return;

  const { clientWidth, clientHeight } = container;
  orbState.width = clientWidth;
  orbState.height = clientHeight;
  svg.setAttribute('viewBox', `0 0 ${clientWidth} ${clientHeight}`);
  svg.innerHTML = '';

  const palette = ['#7dd3fc', '#58c4ff', '#9ef0b8', '#c084fc'];
  const count = 10;
   // subtle gradient background
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  const grad = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
  grad.setAttribute('id', 'bg-grad');
  grad.innerHTML = `
    <stop offset="0%" stop-color="#7dd3fc" stop-opacity="0.4"/>
    <stop offset="50%" stop-color="#c084fc" stop-opacity="0.15"/>
    <stop offset="100%" stop-color="#58c4ff" stop-opacity="0"/>
  `;
  defs.appendChild(grad);
  svg.appendChild(defs);
  const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bg.setAttribute('width', '100%');
  bg.setAttribute('height', '100%');
  bg.setAttribute('fill', 'url(#bg-grad)');
  svg.appendChild(bg);

  orbState.circles = Array.from({ length: count }).map((_, i) => {
    const r = 120 + Math.random() * 120;
    const cx = Math.random() * clientWidth;
    const cy = Math.random() * clientHeight;
    const speed = 0.3 + Math.random() * 0.6;
    const dir = Math.random() > 0.5 ? 1 : -1;
    const hue = palette[i % palette.length];
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('r', r.toFixed(1));
    circle.setAttribute('cx', cx.toFixed(1));
    circle.setAttribute('cy', cy.toFixed(1));
    circle.setAttribute('fill', hue);
    svg.appendChild(circle);
    return { el: circle, r, cx, cy, speed, dir };
  });

  const animate = () => {
    const t = Date.now() * 0.001;
    orbState.circles.forEach((c, idx) => {
      const driftX = Math.sin(t * c.speed + idx) * 18 * c.dir;
      const driftY = Math.cos(t * c.speed + idx * 0.7) * 18 * c.dir;
      const parallaxX = (orbState.mouseX - orbState.width / 2) * 0.02;
      const parallaxY = (orbState.mouseY - orbState.height / 2) * 0.02;
      c.el.setAttribute('cx', (c.cx + driftX + parallaxX).toFixed(1));
      c.el.setAttribute('cy', (c.cy + driftY + parallaxY).toFixed(1));
    });
    orbState.raf = requestAnimationFrame(animate);
  };
  if (orbState.raf) cancelAnimationFrame(orbState.raf);
  orbState.raf = requestAnimationFrame(animate);
}

function handleMouseMove(e) {
  orbState.mouseX = e.clientX;
  orbState.mouseY = e.clientY;
}

window.addEventListener('resize', initOrbField);
window.addEventListener('mousemove', handleMouseMove);

function renderPeers() {
  el.tableBody.innerHTML = '';
  state.peers.forEach((peer) => {
    const tr = document.createElement('tr');
    const stopBtn = `<button class="action-btn danger" data-id="${peer.peer_id}">Stop</button>`;
    tr.innerHTML = `
      <td>${peer.peer_id}</td>
      <td>${peer.state}</td>
      <td>${peer.target}</td>
      <td>${stopBtn}</td>
    `;
    el.tableBody.appendChild(tr);
  });

  document.querySelectorAll('.action-btn.danger').forEach((btn) => {
    btn.onclick = async () => {
      const id = btn.getAttribute('data-id');
      await api(`/control/peers/${id}`, { method: 'DELETE' });
      log(`Peer ${id} stopped`);
      await refreshPeers();
    };
  });
}

async function refreshPeers() {
  const peers = await api('/control/peers');
  state.peers = peers;
  state.lastUpdated = new Date();
  renderPeers();
  updateBadges();
}

async function healthCheck() {
  try {
    const res = await api('/health');
    const ok = res.status === 'ok';
    el.health.innerHTML = `<span class="status-dot ${ok ? 'ok' : 'bad'}"></span>Health: ${res.status}`;
  } catch (err) {
    el.health.innerHTML = `<span class="status-dot bad"></span>Health: down`;
  }
}

function initModeBadge() {
  const mode = document.body.dataset.mode || 'unknown';
  el.mode.textContent = `Mode: ${mode}`;
}

async function createPeer() {
  const target = document.querySelector('#target').value;
  const video_profile = document.querySelector('#video_profile').value;
  const audio_profile = document.querySelector('#audio_profile').value;
  await api('/control/peers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target, video_profile, audio_profile }),
  });
  log(`Created peer for ${target}`);
  await refreshPeers();
}

async function scalePeers() {
  const target_count = parseInt(document.querySelector('#scale_count').value, 10);
  const target = document.querySelector('#scale_target').value || document.querySelector('#target').value;
  const video_profile = document.querySelector('#scale_video_profile').value || document.querySelector('#video_profile').value;
  const audio_profile = document.querySelector('#scale_audio_profile').value || document.querySelector('#audio_profile').value;
  await api('/control/scale', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_count, target, video_profile, audio_profile }),
  });
  log(`Scaled peers to ${target_count}`);
  await refreshPeers();
}

async function stopAllPeers() {
  const peers = await api('/control/peers');
  await Promise.all(peers.map((p) => api(`/control/peers/${p.peer_id}`, { method: 'DELETE' }).catch(() => {})));
  log('Stopped all peers');
  await refreshPeers();
}

function wireEvents() {
  document.querySelector('#create').onclick = createPeer;
  document.querySelector('#scale').onclick = scalePeers;
  el.refresh.onclick = refreshPeers;
  el.stopAll.onclick = stopAllPeers;
  el.clearLog.onclick = () => (el.log.innerHTML = '');
}

async function init() {
  initModeBadge();
  wireEvents();
  initOrbField();
  await refreshPeers();
  await healthCheck();
  setInterval(refreshPeers, 4000);
  setInterval(healthCheck, 7000);
}

init();
