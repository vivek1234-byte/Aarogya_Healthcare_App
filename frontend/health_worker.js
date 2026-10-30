/**
 * AROGYASAATHI - HEALTH WORKER (ASHA / ANM) CONTROLLER
 * Chronic care visit queue with voice check-ins, voice triage with guided
 * questions and safety-gate decisions, and patient registration with consent.
 */

const WORKER_ID = requireStaffRole('Health Worker');

let roster = [];
let villages = [];
let selectedPatientId = null;
let triageSession = null;
let triageLang = 'hi';
let registeredPatients = [];

// ================= 1. INIT =================
document.addEventListener('DOMContentLoaded', async () => {
  if (!WORKER_ID) return;
  setupTabs();
  setupSegmented('triageLang', 'lang', (v) => { triageLang = v; });
  setupSegmented('regChannel', 'channel');
  setupTriage();
  setupRegistration();
  await Promise.all([loadVillages(), loadRoster()]);
});

function setupSegmented(id, key, onChange) {
  const group = document.getElementById(id);
  group.querySelectorAll('button').forEach((btn) => {
    btn.addEventListener('click', () => {
      group.querySelectorAll('button').forEach((b) => b.classList.toggle('active', b === btn));
      if (onChange) onChange(btn.dataset[key]);
    });
  });
}

function segmentedValue(id, key) {
  return document.querySelector(`#${id} button.active`).dataset[key];
}

async function loadVillages() {
  try {
    villages = await api('/api/v1/villages');
  } catch (err) {
    villages = [{ id: 'VILL-UP-RAMPUR-01', name: 'Rampur Central' }];
  }
  const options = villages.map((v) => `<option value="${esc(v.id)}">${esc(v.name)}</option>`).join('');
  document.getElementById('triageVillage').innerHTML = options;
  document.getElementById('regVillage').innerHTML = options;
}

// ================= 2. CHRONIC CARE VISIT QUEUE =================
async function loadRoster() {
  try {
    roster = await api('/api/v1/worker/roster');
  } catch (err) {
    document.getElementById('rosterList').innerHTML = `<p class="empty-state">Could not load patients: ${esc(err.message)}</p>`;
    return;
  }
  renderRosterStats();
  renderRosterList();
  renderTriagePatientOptions();
  if (!selectedPatientId && roster.length) selectedPatientId = roster[0].id;
  renderPatientDetail();
}

function renderRosterStats() {
  const priority = roster.filter((p) => ['HIGH', 'CRITICAL'].includes(p.risk.risk_level)).length;
  const missed = roster.reduce((n, p) => n + p.trend.doses.filter((d) => d !== 'TAKEN').length, 0);
  const nextVisit = Math.min(...roster.map((p) => p.days_to_visit));
  document.getElementById('statPatients').textContent = roster.length;
  document.getElementById('statPriority').textContent = priority;
  document.getElementById('statMissed').textContent = missed;
  document.getElementById('statVisit').textContent = Number.isFinite(nextVisit) ? `${nextVisit} days` : '–';
  const count = document.getElementById('visitsCount');
  count.textContent = priority;
  count.classList.toggle('hidden', priority === 0);
}

function renderRosterList() {
  const list = document.getElementById('rosterList');
  list.innerHTML = roster.map((p) => `
    <button type="button" class="list-item ${p.id === selectedPatientId ? 'selected' : ''}" data-id="${esc(p.id)}">
      <div class="list-main">
        <div class="list-title">${esc(p.name)}</div>
        <div class="list-meta">${esc(p.age)} yrs · ${esc(p.village_name)} · ${esc(p.condition)}</div>
        <div class="list-meta">BP ${esc(p.latest.bp)} · Sugar ${esc(p.latest.glucose)} mg/dL</div>
      </div>
      ${levelBadge(p.risk.risk_level)}
    </button>`).join('');
  list.querySelectorAll('.list-item').forEach((item) => {
    item.addEventListener('click', () => {
      selectedPatientId = item.dataset.id;
      renderRosterList();
      renderPatientDetail();
    });
  });
}

function renderPatientDetail() {
  const p = roster.find((r) => r.id === selectedPatientId);
  const host = document.getElementById('patientDetail');
  if (!p) return;
  const r = p.risk;
  host.innerHTML = `
    <div class="panel">
      <div class="view-head" style="margin-bottom: 12px;">
        <div>
          <div class="panel-title">${esc(p.name)} ${levelBadge(r.risk_level)}</div>
          <div class="list-meta">${esc(p.pseudonym)} · ${esc(p.age)} yrs / ${esc(p.gender)} · ${esc(p.village_name)} · Next PHC visit ${esc(p.next_visit)}</div>
        </div>
      </div>
      ${r.is_deteriorating ? `
        <div class="notice notice-red" style="margin-bottom: 14px;">
          <span>⚠️</span><span><strong>Deterioration flagged ${esc(p.days_to_visit)} days before the next visit.</strong> ${esc(r.recommended_action)}</span>
        </div>` : `
        <div class="notice notice-green" style="margin-bottom: 14px;"><span>✅</span><span>${esc(r.recommended_action)}</span></div>`}
      <div class="list-flags" style="margin-bottom: 14px;">
        ${r.flags.length ? r.flags.map((f) => `<span class="chip chip-red">${esc(prettyCode(f))}</span>`).join('') : '<span class="chip">No flags</span>'}
        <span class="chip">BP slope ${esc(r.systolic_slope_per_week)} mmHg/week</span>
        <span class="chip">Adherence ${esc(r.adherence_rate_pct)}%</span>
      </div>

      <div class="grid-2">
        <div>
          <div class="panel-title">Blood pressure</div>
          <div class="chart-box" id="bpChart"></div>
        </div>
        <div>
          <div class="panel-title">Fasting sugar</div>
          <div class="chart-box" id="sugarChart"></div>
        </div>
      </div>
      <div style="margin-top: 14px;">
        <div class="panel-title">Medicine doses</div>
        <div id="doseStrip"></div>
      </div>
    </div>

    <form class="panel" id="checkinForm">
      <div class="panel-title">Record today's check-in</div>
      <div class="panel-sub">Let the patient say their reading, e.g. "आज मेरा बीपी 150 बटा 95 है, दवाई ले ली". Numbers typed below take priority over the voice reading.</div>
      <div class="speech-input-row" style="margin-top: 0;">
        <button type="button" class="btn btn-ghost" id="checkinMicBtn">🎙️ Speak</button>
        <input id="checkinTranscript" class="form-input" placeholder="Spoken check-in appears here" autocomplete="off">
      </div>
      <div class="form-row" style="margin-top: 12px;">
        <div class="form-group"><label for="ciSys">Systolic BP</label><input id="ciSys" class="form-input" type="number" placeholder="mmHg"></div>
        <div class="form-group"><label for="ciDia">Diastolic BP</label><input id="ciDia" class="form-input" type="number" placeholder="mmHg"></div>
        <div class="form-group"><label for="ciSugar">Fasting sugar</label><input id="ciSugar" class="form-input" type="number" placeholder="mg/dL"></div>
      </div>
      <div class="form-group">
        <label>Today's medicine</label>
        <div class="segmented" id="ciDose">
          <button type="button" data-dose="">From voice</button>
          <button type="button" class="active" data-dose="TAKEN">Taken</button>
          <button type="button" data-dose="MISSED">Missed</button>
        </div>
      </div>
      <button type="submit" class="btn btn-primary btn-block">Save Check-in</button>
    </form>`;

  const t = p.trend;
  renderLineChart(document.getElementById('bpChart'), {
    labels: t.days,
    series: [
      { name: 'Systolic', color: '#EF4444', values: t.systolic },
      { name: 'Diastolic', color: '#3B82F6', values: t.diastolic }
    ],
    bands: [{ from: 140, to: 400, color: 'rgba(239, 68, 68, 0.06)' }],
    unit: ' mmHg'
  });
  renderLineChart(document.getElementById('sugarChart'), {
    labels: t.days,
    series: [{ name: 'Fasting glucose', color: '#10B981', values: t.glucose }],
    bands: [{ from: 126, to: 600, color: 'rgba(245, 158, 11, 0.08)' }],
    unit: ' mg/dL'
  });
  renderDoseStrip(document.getElementById('doseStrip'), t.doses, t.days);

  setupSegmented('ciDose', 'dose');
  const transcriptInput = document.getElementById('checkinTranscript');
  attachSpeech(document.getElementById('checkinMicBtn'), () => (triageLang === 'en' ? 'en-IN' : 'hi-IN'), (text) => {
    transcriptInput.value = text;
    document.querySelector('#ciDose button[data-dose=""]').click();
  });
  document.getElementById('checkinForm').addEventListener('submit', (e) => {
    e.preventDefault();
    submitCheckin(p.id);
  });
}

async function submitCheckin(patientId) {
  const num = (id) => {
    const v = document.getElementById(id).value;
    return v === '' ? null : Number(v);
  };
  const transcript = document.getElementById('checkinTranscript').value.trim();
  const body = {
    worker_id: WORKER_ID,
    transcript,
    language: /[ऀ-ॿ]/.test(transcript) ? 'hi' : 'en',
    systolic: num('ciSys'),
    diastolic: num('ciDia'),
    glucose: num('ciSugar'),
    dose_status: segmentedValue('ciDose', 'dose') || null
  };
  if (!transcript && body.systolic === null && body.glucose === null) {
    showToast('Speak or enter at least one reading');
    return;
  }
  try {
    const res = await api(`/api/v1/worker/roster/${patientId}/checkin`, body);
    showToast(res.escalation_id
      ? `Saved. Risk ${res.patient.risk.risk_level}: sent to doctor (${res.escalation_id})`
      : `Saved. Risk level: ${res.patient.risk.risk_level}`);
    await loadRoster();
  } catch (err) {
    showToast(`Could not save: ${err.message}`);
  }
}

// ================= 3. SPEECH TO TEXT =================
const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition;

function attachSpeech(button, getLang, onText) {
  if (!SpeechRecognitionApi) {
    button.title = 'Voice input needs Chrome over HTTPS or localhost. Type instead.';
    button.addEventListener('click', () => showToast('Voice input is not available in this browser. Please type.'));
    return null;
  }
  let recognition = null;
  button.addEventListener('click', () => {
    if (recognition) { recognition.stop(); return; }
    recognition = new SpeechRecognitionApi();
    recognition.lang = getLang();
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    button.classList.add('recording');
    recognition.onresult = (event) => onText(event.results[0][0].transcript);
    recognition.onerror = (event) => showToast(`Voice error: ${event.error}. Please type instead.`);
    recognition.onend = () => { button.classList.remove('recording'); recognition = null; };
    recognition.start();
  });
  return true;
}

// ================= 4. VOICE TRIAGE =================
function renderTriagePatientOptions() {
  const select = document.getElementById('triagePatientSelect');
  const current = select.value;
  const fromRoster = roster.map((p) => `<option value="roster:${esc(p.id)}">${esc(p.name)} · ${esc(p.village_name)}</option>`);
  const fromRegistered = registeredPatients.map((p, i) => `<option value="reg:${i}">${esc(p.name)} · ${esc(p.pseudonym)}</option>`);
  select.innerHTML = `<option value="">New / walk-in patient</option>${fromRegistered.join('')}${fromRoster.join('')}`;
  select.value = current;
}

function setupTriage() {
  const select = document.getElementById('triagePatientSelect');
  select.addEventListener('change', () => {
    const [kind, key] = select.value.split(':');
    const p = kind === 'roster' ? roster.find((r) => r.id === key) : kind === 'reg' ? registeredPatients[Number(key)] : null;
    document.getElementById('triageName').value = p ? p.name : '';
    document.getElementById('triageAge').value = p ? p.age : '';
    document.getElementById('triageGender').value = p ? p.gender : 'F';
    if (p) document.getElementById('triageVillage').value = p.village_id;
    document.getElementById('triageConsent').checked = Boolean(p && p.consent && p.consent.data_use);
  });

  document.getElementById('startTriageBtn').addEventListener('click', startTriage);

  attachSpeech(document.getElementById('micBtn'), () => (triageLang === 'en' ? 'en-IN' : 'hi-IN'), (text) => {
    sendTriageText(text);
  });

  document.getElementById('triageInputForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const input = document.getElementById('triageTextInput');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    sendTriageText(text);
  });
}

async function startTriage() {
  const consent = document.getElementById('triageConsent').checked;
  if (!consent) {
    showToast('Take the patient\'s voice consent before starting');
    return;
  }
  const age = document.getElementById('triageAge').value;
  if (age === '') {
    showToast('Enter the patient\'s age');
    return;
  }
  const [kind, key] = document.getElementById('triagePatientSelect').value.split(':');
  const known = kind === 'roster' ? roster.find((r) => r.id === key) : kind === 'reg' ? registeredPatients[Number(key)] : null;
  const vitals = {};
  const temp = document.getElementById('vitalTemp').value;
  const spo2 = document.getElementById('vitalSpo2').value;
  const sys = document.getElementById('vitalSys').value;
  if (temp) vitals.temperature_f = Number(temp);
  if (spo2) vitals.spo2 = Number(spo2);
  if (sys) vitals.systolic_bp = Number(sys);

  try {
    triageSession = await api('/api/v1/triage/sessions', {
      worker_id: WORKER_ID,
      name: document.getElementById('triageName').value.trim() || 'Walk-in patient',
      age: Number(age),
      gender: document.getElementById('triageGender').value,
      village_id: document.getElementById('triageVillage').value,
      pseudonym: known ? known.pseudonym : undefined,
      language: triageLang,
      consent: { data_use: true },
      vitals
    });
  } catch (err) {
    showToast(err.message);
    return;
  }

  document.getElementById('conversation').innerHTML = '';
  document.getElementById('decisionPanel').classList.add('hidden');
  const badge = document.getElementById('triageSessionBadge');
  badge.textContent = triageSession.session_id;
  badge.classList.remove('hidden');
  document.getElementById('triageConvSub').textContent = `${triageSession.patient.pseudonym} · ${triageSession.patient.age} yrs · ${triageSession.patient.village_name}`;
  setTriageInputEnabled(true);
  document.getElementById('micHint').textContent = triageLang === 'hi'
    ? 'माइक दबाएं और मरीज़ की तकलीफ़ बोलें'
    : 'Tap the mic and describe the main complaint';
  document.getElementById('triageTextInput').focus();
  showToast('Triage started');
}

function setTriageInputEnabled(enabled) {
  ['micBtn', 'triageTextInput', 'triageSendBtn'].forEach((id) => { document.getElementById(id).disabled = !enabled; });
}

async function sendTriageText(text) {
  if (!triageSession || triageSession.is_final) return;
  appendTurn('turn-input', 'Patient / health worker', text);
  setTriageInputEnabled(false);
  try {
    triageSession = await api(`/api/v1/triage/sessions/${triageSession.session_id}/turn`, { worker_id: WORKER_ID, text });
  } catch (err) {
    showToast(err.message);
    setTriageInputEnabled(true);
    return;
  }
  if (triageSession.is_final) {
    renderDecision(triageSession);
  } else {
    appendTurn('turn-question', 'Ask next', triageSession.next_question,
      triageSession.language === 'hi' ? triageSession.next_question_en : null, triageSession.checklist);
    setTriageInputEnabled(true);
  }
}

function appendTurn(cls, label, text, subText, checks) {
  const conv = document.getElementById('conversation');
  conv.insertAdjacentHTML('beforeend', `
    <div class="turn ${cls}">
      <div class="turn-label">${esc(label)}</div>
      <div>${esc(text)}</div>
      ${subText ? `<div class="q-en">${esc(subText)}</div>` : ''}
      ${checks && checks.length ? `<div class="q-en">Also check: ${checks.map(esc).join(' · ')}</div>` : ''}
    </div>`);
}

function renderDecision(s) {
  const panel = document.getElementById('decisionPanel');
  panel.classList.remove('hidden');
  panel.innerHTML = `
    <div class="panel-title">3. Decision</div>
    <div class="decision-card d-${esc(s.triage_level)}" style="margin-top: 10px;">
      <div class="decision-level">${esc(s.triage_label)}</div>
      <div class="decision-rationale">${esc(s.decision_rationale)}</div>

      ${s.is_red_flag_overridden ? `
        <div class="notice notice-red" style="margin-top: 12px;"><span>🛑</span><span><strong>Red-flag rule fired.</strong> The fixed safety rule overrode the model. Danger signs: ${s.danger_signs.map((d) => esc(prettyCode(d))).join(', ')}</span></div>` : ''}
      ${s.uncertain ? `
        <div class="notice notice-amber" style="margin-top: 12px;"><span>❓</span><span><strong>Uncertain.</strong> ${esc(s.uncertainty_reason)}</span></div>` : ''}

      <div class="decision-section">
        <h4>Step-by-step checklist</h4>
        <ul class="checklist">
          ${s.checklist.map((c) => `<li><label><input type="checkbox"><span>${esc(c)}</span></label></li>`).join('')}
        </ul>
      </div>

      <div class="decision-section">
        <h4>Protocol</h4>
        <div class="list-flags">${s.protocol_citations.map((c) => `<span class="chip">${esc(c)}</span>`).join('') || '<span class="chip">None</span>'}</div>
      </div>

      <div class="decision-section">
        <h4>Symptoms recorded</h4>
        <div class="list-flags">${s.symptoms.map((x) => `<span class="chip">${esc(prettyCode(x))}</span>`).join('') || '<span class="chip">None recognised</span>'}</div>
      </div>
    </div>

    <div class="notice notice-blue" style="margin-top: 14px;"><span>ℹ️</span><span>ArogyaSaathi does not diagnose or prescribe. Medicines are decided only by the doctor.</span></div>

    ${s.escalation_id ? `
      <div class="notice notice-green" style="margin-top: 10px;"><span>📤</span><span>Referral summary sent to the PHC doctor's queue (${esc(s.escalation_id)}).</span></div>` : ''}

    <div class="btn-row" style="margin-top: 14px;">
      ${s.triage_level === 'EMERGENCY' ? '<a href="tel:108" class="btn sos-btn">🚑 Call 108 now</a>' : ''}
      ${s.summary_markdown ? '<button type="button" class="btn btn-ghost" id="toggleSummaryBtn">View doctor summary</button>' : ''}
      <button type="button" class="btn btn-primary" id="newTriageBtn">New triage</button>
    </div>
    ${s.summary_markdown ? `<div class="summary-doc hidden" id="triageSummaryDoc" style="margin-top: 14px;">${renderMarkdown(s.summary_markdown)}</div>` : ''}`;

  const toggle = document.getElementById('toggleSummaryBtn');
  if (toggle) {
    toggle.addEventListener('click', () => document.getElementById('triageSummaryDoc').classList.toggle('hidden'));
  }
  document.getElementById('newTriageBtn').addEventListener('click', () => {
    triageSession = null;
    panel.classList.add('hidden');
    document.getElementById('conversation').innerHTML = '';
    document.getElementById('triageSessionBadge').classList.add('hidden');
    document.getElementById('triageConvSub').textContent = 'Start triage to begin.';
    setTriageInputEnabled(false);
    document.getElementById('triageSetupPanel').scrollIntoView({ behavior: 'smooth' });
  });
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ================= 5. REGISTRATION & CONSENT =================
function setupRegistration() {
  document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const consent = {
      data_use: document.getElementById('consentData').checked,
      sharing: document.getElementById('consentShare').checked,
      deletion_rights_explained: document.getElementById('consentDelete').checked
    };
    if (!consent.data_use) {
      showToast('Consent for data use is required to register');
      return;
    }
    const name = document.getElementById('regName').value.trim();
    const age = Number(document.getElementById('regAge').value);
    const gender = document.getElementById('regGender').value;
    try {
      const res = await api('/api/v1/worker/register', {
        worker_id: WORKER_ID,
        name,
        phone: document.getElementById('regPhone').value.trim(),
        village_id: document.getElementById('regVillage').value,
        channel: segmentedValue('regChannel', 'channel'),
        consent
      });
      registeredPatients.unshift({ name, age, gender, village_id: res.village_id, village_name: res.village_name, pseudonym: res.pseudonym, consent: res.consent });
      e.target.reset();
      renderRegistered();
      renderTriagePatientOptions();
      showToast(`Registered as ${res.pseudonym}`);
    } catch (err) {
      showToast(err.message);
    }
  });
}

function renderRegistered() {
  const list = document.getElementById('registeredList');
  list.innerHTML = registeredPatients.map((p, i) => `
    <div class="list-item">
      <div class="list-main">
        <div class="list-title">${esc(p.pseudonym)}</div>
        <div class="list-meta">${esc(p.age)} yrs / ${esc(p.gender)} · ${esc(p.village_name)}</div>
        <div class="list-flags">
          <span class="chip">Data use ✓</span>
          <span class="chip">${p.consent.sharing ? 'Sharing ✓' : 'Sharing ✗'}</span>
          <span class="chip">${p.consent.deletion_rights_explained ? 'Deletion rights explained ✓' : 'Deletion rights ✗'}</span>
        </div>
      </div>
      <button type="button" class="btn btn-ghost" data-triage="${i}">Triage</button>
    </div>`).join('');
  list.querySelectorAll('[data-triage]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const select = document.getElementById('triagePatientSelect');
      select.value = `reg:${btn.dataset.triage}`;
      select.dispatchEvent(new Event('change'));
      switchTab('triage');
    });
  });
}
