/**
 * AROGYASAATHI - SHARED APP HELPERS (patient, ASHA, doctor and officer pages)
 * Session + API, role guard, tabs, toast, five-language voice input and read-aloud,
 * charts, markdown and audit rendering.
 */

const API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8080';

const ROLE_PAGES = {
  PATIENT: 'patient_dashboard.html',
  HEALTH_WORKER: 'health_worker.html',
  DOCTOR: 'doctor.html',
  HEALTH_OFFICER: 'officer.html'
};

// ================= 1. SESSION & API =================
function storedToken() {
  try { return localStorage.getItem('arogya_token'); } catch (e) { return null; }
}

function storedUser() {
  try { return JSON.parse(localStorage.getItem('arogya_user') || 'null'); } catch (e) { return null; }
}

function clearSession() {
  try {
    localStorage.removeItem('arogya_token');
    localStorage.removeItem('arogya_user');
  } catch (e) { /* ignore */ }
}

async function signOut() {
  try { await api('/api/v1/auth/logout', {}); } catch (e) { /* already signed out */ }
  clearSession();
  window.location.replace('index.html');
}

async function api(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = storedToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const opts = body === undefined ? { headers } : { method: 'POST', headers, body: JSON.stringify(body) };
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, opts);
  } catch (e) {
    throw new Error('No connection to the server. Check internet and try again.');
  }
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && !path.startsWith('/api/v1/auth/logout')) {
    clearSession();
    window.location.replace('index.html');
  }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

/** Ensures the logged-in user has `role`; otherwise sends them to login or their own page. */
function requireRole(role) {
  const user = storedUser();
  if (!storedToken() || !user) {
    window.location.replace('index.html');
    return null;
  }
  if (user.role !== role) {
    window.location.replace(ROLE_PAGES[user.role] || 'index.html');
    return null;
  }
  document.querySelectorAll('[data-user-name]').forEach((el) => { el.textContent = user.name; });
  document.querySelectorAll('[data-user-id]').forEach((el) => { el.textContent = user.id; });
  document.querySelectorAll('[data-signout]').forEach((el) => {
    el.addEventListener('click', (e) => { e.preventDefault(); signOut(); });
  });
  // Refresh the profile in the background (village / facility may have changed)
  api('/api/v1/auth/me').then((fresh) => {
    try { localStorage.setItem('arogya_user', JSON.stringify(fresh)); } catch (e) { /* ignore */ }
  }).catch(() => {});
  return user;
}

// ================= 2. TABS =================
function setupTabs(onSwitch) {
  document.querySelectorAll('.nav-pill[data-tab]').forEach((pill) => {
    pill.addEventListener('click', () => switchTab(pill.dataset.tab, onSwitch));
  });
  const initial = window.location.hash.replace('#', '');
  if (initial && document.getElementById(`view-${initial}`)) switchTab(initial, onSwitch);
}

function switchTab(tab, onSwitch) {
  document.querySelectorAll('.nav-pill[data-tab]').forEach((p) => p.classList.toggle('active', p.dataset.tab === tab));
  document.querySelectorAll('.staff-view').forEach((v) => v.classList.toggle('active', v.id === `view-${tab}`));
  history.replaceState(null, '', `#${tab}`);
  window.scrollTo({ top: 0 });
  if (onSwitch) onSwitch(tab);
}

// ================= 3. TOAST & FORMATTING =================
let toastTimer = null;
function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3200);
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function prettyCode(code) {
  return String(code || '').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDateTime(ts) {
  if (!ts) return '';
  const d = new Date(ts.replace(' ', 'T'));
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
}

const LEVEL_TEXT = {
  EMERGENCY: 'Emergency', REFER: 'Refer', TREAT_LOCALLY: 'Treat locally', HOME_CARE: 'Home care',
  CRITICAL: 'Critical', HIGH: 'High', MODERATE: 'Moderate', LOW: 'Low', NO_DATA: 'No readings',
  OUTBREAK: 'Outbreak', WARNING: 'Warning', WATCH: 'Watch', NORMAL: 'Normal', NO_BASELINE: 'Collecting data',
  PENDING: 'Pending', REVIEWED: 'Reviewed', ACTIVE: 'Active', ACKNOWLEDGED: 'Acknowledged',
  SAME_DAY: 'Same day', WITHIN_WEEK: 'Within a week', REFERRED: 'Referred'
};

function levelBadge(level) {
  return `<span class="badge lvl-${esc(level)}">${esc(LEVEL_TEXT[level] || prettyCode(level))}</span>`;
}

function telLink(number, label) {
  const digits = String(number || '').replace(/[^\d+]/g, '');
  return digits ? `<a class="btn btn-ghost btn-call" href="tel:${esc(digits)}">📞 ${esc(label || number)}</a>` : '';
}

function mapsLink(lat, lon, name) {
  if (lat == null || lon == null) {
    return name ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(name)}` : '';
  }
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`;
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

// ================= 4. LANGUAGES, VOICE INPUT & READ-ALOUD =================
const LANGS = [
  { code: 'hi', label: 'हिंदी', name: 'Hindi', speech: 'hi-IN' },
  { code: 'en', label: 'English', name: 'English', speech: 'en-IN' },
  { code: 'bn', label: 'বাংলা', name: 'Bengali', speech: 'bn-IN' },
  { code: 'mr', label: 'मराठी', name: 'Marathi', speech: 'mr-IN' },
  { code: 'te', label: 'తెలుగు', name: 'Telugu', speech: 'te-IN' }
];

function langInfo(code) {
  return LANGS.find((l) => l.code === code) || LANGS[0];
}

/** Renders language chips into `container`; calls onChange(code) when one is tapped. */
function renderLanguageChips(container, current, onChange) {
  container.innerHTML = LANGS.map((l) => `
    <button type="button" class="lang-chip ${l.code === current ? 'active' : ''}" data-lang="${l.code}" aria-pressed="${l.code === current}">${esc(l.label)}</button>`).join('');
  container.querySelectorAll('.lang-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      container.querySelectorAll('.lang-chip').forEach((c) => {
        c.classList.toggle('active', c === chip);
        c.setAttribute('aria-pressed', String(c === chip));
      });
      onChange(chip.dataset.lang);
    });
  });
}

/** Picks the language from the script of typed text; Latin text keeps the selected language. */
function detectLanguage(text, selected) {
  if (/[ঀ-৿]/.test(text)) return 'bn';
  if (/[ఀ-౿]/.test(text)) return 'te';
  if (/[ऀ-ॿ]/.test(text)) return selected === 'mr' ? 'mr' : 'hi';
  return selected;
}

const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition;

const SPEECH_ERRORS = {
  'not-allowed': 'Microphone is blocked. Allow microphone for this app in phone Settings → Apps → Chrome → Permissions, then try again.',
  'service-not-allowed': 'Microphone is blocked for this app. Allow it in phone settings.',
  'no-speech': 'Did not hear anything. Tap the mic and speak again.',
  'audio-capture': 'No microphone found on this device.',
  network: 'Voice typing needs internet. Please type instead.',
  'language-not-supported': 'Voice typing for this language is not installed on this phone. Please type instead.'
};

/**
 * Voice input into an editable text field.
 * Words appear in `input` while speaking; the user can correct them before sending.
 * getLang() returns a language code; onFinal(text) is optional (e.g. to auto-send).
 */
function attachDictation(button, input, getLang, onFinal) {
  if (!SpeechRecognitionApi) {
    button.addEventListener('click', () => showToast('Voice typing is not available in this browser. Please type.'));
    return;
  }
  let recognition = null;
  let base = '';
  button.addEventListener('click', () => {
    if (recognition) { recognition.stop(); return; }
    recognition = new SpeechRecognitionApi();
    recognition.lang = langInfo(getLang()).speech;
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;
    base = input.value.trim() ? `${input.value.trim()} ` : '';
    let finalText = '';
    button.classList.add('recording');
    button.setAttribute('aria-label', 'Stop listening');
    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const piece = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += piece;
        else interim += piece;
      }
      input.value = (base + finalText + interim).trim();
    };
    recognition.onerror = (event) => {
      if (event.error !== 'aborted') showToast(SPEECH_ERRORS[event.error] || `Voice error: ${event.error}. Please type instead.`);
    };
    recognition.onend = () => {
      button.classList.remove('recording');
      button.setAttribute('aria-label', 'Speak');
      recognition = null;
      input.focus();
      if (finalText.trim() && onFinal) onFinal(input.value.trim());
    };
    try {
      recognition.start();
    } catch (e) {
      button.classList.remove('recording');
      recognition = null;
    }
  });
}

let voicesReady = null;
function loadVoices() {
  if (!('speechSynthesis' in window)) return Promise.resolve([]);
  if (voicesReady) return voicesReady;
  voicesReady = new Promise((resolve) => {
    const voices = speechSynthesis.getVoices();
    if (voices.length) { resolve(voices); return; }
    speechSynthesis.onvoiceschanged = () => resolve(speechSynthesis.getVoices());
    setTimeout(() => resolve(speechSynthesis.getVoices()), 1500);
  });
  return voicesReady;
}

/** Reads `text` aloud in `lang` if the phone has a voice for it. Returns false otherwise. */
async function speak(text, lang) {
  if (!('speechSynthesis' in window)) return false;
  const tag = langInfo(lang).speech;
  const voices = await loadVoices();
  const voice = voices.find((v) => v.lang === tag) || voices.find((v) => v.lang && v.lang.startsWith(lang));
  if (!voice && lang !== 'en' && lang !== 'hi') return false;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = tag;
  if (voice) utterance.voice = voice;
  utterance.rate = 0.95;
  speechSynthesis.speak(utterance);
  return true;
}

// ================= 5. LINE CHART (SVG) =================
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
  if (!doses.length) { container.innerHTML = '<p class="empty-state">No medicine check-ins yet.</p>'; return; }
  const missed = doses.filter((d) => d !== 'TAKEN').length;
  container.innerHTML = `
    <div class="dose-strip">${doses.map((d, i) => `<div class="dose ${d === 'TAKEN' ? '' : 'missed'}" title="${esc(days[i])}: ${esc(prettyCode(d))}"></div>`).join('')}</div>
    <div class="dose-label"><span>${esc(days[0] || '')}</span><span>${missed} missed of ${doses.length}</span><span>${esc(days[days.length - 1] || '')}</span></div>`;
}

function renderTrendCharts(trend, bpEl, sugarEl) {
  renderLineChart(bpEl, {
    labels: trend.days,
    series: [
      { name: 'Systolic (upper)', color: '#EF4444', values: trend.systolic },
      { name: 'Diastolic (lower)', color: '#3B82F6', values: trend.diastolic }
    ],
    bands: [{ from: 140, to: 400, color: 'rgba(239, 68, 68, 0.06)' }],
    unit: ' mmHg'
  });
  renderLineChart(sugarEl, {
    labels: trend.days,
    series: [{ name: 'Sugar', color: '#10B981', values: trend.glucose }],
    bands: [{ from: 180, to: 700, color: 'rgba(245, 158, 11, 0.08)' }],
    unit: ' mg/dL'
  });
}

// ================= 6. AUDIT TRAIL =================
async function loadAuditTrail(tableBody, statusEl) {
  try {
    const data = await api('/api/v1/audit');
    statusEl.className = `notice ${data.chain_valid ? 'notice-green' : 'notice-red'}`;
    statusEl.innerHTML = data.chain_valid
      ? `<span>🔒</span><span><strong>Hash chain verified.</strong> Each entry includes the SHA-256 hash of the previous one, so any edit breaks the chain. Showing the latest ${data.entries.length}.</span>`
      : `<span>⚠️</span><span><strong>Tamper detected</strong> at entry #${esc(data.broken_at_seq)}. Report to the district data officer.</span>`;
    tableBody.innerHTML = data.entries.length ? data.entries.map((e) => `
      <tr>
        <td>#${e.seq}</td>
        <td>${esc(e.ts)}</td>
        <td><strong>${esc(prettyCode(e.event))}</strong></td>
        <td>${esc(e.actor)}<div class="list-meta">${esc(prettyCode(e.role))}</div></td>
        <td class="audit-details">${esc(Object.entries(e.details || {}).map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' · '))}</td>
        <td class="hash" title="${esc(e.hash)}">${esc(e.hash.slice(0, 12))}…</td>
      </tr>`).join('') : '<tr><td colspan="6" class="empty-state">No audit entries yet.</td></tr>';
  } catch (err) {
    statusEl.className = 'notice notice-red';
    statusEl.textContent = `Could not load audit trail: ${err.message}`;
  }
}

// Offline app shell (network first; see service-worker.js)
if ('serviceWorker' in navigator && window.location.protocol !== 'file:') {
  window.addEventListener('load', () => navigator.serviceWorker.register('service-worker.js').catch(() => {}));
}
