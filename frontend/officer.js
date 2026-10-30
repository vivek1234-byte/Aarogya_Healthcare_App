/**
 * AROGYASAATHI - BLOCK / DISTRICT HEALTH OFFICER CONTROLLER
 * Village map (Leaflet + OpenStreetMap), fused syndromic signals per village,
 * alert acknowledgement with response checklist, and the audit trail.
 */

const OFFICER = requireRole('HEALTH_OFFICER');

let block = null;
let selectedVillageId = null;
let map = null;
let markerLayer = null;

const RISK_COLOR = { OUTBREAK: '#EF4444', WARNING: '#F97316', WATCH: '#F59E0B', NORMAL: '#10B981', NO_BASELINE: '#94A3B8' };

document.addEventListener('DOMContentLoaded', () => {
  if (!OFFICER) return;
  setupTabs((tab) => {
    if (tab === 'audit') refreshAudit();
    if (tab === 'signals') renderSignals();
    if (tab === 'map' && map) setTimeout(() => map.invalidateSize(), 50);
  });
  document.getElementById('refreshBtn').addEventListener('click', loadBlock);
  document.getElementById('refreshAuditBtn').addEventListener('click', refreshAudit);
  document.getElementById('signalVillage').addEventListener('change', (e) => {
    selectedVillageId = e.target.value;
    renderSignals();
  });
  loadBlock();
  if (window.location.hash === '#audit') refreshAudit();
});

async function loadBlock() {
  try {
    block = await api('/api/v1/surveillance/block');
  } catch (err) {
    document.getElementById('alertPanel').innerHTML = `<div class="panel"><p class="empty-state">${esc(err.message)}</p></div>`;
    return;
  }
  document.getElementById('baselineDays').textContent = block.baseline_min_days;
  const ranked = block.villages.slice().sort((a, b) => maxZ(b) - maxZ(a));
  if (!selectedVillageId && ranked.length) selectedVillageId = ranked[0].id;
  document.getElementById('signalVillage').innerHTML = block.villages
    .map((v) => `<option value="${esc(v.id)}">${esc(v.name)}, ${esc(v.district)}</option>`).join('');
  renderStats();
  renderMap();
  renderAlerts();
  renderSignals();
}

function maxZ(v) {
  return Math.max(...Object.values(v.evaluations).map((e) => (e ? e.z_score : -99)));
}

function zText(e) {
  return e ? `${e.z_score} ${LEVEL_TEXT[e.risk_level] ? `(${LEVEL_TEXT[e.risk_level]})` : ''}` : '–';
}

// ================= 1. STATS =================
function renderStats() {
  const active = block.alerts.filter((a) => a.status === 'ACTIVE').length;
  document.getElementById('statVillages').textContent = block.villages.length;
  document.getElementById('statAlerts').textContent = active;
  document.getElementById('statReporting').textContent = `${block.reporting_today}/${block.villages.length}`;
  document.getElementById('statBaseline').textContent = block.villages.filter((v) => v.risk_level !== 'NO_BASELINE').length;
  const count = document.getElementById('alertCount');
  count.textContent = active;
  count.classList.toggle('hidden', active === 0);
}

// ================= 2. MAP =================
function renderMap() {
  const host = document.getElementById('villageMap');
  const located = block.villages.filter((v) => v.lat != null && v.lon != null);
  if (!window.L) {
    host.innerHTML = '<p class="empty-state">Map could not load (no internet). Village list is in the Signals tab.</p>';
    return;
  }
  if (!located.length) {
    host.innerHTML = '<p class="empty-state">No village has GPS yet. ASHAs add it when they create their account ("Use my current location").</p>';
    return;
  }
  if (!map) {
    map = L.map(host, { scrollWheelZoom: false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    markerLayer = L.layerGroup().addTo(map);
  }
  markerLayer.clearLayers();
  const alertVillages = new Set(block.alerts.filter((a) => a.status === 'ACTIVE').flatMap((a) => a.village_ids));
  located.forEach((v) => {
    const color = RISK_COLOR[v.risk_level] || RISK_COLOR.NO_BASELINE;
    if (alertVillages.has(v.id)) {
      L.circle([v.lat, v.lon], { radius: 3000, color: '#DC2626', weight: 2, dashArray: '6 4', fillOpacity: 0.05 }).addTo(markerLayer);
    }
    const marker = L.circleMarker([v.lat, v.lon], {
      radius: 11, color: '#FFFFFF', weight: 2, fillColor: color, fillOpacity: 0.95
    }).addTo(markerLayer);
    marker.bindTooltip(`${v.name}: ${LEVEL_TEXT[v.risk_level] || v.risk_level}`);
    marker.on('click', () => {
      selectedVillageId = v.id;
      switchTab('signals', () => renderSignals());
    });
  });
  map.fitBounds(L.latLngBounds(located.map((v) => [v.lat, v.lon])).pad(0.4), { maxZoom: 12 });
  setTimeout(() => map.invalidateSize(), 50);
}

// ================= 3. ALERTS =================
function renderAlerts() {
  const host = document.getElementById('alertPanel');
  if (!block.alerts.length) {
    host.innerHTML = `<div class="panel"><div class="panel-title">Alerts</div>
      <p class="empty-state">No outbreak alerts in the last 14 days.</p>
      <div class="notice notice-blue"><span>ℹ️</span><span>Alerts start once villages have ${esc(block.baseline_min_days)}+ days of ASHA reports. ${esc(block.reporting_today)} of ${esc(block.villages.length)} villages reported today.</span></div></div>`;
    return;
  }
  host.innerHTML = block.alerts.map((a) => {
    const d = a.details;
    return `
    <div class="panel">
      <div class="view-head" style="margin-bottom: 8px;">
        <div>
          <div class="panel-title">${esc(d.label)}</div>
          <div class="list-meta">${esc(a.id)} · ${esc(formatDateTime(a.created_at))}</div>
        </div>
        ${levelBadge(a.status)}
      </div>
      <div class="notice notice-red"><span>📍</span><span><strong>${d.villages.map((v) => esc(v.name)).join(', ')}</strong><br>
        ${esc(d.observed)} combined signals vs ${esc(d.expected)} expected · z-score ${esc(d.z_score)} · confidence ${Math.round(d.confidence * 100)}%</span></div>
      <div class="decision-section">
        <h4>Rapid response checklist</h4>
        <ul class="checklist">${d.interventions.map((c) => `<li><label><input type="checkbox" ${a.status === 'ACKNOWLEDGED' ? 'checked disabled' : ''}><span>${esc(c)}</span></label></li>`).join('')}</ul>
      </div>
      ${a.status === 'ACTIVE' ? `
        <form class="ack-form" data-id="${esc(a.id)}" style="margin-top: 14px;">
          <div class="form-group">
            <label for="ackNote-${esc(a.id)}">Response note</label>
            <textarea id="ackNote-${esc(a.id)}" class="form-textarea" placeholder="e.g. RRT sent, chlorination started in Ward 2."></textarea>
          </div>
          <button type="submit" class="btn btn-red btn-block">Acknowledge &amp; dispatch response</button>
        </form>` : `
        <div class="notice notice-green" style="margin-top: 12px;"><span>✅</span><span>Acknowledged by ${esc(a.ack_by_name || a.ack_by)} · ${esc(formatDateTime(a.ack_at))}${a.ack_note ? `<br>${esc(a.ack_note)}` : ''}</span></div>`}
    </div>`;
  }).join('');
  host.querySelectorAll('.ack-form').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = form.dataset.id;
      try {
        await api(`/api/v1/surveillance/alerts/${id}/ack`, { note: document.getElementById(`ackNote-${id}`).value.trim() });
        showToast('Alert acknowledged and logged');
        await loadBlock();
      } catch (err) {
        showToast(err.message);
      }
    });
  });
}

// ================= 4. SIGNALS =================
function renderSignals() {
  if (!block) return;
  const v = block.villages.find((x) => x.id === selectedVillageId);
  if (!v) {
    document.getElementById('signalChart').innerHTML = '<p class="empty-state">No villages yet. They appear when ASHAs sign up.</p>';
    document.getElementById('villageTable').innerHTML = '';
    return;
  }
  document.getElementById('signalVillage').value = v.id;
  document.getElementById('signalTitle').innerHTML = `${esc(v.name)} ${levelBadge(v.risk_level)}`;
  document.getElementById('signalSub').textContent = v.risk_level === 'NO_BASELINE'
    ? `Collecting history: ${v.baseline_days} of ${block.baseline_min_days} days reported.`
    : `Fever z ${zText(v.evaluations.ACUTE_FEBRILE_ILLNESS)} · Diarrhoea z ${zText(v.evaluations.ACUTE_DIARRHOEAL_DISEASE)}`;
  const s = v.series;
  renderLineChart(document.getElementById('signalChart'), {
    labels: s.dates.map((d) => d.slice(8, 10) + '/' + d.slice(5, 7)),
    series: [
      { name: 'Clinic: fever', color: '#EF4444', values: s.clinic_ACUTE_FEBRILE_ILLNESS },
      { name: 'Clinic: diarrhoea', color: '#3B82F6', values: s.clinic_ACUTE_DIARRHOEAL_DISEASE },
      { name: 'Chemist: ORS', color: '#F97316', values: s.pharmacy_ors_sales },
      { name: 'Chemist: fever medicine', color: '#EC4899', values: s.pharmacy_fever_sales },
      { name: 'School absent', color: '#8B5CF6', values: s.school_absent }
    ],
    yMin: 0,
    height: 260
  });
  document.getElementById('villageTable').innerHTML = block.villages.slice().sort((a, b) => maxZ(b) - maxZ(a)).map((x) => `
    <tr>
      <td><strong>${esc(x.name)}</strong><div class="list-meta">${esc(x.district)}${x.lat == null ? ' · no GPS' : ''}</div></td>
      <td>${levelBadge(x.risk_level)}</td>
      <td>${esc(zText(x.evaluations.ACUTE_FEBRILE_ILLNESS))}</td>
      <td>${esc(zText(x.evaluations.ACUTE_DIARRHOEAL_DISEASE))}</td>
      <td>${esc(x.baseline_days)}</td>
      <td>${x.series.reported_today ? '✅' : '—'}</td>
    </tr>`).join('');
}

// ================= 5. AUDIT =================
function refreshAudit() {
  loadAuditTrail(document.getElementById('auditBody'), document.getElementById('auditStatus'));
}
