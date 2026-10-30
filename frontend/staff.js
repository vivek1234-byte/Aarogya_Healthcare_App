/**
 * AROGYASAATHI STAFF PORTALS - SHARED HELPERS
 * API access, role guard, tab navigation, toast, charts, markdown and audit rendering.
 */

const API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8080';

const STAFF_ROLES = {
  'Health Worker': { page: 'health_worker.html', avatar: '👩‍⚕️', defaultId: 'ASHA-RAMPUR-7821' },
  'Doctor': { page: 'doctor.html', avatar: '🩺', defaultId: 'DR-VERMA-PHC-402' },
  'Health Officer': { page: 'officer.html', avatar: '👮', defaultId: 'OFFICER-DIST-881' }
};

// ================= 1. ROLE GUARD =================
function requireStaffRole(role) {
  if (window.location.search.includes('dev=1')) {
    sessionStorage.setItem('arogya_staff_role', role);
    sessionStorage.setItem('arogya_staff_id', STAFF_ROLES[role].defaultId);
  }
  if (sessionStorage.getItem('arogya_staff_role') !== role) {
    window.location.replace('index.html');
    return null;
  }
  const staffId = sessionStorage.getItem('arogya_staff_id') || STAFF_ROLES[role].defaultId;
  document.querySelectorAll('[data-staff-id]').forEach((el) => { el.textContent = staffId; });
  document.querySelectorAll('[data-signout]').forEach((el) => {
    el.addEventListener('click', () => {
      sessionStorage.removeItem('arogya_staff_role');
      sessionStorage.removeItem('arogya_staff_id');
    });
  });
  return staffId;
}

// ================= 2. API =================
async function api(path, body) {
  const opts = body === undefined
    ? {}
    : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
  const res = await fetch(`${API_BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

// ================= 3. TABS =================
function setupTabs(onSwitch) {
  const pills = document.querySelectorAll('.nav-pill[data-tab]');
  pills.forEach((pill) => {
    pill.addEventListener('click', () => switchTab(pill.dataset.tab, onSwitch));
  });
  const initial = window.location.hash.replace('#', '');
  if (initial && document.getElementById(`view-${initial}`)) switchTab(initial, onSwitch);
}

function switchTab(tab, onSwitch) {
  document.querySelectorAll('.nav-pill[data-tab]').forEach((p) => p.classList.toggle('active', p.dataset.tab === tab));
  document.querySelectorAll('.staff-view').forEach((v) => v.classList.toggle('active', v.id === `view-${tab}`));
  history.replaceState(null, '', `#${tab}`);
  if (onSwitch) onSwitch(tab);
}

// ================= 4. TOAST =================
let toastTimer = null;
function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

// ================= 5. FORMATTING =================
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function prettyCode(code) {
  return String(code || '').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

const LEVEL_TEXT = {
  EMERGENCY: 'Emergency', REFER: 'Refer', TREAT_LOCALLY: 'Treat locally', HOME_CARE: 'Home care',
  CRITICAL: 'Critical', HIGH: 'High', MODERATE: 'Moderate', LOW: 'Low',
  OUTBREAK: 'Outbreak', WARNING: 'Warning', WATCH: 'Watch', NORMAL: 'Normal',
  PENDING: 'Pending', REVIEWED: 'Reviewed', ACTIVE: 'Active', ACKNOWLEDGED: 'Acknowledged'
};

function levelBadge(level) {
  return `<span class="badge lvl-${esc(level)}">${esc(LEVEL_TEXT[level] || prettyCode(level))}</span>`;
}

// Minimal markdown renderer for referral summaries (headings, lists, bold, code, quotes, rules)
function renderMarkdown(md) {
  if (!md) return '<p class="empty-state">No summary available.</p>';
  const inline = (s) => esc(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>')
    .replace(/(^|\s)_([^_]+)_(?=\s|$)/g, '$1<em>$2</em>');
  const out = [];
  let inList = false;
  md.split('\n').forEach((raw) => {
    const line = raw.trimEnd();
    const isItem = /^\s*[-*] /.test(line);
    if (!isItem && inList) { out.push('</ul>'); inList = false; }
    if (/^---+$/.test(line)) out.push('<hr>');
    else if (line.startsWith('### ')) out.push(`<h3>${inline(line.slice(4))}</h3>`);
    else if (line.startsWith('## ')) out.push(`<h2>${inline(line.slice(3))}</h2>`);
    else if (line.startsWith('# ')) out.push(`<h1>${inline(line.slice(2))}</h1>`);
    else if (line.startsWith('> ')) out.push(`<blockquote>${inline(line.slice(2))}</blockquote>`);
    else if (isItem) {
      if (!inList) { out.push('<ul>'); inList = true; }
      out.push(`<li>${inline(line.replace(/^\s*[-*] /, ''))}</li>`);
    } else if (line.trim()) out.push(`<p>${inline(line)}</p>`);
  });
  if (inList) out.push('</ul>');
  return out.join('');
}

// ================= 6. LINE CHART (SVG) =================
// series: [{ name, color, values: [number|null] }], bands: [{ from, to, color }]
function renderLineChart(container, { labels, series, height = 200, bands = [], yMin, yMax, unit = '' }) {
  const width = 640;
  const pad = { top: 12, right: 12, bottom: 26, left: 40 };
  const all = series.flatMap((s) => s.values).filter((v) => v !== null && v !== undefined);
  if (!all.length) { container.innerHTML = '<p class="empty-state">No readings yet.</p>'; return; }
  let lo = yMin ?? Math.min(...all);
  let hi = yMax ?? Math.max(...all);
  if (yMin === undefined) lo = Math.floor((lo - (hi - lo) * 0.15 - 1) / 5) * 5;
  if (yMax === undefined) hi = Math.ceil((hi + (hi - lo) * 0.15 + 1) / 5) * 5;
  const iw = width - pad.left - pad.right;
  const ih = height - pad.top - pad.bottom;
  const x = (i) => pad.left + (labels.length === 1 ? iw / 2 : (i * iw) / (labels.length - 1));
  const y = (v) => pad.top + ih - ((v - lo) / (hi - lo || 1)) * ih;

  const parts = [];
  bands.forEach((b) => {
    const top = y(Math.min(b.to, hi));
    const bottom = y(Math.max(b.from, lo));
    if (bottom > top) parts.push(`<rect x="${pad.left}" y="${top}" width="${iw}" height="${bottom - top}" fill="${b.color}"/>`);
  });
  for (let t = 0; t <= 4; t += 1) {
    const v = lo + ((hi - lo) * t) / 4;
    parts.push(`<line x1="${pad.left}" x2="${width - pad.right}" y1="${y(v)}" y2="${y(v)}" stroke="#F1F5F9"/>`);
    parts.push(`<text x="${pad.left - 8}" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="#94A3B8">${Math.round(v)}</text>`);
  }
  const step = Math.max(1, Math.ceil(labels.length / 7));
  labels.forEach((l, i) => {
    if (i % step === 0 || i === labels.length - 1) {
      parts.push(`<text x="${x(i)}" y="${height - 6}" text-anchor="middle" font-size="11" fill="#94A3B8">${esc(l)}</text>`);
    }
  });
  series.forEach((s) => {
    const pts = s.values.map((v, i) => (v === null || v === undefined ? null : [x(i), y(v)])).filter(Boolean);
    if (!pts.length) return;
    parts.push(`<polyline fill="none" stroke="${s.color}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" points="${pts.map((p) => p.join(',')).join(' ')}"/>`);
    s.values.forEach((v, i) => {
      if (v === null || v === undefined) return;
      parts.push(`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="#FFFFFF" stroke="${s.color}" stroke-width="2"><title>${esc(labels[i])}: ${esc(v)}${esc(unit)} (${esc(s.name)})</title></circle>`);
    });
  });
  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(series.map((s) => s.name).join(', '))} trend">${parts.join('')}</svg>
    <div class="chart-legend">${series.map((s) => `<span><span class="legend-dot" style="background:${s.color}"></span>${esc(s.name)}</span>`).join('')}</div>`;
}

function renderDoseStrip(container, doses, days) {
  const missed = doses.filter((d) => d !== 'TAKEN').length;
  container.innerHTML = `
    <div class="dose-strip">${doses.map((d, i) => `<div class="dose ${d === 'TAKEN' ? '' : 'missed'}" title="${esc(days[i])}: ${esc(prettyCode(d))}"></div>`).join('')}</div>
    <div class="dose-label"><span>${esc(days[0] || '')}</span><span>${missed} missed of ${doses.length} doses</span><span>${esc(days[days.length - 1] || '')}</span></div>`;
}

// ================= 7. AUDIT TRAIL =================
async function loadAuditTrail(tableBody, statusEl, roleFilter) {
  try {
    const data = await api('/api/v1/audit');
    const entries = roleFilter ? data.entries.filter((e) => roleFilter.includes(e.role)) : data.entries;
    statusEl.className = `notice ${data.chain_valid ? 'notice-green' : 'notice-red'}`;
    statusEl.innerHTML = data.chain_valid
      ? `<span>🔒</span><span><strong>Hash chain verified.</strong> ${data.entries.length} entries; each entry includes the SHA-256 hash of the previous one, so any edit breaks the chain.</span>`
      : `<span>⚠️</span><span><strong>Tamper detected</strong> at entry #${esc(data.broken_at_seq)}. Report to the district data officer.</span>`;
    tableBody.innerHTML = entries.length ? entries.map((e) => `
      <tr>
        <td>#${e.seq}</td>
        <td>${esc(e.ts)}</td>
        <td><strong>${esc(prettyCode(e.event))}</strong></td>
        <td>${esc(e.actor)}<div class="list-meta">${esc(prettyCode(e.role))}</div></td>
        <td class="audit-details">${esc(Object.entries(e.details).map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' · '))}</td>
        <td class="hash" title="${esc(e.hash)}">${esc(e.hash.slice(0, 12))}…</td>
      </tr>`).join('') : '<tr><td colspan="6" class="empty-state">No audit entries yet.</td></tr>';
  } catch (err) {
    statusEl.className = 'notice notice-red';
    statusEl.textContent = `Could not load audit trail: ${err.message}`;
  }
}
