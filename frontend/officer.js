/**
 * AROGYASAATHI - BLOCK / DISTRICT HEALTH OFFICER CONTROLLER
 * Village outbreak map, fused syndromic signals, alert acknowledgement
 * with rapid-response checklist, and the audit trail.
 */

const OFFICER_ID = requireStaffRole('Health Officer');

let block = null;
let selectedVillageId = null;

const RISK_FILL = { OUTBREAK: '#FCA5A5', WARNING: '#FDBA74', WATCH: '#FDE68A', NORMAL: '#A7F3D0' };

document.addEventListener('DOMContentLoaded', () => {
  if (!OFFICER_ID) return;
  setupTabs((tab) => {
    if (tab === 'audit') refreshAudit();
    if (tab === 'signals') renderSignals();
  });
  document.getElementById('refreshAuditBtn').addEventListener('click', refreshAudit);
  document.getElementById('signalVillage').addEventListener('change', (e) => {
    selectedVillageId = e.target.value;
    renderSignals();
    renderMap();
  });
  loadBlock();
  if (window.location.hash === '#audit') refreshAudit();
});

async function loadBlock() {
  try {
    block = await api('/api/v1/surveillance/block');
  } catch (err) {
    document.getElementById('alertPanel').innerHTML = `<div class="panel"><p class="empty-state">Could not load surveillance data: ${esc(err.message)}</p></div>`;
    return;
  }
  const flagged = block.villages.filter((v) => v.risk_level !== 'NORMAL').sort((a, b) => b.z_score - a.z_score);
  if (!selectedVillageId) selectedVillageId = (flagged[0] || block.villages[0]).id;
  const v0 = block.villages[0];
  document.getElementById('blockTitle').textContent = `${v0.block} Block, ${v0.district}: Outbreak Early Warning`;
  document.getElementById('signalVillage').innerHTML = block.villages
    .map((v) => `<option value="${esc(v.id)}">${esc(v.name)}</option>`).join('');
  renderStats();
  renderMap();
  renderAlerts();
  renderSignals();
}

// ================= 1. STATS =================
function renderStats() {
  const active = block.alerts.filter((a) => a.status === 'ACTIVE').length;
  const b = block.benchmark;
  document.getElementById('statVillages').textContent = block.villages.length;
  document.getElementById('statAlerts').textContent = active;
  document.getElementById('statLead').textContent = `${b.lead_time_days_earlier} days`;
  document.getElementById('statFalse').textContent = b.false_alarms_per_month_per_block;
  const count = document.getElementById('alertCount');
  count.textContent = active;
  count.classList.toggle('hidden', active === 0);
}

// ================= 2. MAP =================
function renderMap() {
  const host = document.getElementById('villageMap');
  const allCoords = block.villages.flatMap((v) => v.polygon);
  const lons = allCoords.map((c) => c[0]);
  const lats = allCoords.map((c) => c[1]);
  const minLon = Math.min(...lons); const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats); const maxLat = Math.max(...lats);
  const width = 640; const pad = 30;
  const scale = (width - pad * 2) / (maxLon - minLon);
  const height = Math.round((maxLat - minLat) * scale + pad * 2);
  const px = (c) => [pad + (c[0] - minLon) * scale, pad + (maxLat - c[1]) * scale];
  const clusterIds = new Set(block.alerts.filter((a) => a.status === 'ACTIVE').flatMap((a) => a.affected_villages));

  const shapes = block.villages.map((v) => {
    const pts = v.polygon.map((c) => px(c).map((n) => n.toFixed(1)).join(',')).join(' ');
    const [cx, cy] = px(v.center);
    const selected = v.id === selectedVillageId;
    return `
      <g class="map-village" data-id="${esc(v.id)}" tabindex="0" role="button" aria-label="${esc(v.name)}: ${esc(LEVEL_TEXT[v.risk_level])}">
        <polygon points="${pts}" fill="${RISK_FILL[v.risk_level] || RISK_FILL.NORMAL}" stroke="${selected ? '#0F172A' : '#FFFFFF'}" stroke-width="${selected ? 3 : 2}"/>
        ${clusterIds.has(v.id) ? `<polygon points="${pts}" fill="none" stroke="#DC2626" stroke-width="2" stroke-dasharray="6 4"/>` : ''}
        <text class="map-label" x="${cx}" y="${cy - 2}" text-anchor="middle">${esc(v.name)}</text>
        <text x="${cx}" y="${cy + 13}" text-anchor="middle" font-size="10" fill="#475569">z ${esc(v.z_score)}</text>
        <title>${esc(v.name)}: ${esc(LEVEL_TEXT[v.risk_level])} (z ${esc(v.z_score)})</title>
      </g>`;
  }).join('');

  host.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Village outbreak map">${shapes}</svg>`;
  host.querySelectorAll('.map-village').forEach((g) => {
    const select = () => {
      selectedVillageId = g.dataset.id;
      document.getElementById('signalVillage').value = selectedVillageId;
      renderMap();
      renderSignals();
      switchTab('signals', (tab) => { if (tab === 'signals') renderSignals(); });
    };
    g.addEventListener('click', select);
    g.addEventListener('keydown', (e) => { if (e.key === 'Enter') select(); });
  });
}

// ================= 3. ALERTS =================
function renderAlerts() {
  const host = document.getElementById('alertPanel');
  if (!block.alerts.length) {
    host.innerHTML = '<div class="panel"><div class="panel-title">Alerts</div><p class="empty-state">No outbreak alerts in this block.</p></div>';
    return;
  }
  host.innerHTML = block.alerts.map((a) => `
    <div class="panel">
      <div class="view-head" style="margin-bottom: 8px;">
        <div>
          <div class="panel-title">${esc(prettyCode(a.syndrome))}</div>
          <div class="list-meta">${esc(a.id)} · Detected ${esc(a.detected_on)}</div>
        </div>
        ${levelBadge(a.status)}
      </div>
      <div class="notice notice-red"><span>📍</span><span><strong>${a.affected_village_names.map(esc).join(', ')}</strong><br>
        ${esc(a.observed_cases)} combined signals vs ${esc(a.baseline_expected_cases)} expected · z-score ${esc(a.z_score)} · confidence ${Math.round(a.confidence * 100)}%</span></div>
      <div class="notice notice-blue" style="margin-top: 10px;"><span>⏱️</span><span>Detected on <strong>${esc(a.detected_on)}</strong>. Clinic counts alone would have crossed the threshold on <strong>${esc(a.baseline_would_detect_on || 'not yet')}</strong>.</span></div>

      <div class="decision-section">
        <h4>Rapid response checklist</h4>
        <ul class="checklist">
          ${a.recommended_interventions.map((c) => `<li><label><input type="checkbox" ${a.status === 'ACKNOWLEDGED' ? 'checked disabled' : ''}><span>${esc(c)}</span></label></li>`).join('')}
        </ul>
      </div>

      ${a.status === 'ACTIVE' ? `
        <form class="ack-form" data-id="${esc(a.id)}" style="margin-top: 14px;">
          <div class="form-group">
            <label for="ackNote-${esc(a.id)}">Response note</label>
            <textarea id="ackNote-${esc(a.id)}" class="form-textarea" placeholder="e.g. RRT dispatched, chlorination started in Ward 2."></textarea>
          </div>
          <button type="submit" class="btn btn-red btn-block">Acknowledge &amp; Dispatch Response</button>
        </form>` : `
        <div class="notice notice-green" style="margin-top: 12px;"><span>✅</span><span>Acknowledged by ${esc(a.acknowledged_by)}${a.response_note ? `: ${esc(a.response_note)}` : ''}</span></div>`}
    </div>`).join('');

  host.querySelectorAll('.ack-form').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = form.dataset.id;
      try {
        await api(`/api/v1/surveillance/alerts/${id}/ack`, {
          officer: OFFICER_ID,
          note: document.getElementById(`ackNote-${id}`).value.trim()
        });
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
  if (!v) return;
  document.getElementById('signalVillage').value = v.id;
  document.getElementById('signalTitle').innerHTML = `${esc(v.name)} ${levelBadge(v.risk_level)}`;
  document.getElementById('signalSub').textContent = `Anomaly score today: z ${v.z_score}`;
  renderLineChart(document.getElementById('signalChart'), {
    labels: block.day_labels,
    series: [
      { name: 'Clinic diarrhoea visits', color: '#3B82F6', values: v.streams.clinic_visits },
      { name: 'Pharmacy ORS sales', color: '#F97316', values: v.streams.pharmacy_ors_sales },
      { name: 'School absenteeism', color: '#8B5CF6', values: v.streams.school_absenteeism }
    ],
    yMin: 0,
    height: 260
  });

  document.getElementById('villageTable').innerHTML = block.villages
    .slice()
    .sort((a, b) => b.z_score - a.z_score)
    .map((x) => {
      const last = (arr) => arr[arr.length - 1];
      return `
        <tr>
          <td><strong>${esc(x.name)}</strong></td>
          <td>${levelBadge(x.risk_level)}</td>
          <td>${esc(x.z_score)}</td>
          <td>${esc(last(x.streams.clinic_visits))}</td>
          <td>${esc(last(x.streams.pharmacy_ors_sales))}</td>
          <td>${esc(last(x.streams.school_absenteeism))}</td>
        </tr>`;
    }).join('');
}

// ================= 5. AUDIT =================
function refreshAudit() {
  loadAuditTrail(document.getElementById('auditBody'), document.getElementById('auditStatus'));
}
