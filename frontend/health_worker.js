/**
 * AROGYASAATHI - HEALTH WORKER (ASHA / ANM) CONTROLLER
 * Village patient list with check-ins, multilingual voice triage, registration with consent,
 * referral to government facilities, and the daily surveillance report.
 */

const WORKER = requireRole('HEALTH_WORKER');

let patients = [];
let conditions = [];
let village = null;
let selectedPatientId = null;
let checkinLang = 'hi';
let triageLang = 'hi';
let triage = null;
let hospitals = [];
let chosenHospital = null;
let referralEncounter = null;   // set when referring straight from a triage decision

document.addEventListener('DOMContentLoaded', async () => {
  if (!WORKER) return;
  setupTabs((tab) => {
    if (tab === 'refer') loadReferrals();
    if (tab === 'report') loadSignals();
  });
  document.querySelectorAll('[data-goto]').forEach((b) => b.addEventListener('click', () => switchTab(b.dataset.goto)));
  document.getElementById('patientSearch').addEventListener('input', renderPatientList);
  setupTriage();
  setupRegistration();
  setupReferral();
  setupSignals();
  setupDeletes();
  await loadPatients();
});

function setupDeletes() {
  document.getElementById('referralHistory').addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-del-referral]');
    if (btn && await confirmAndDelete(`/api/v1/worker/referrals/${btn.dataset.delReferral}/delete`, 'Delete this referral record?')) loadReferrals();
  });
  document.getElementById('signalHistory').addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-del-signal]');
    if (btn && await confirmAndDelete(`/api/v1/worker/signals/${btn.dataset.delSignal}/delete`, 'Delete this daily report? Outbreak scoring will no longer count it.')) loadSignals();
  });
  document.getElementById('deleteAccountForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!window.confirm('Delete your ASHA account for good? You will be signed out and cannot log in again.')) return;
    try {
      await api('/api/v1/worker/account/delete', { password: document.getElementById('deletePassword').value });
      clearSession();
      window.location.replace('index.html');
    } catch (err) {
      showToast(err.message);
    }
  });
}

// ================= 1. PATIENTS =================
async function loadPatients() {
  try {
    const data = await api('/api/v1/worker/patients');
    patients = data.patients;
    conditions = data.conditions;
    village = data.village;
  } catch (err) {
    document.getElementById('patientList').innerHTML = `<p class="empty-state">${esc(err.message)}</p>`;
    return;
  }
  if (village) document.getElementById('villageLabel').textContent = `ASHA · ${village.name}`;
  renderStats();
  renderPatientList();
  renderPatientOptions();
  renderConditionChips();
  if (!selectedPatientId && patients.length) selectedPatientId = patients[0].id;
  renderPatientDetail();
}

function renderStats() {
  const priority = patients.filter((p) => ['HIGH', 'CRITICAL'].includes(p.risk.risk_level)).length;
  const missed = patients.reduce((n, p) => n + p.dose_strip.doses.filter((d) => d !== 'TAKEN').length, 0);
  document.getElementById('statPatients').textContent = patients.length;
  document.getElementById('statPriority').textContent = priority;
  document.getElementById('statMissed').textContent = missed;
  document.getElementById('statPending').textContent = patients.filter((p) => p.account_status !== 'ACTIVE').length;
  const badge = document.getElementById('priorityCount');
  badge.textContent = priority;
  badge.classList.toggle('hidden', priority === 0);
}

function renderPatientList() {
  const q = document.getElementById('patientSearch').value.trim().toLowerCase();
  const list = document.getElementById('patientList');
  const shown = patients.filter((p) => !q || p.name.toLowerCase().includes(q) || p.mobile.includes(q));
  if (!patients.length) {
    list.innerHTML = '<p class="empty-state">No patients yet. Register your first patient.</p>';
    return;
  }
  list.innerHTML = shown.map((p) => `
    <button type="button" class="list-item ${p.id === selectedPatientId ? 'selected' : ''}" data-id="${esc(p.id)}">
      <div class="list-main">
        <div class="list-title">${esc(p.name)}</div>
        <div class="list-meta">${esc(p.age)} yrs · ${esc(p.conditions.join(', ') || 'No condition recorded')}</div>
        <div class="list-meta">${p.latest ? `BP ${esc(p.latest.systolic ?? '–')}/${esc(p.latest.diastolic ?? '–')} · Sugar ${esc(p.latest.glucose ?? '–')}` : 'No readings yet'}</div>
      </div>
      <div style="display:flex; flex-direction:column; gap:6px; align-items:flex-end;">
        ${levelBadge(p.risk.risk_level)}
        ${p.account_status !== 'ACTIVE' ? '<span class="badge badge-plain">Not activated</span>' : ''}
      </div>
    </button>`).join('') || '<p class="empty-state">No match.</p>';
  list.querySelectorAll('.list-item').forEach((item) => {
    item.addEventListener('click', () => {
      selectedPatientId = item.dataset.id;
      renderPatientList();
      renderPatientDetail();
      if (window.innerWidth < 1100) document.getElementById('patientDetail').scrollIntoView({ behavior: 'smooth' });
    });
  });
}

function renderPatientDetail() {
  const host = document.getElementById('patientDetail');
  const p = patients.find((x) => x.id === selectedPatientId);
  if (!p) {
    host.innerHTML = '<div class="panel"><p class="empty-state">Select a patient.</p></div>';
    return;
  }
  const r = p.risk;
  host.innerHTML = `
    <div class="panel">
      <div class="view-head" style="margin-bottom: 10px;">
        <div>
          <div class="panel-title">${esc(p.name)} ${levelBadge(r.risk_level)}</div>
          <div class="list-meta">${esc(p.pseudonym)} · ${esc(p.age)} yrs / ${esc(p.gender)} · 📞 ${esc(p.mobile)}${p.next_visit ? ` · Next visit ${esc(p.next_visit)}` : ''}</div>
        </div>
      </div>
      <div class="btn-row" style="margin-bottom: 12px;">
        ${telLink(p.mobile, 'Call')}
        <button type="button" class="btn btn-ghost" id="pTriageBtn">🩺 Triage</button>
        <button type="button" class="btn btn-ghost" id="pReferBtn">🏥 Refer</button>
        ${p.account_status !== 'ACTIVE' ? '<button type="button" class="btn btn-ghost" id="pCodeBtn">🔑 New code</button>' : ''}
        <button type="button" class="btn btn-ghost btn-delete" id="pDeleteBtn">🗑 Delete</button>
      </div>
      <div id="pCodeBox"></div>
      ${r.risk_level === 'NO_DATA' ? `<div class="notice notice-blue"><span>ℹ️</span><span>${esc(r.recommended_action)}</span></div>`
    : r.is_deteriorating
      ? `<div class="notice notice-red"><span>⚠️</span><span><strong>Deterioration flagged${r.lead_time_days_before_visit ? ` ${esc(r.lead_time_days_before_visit)} days before the next visit` : ''}.</strong> ${esc(r.recommended_action)}</span></div>`
      : `<div class="notice notice-green"><span>✅</span><span>${esc(r.recommended_action)}</span></div>`}
      <div class="list-flags" style="margin: 12px 0;">
        ${r.flags.map((f) => `<span class="chip chip-red">${esc(prettyCode(f))}</span>`).join('')}
        ${r.risk_level !== 'NO_DATA' ? `<span class="chip">Adherence ${esc(r.adherence_rate_pct)}%</span>` : ''}
      </div>
      <div class="grid-2">
        <div><div class="panel-title">Blood pressure</div><div class="chart-box" id="bpChart"></div></div>
        <div><div class="panel-title">Sugar</div><div class="chart-box" id="sugarChart"></div></div>
      </div>
      <div style="margin-top: 12px;"><div class="panel-title">Medicine doses</div><div id="doseStrip"></div></div>
    </div>

    <form class="panel" id="checkinForm">
      <div class="panel-title">Record today's check-in</div>
      <div class="panel-sub">Choose the language, tap 🎙️ and let the patient say their reading, e.g. "BP 150 by 95, I took my medicine". Check the numbers below before saving.</div>
      <div class="lang-chips" id="checkinLangs" style="margin-bottom: 10px;"></div>
      <div class="speech-input-row" style="margin-top: 0;">
        <button type="button" class="mic-inline" id="checkinMic" aria-label="Speak">🎙️</button>
        <input id="checkinTranscript" class="form-input" placeholder="Spoken words appear here (you can edit)" autocomplete="off">
      </div>
      <div class="form-row" style="margin-top: 12px;">
        <div class="form-group"><label for="ciSys">Upper BP</label><input id="ciSys" class="form-input" type="number" inputmode="numeric" placeholder="mmHg"></div>
        <div class="form-group"><label for="ciDia">Lower BP</label><input id="ciDia" class="form-input" type="number" inputmode="numeric" placeholder="mmHg"></div>
        <div class="form-group"><label for="ciSugar">Sugar</label><input id="ciSugar" class="form-input" type="number" inputmode="decimal" placeholder="mg/dL"></div>
      </div>
      <div class="form-group">
        <label>Today's medicine</label>
        <div class="segmented" id="ciDose">
          <button type="button" class="active" data-dose="">Not asked</button>
          <button type="button" data-dose="TAKEN">Taken</button>
          <button type="button" data-dose="MISSED">Missed</button>
        </div>
      </div>
      <div class="form-group">
        <label for="ciNextVisit">Next PHC visit</label>
        <input id="ciNextVisit" class="form-input" type="date" value="${esc(p.next_visit || '')}">
      </div>
      <button type="submit" class="btn btn-primary btn-block">Save Check-in</button>
    </form>`;

  renderTrendCharts(p.trend, document.getElementById('bpChart'), document.getElementById('sugarChart'));
  renderDoseStrip(document.getElementById('doseStrip'), p.dose_strip.doses, p.dose_strip.days);

  checkinLang = p.language || 'hi';
  renderLanguageChips(document.getElementById('checkinLangs'), checkinLang, (code) => { checkinLang = code; });
  const transcript = document.getElementById('checkinTranscript');
  attachDictation(document.getElementById('checkinMic'), transcript, () => checkinLang, (text) => fillFromSpeech(text));
  transcript.addEventListener('change', () => fillFromSpeech(transcript.value));
  document.querySelectorAll('#ciDose button').forEach((btn) => {
    btn.addEventListener('click', () => document.querySelectorAll('#ciDose button').forEach((b) => b.classList.toggle('active', b === btn)));
  });
  document.getElementById('checkinForm').addEventListener('submit', (e) => { e.preventDefault(); submitCheckin(p.id); });
  document.getElementById('pTriageBtn').addEventListener('click', () => {
    document.getElementById('triagePatient').value = p.id;
    document.getElementById('triagePatient').dispatchEvent(new Event('change'));
    switchTab('triage');
  });
  document.getElementById('pReferBtn').addEventListener('click', () => openReferral({ patientId: p.id }));
  document.getElementById('pDeleteBtn').addEventListener('click', async () => {
    const done = await confirmAndDelete(`/api/v1/worker/patients/${p.id}/delete`,
      `Delete ${p.name}'s record for good? Their readings, medicine log, referrals and chat are erased and they can no longer sign in. This cannot be undone.`);
    if (done) { selectedPatientId = null; await loadPatients(); }
  });
  const codeBtn = document.getElementById('pCodeBtn');
  if (codeBtn) {
    codeBtn.addEventListener('click', async () => {
      try {
        const res = await api(`/api/v1/worker/patients/${p.id}/activation-code`, {});
        document.getElementById('pCodeBox').innerHTML = activationBox(p.name, res.activation_code, res.activation_hours);
      } catch (err) {
        showToast(err.message);
      }
    });
  }
}

/** Fills the number boxes from spoken words so the ASHA can check them before saving. */
function fillFromSpeech(text) {
  const normalized = text.replace(/[०-९]/g, (d) => '०१२३४५६७८९'.indexOf(d))
    .replace(/[০-৯]/g, (d) => '০১২৩৪৫৬৭৮৯'.indexOf(d))
    .replace(/[౦-౯]/g, (d) => '౦౧౨౩౪౫౬౭౮౯'.indexOf(d));
  const bp = normalized.match(/(\d{2,3})\s*(?:\/|by|over|बटा|बाय|बाई|ओवर|বাই|ওভার|బై|ఓవర్|,|-)\s*(\d{2,3})/i);
  if (bp && !document.getElementById('ciSys').value) {
    document.getElementById('ciSys').value = bp[1];
    document.getElementById('ciDia').value = bp[2];
  }
  const sugar = normalized.match(/(?:sugar|शुगर|सुगर|शर्करा|साखर|সুগার|শর্করা|షుగర్|చక్కెర)\D{0,12}(\d{2,3})/i);
  if (sugar && !document.getElementById('ciSugar').value) document.getElementById('ciSugar').value = sugar[1];
}

async function submitCheckin(patientId) {
  const val = (id) => document.getElementById(id).value.trim();
  const transcript = val('checkinTranscript');
  const body = {
    transcript,
    language: detectLanguage(transcript, checkinLang),
    systolic: val('ciSys'),
    diastolic: val('ciDia'),
    glucose: val('ciSugar'),
    dose_status: document.querySelector('#ciDose button.active').dataset.dose || null,
    next_visit: val('ciNextVisit') || null
  };
  try {
    const res = await api(`/api/v1/worker/patients/${patientId}/checkin`, body);
    showToast(res.escalation_id
      ? `Saved. Risk ${res.patient.risk.risk_level}: sent to the doctor's queue.`
      : `Saved. Risk: ${LEVEL_TEXT[res.patient.risk.risk_level] || res.patient.risk.risk_level}`);
    await loadPatients();
  } catch (err) {
    showToast(err.message);
  }
}

function activationBox(name, code, hours) {
  return `<div class="notice notice-green" style="display:block; margin-bottom: 12px;">
    <strong>Activation code for ${esc(name)}</strong>
    <div class="code-box">${esc(code)}</div>
    Valid for ${esc(hours)} hours. The patient opens ArogyaSaathi → <em>First time? Activate account</em>, enters their mobile number and this code, and sets a password.
  </div>`;
}

// ================= 2. VOICE TRIAGE =================
function renderPatientOptions() {
  const options = patients.map((p) => `<option value="${esc(p.id)}">${esc(p.name)} · ${esc(p.age)} yrs</option>`).join('');
  const triageSelect = document.getElementById('triagePatient');
  const keep = triageSelect.value;
  triageSelect.innerHTML = `<option value="">Walk-in (not registered)</option>${options}`;
  triageSelect.value = keep;
  const referSelect = document.getElementById('referPatient');
  const keepRefer = referSelect.value;
  referSelect.innerHTML = `<option value="">Choose patient…</option>${options}`;
  referSelect.value = keepRefer;
}

function setupTriage() {
  renderLanguageChips(document.getElementById('triageLangs'), triageLang, (code) => { triageLang = code; });
  const select = document.getElementById('triagePatient');
  select.addEventListener('change', () => {
    const p = patients.find((x) => x.id === select.value);
    document.getElementById('walkinFields').classList.toggle('hidden', Boolean(p));
    if (p) {
      triageLang = p.language || 'hi';
      renderLanguageChips(document.getElementById('triageLangs'), triageLang, (code) => { triageLang = code; });
      document.getElementById('triageConsent').checked = Boolean(p.consent && p.consent.data_use);
    }
  });
  document.getElementById('startTriageBtn').addEventListener('click', startTriage);
  const input = document.getElementById('triageText');
  attachDictation(document.getElementById('triageMic'), input, () => triageLang);
  document.getElementById('triageForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (text) sendTriage(text);
  });
}

async function startTriage() {
  if (!document.getElementById('triageConsent').checked) {
    showToast("Take the patient's voice consent first");
    return;
  }
  const patientId = document.getElementById('triagePatient').value;
  const vitals = {};
  [['vitalTemp', 'temperature_f'], ['vitalSpo2', 'spo2'], ['vitalSys', 'systolic_bp']].forEach(([id, key]) => {
    const v = document.getElementById(id).value;
    if (v) vitals[key] = Number(v);
  });
  const body = { language: triageLang, consent: { data_use: true }, vitals };
  if (patientId) body.patient_id = patientId;
  else body.walkin = { age: document.getElementById('walkAge').value, gender: document.getElementById('walkGender').value };
  try {
    triage = await api('/api/v1/triage/sessions', body);
  } catch (err) {
    showToast(err.message);
    return;
  }
  document.getElementById('conversation').innerHTML = '';
  document.getElementById('quickAnswers').innerHTML = '';
  document.getElementById('decisionPanel').classList.add('hidden');
  const badge = document.getElementById('triageSessionBadge');
  badge.textContent = `${triage.session_id} · ${langInfo(triage.language).label}`;
  badge.classList.remove('hidden');
  document.getElementById('triageConvSub').textContent =
    `${triage.patient.pseudonym} · ${triage.patient.age} yrs · ${triage.patient.village_name}. Ask: "What is the problem?"`;
  setTriageInput(true);
  document.getElementById('triageText').focus();
}

function setTriageInput(enabled) {
  ['triageMic', 'triageText', 'triageSend'].forEach((id) => { document.getElementById(id).disabled = !enabled; });
}

async function sendTriage(text) {
  if (!triage || triage.is_final) return;
  document.getElementById('triageText').value = '';
  appendTurn('turn-input', 'Patient', text);
  setTriageInput(false);
  try {
    triage = await api(`/api/v1/triage/sessions/${triage.session_id}/turn`, { text });
  } catch (err) {
    showToast(err.message);
    setTriageInput(true);
    return;
  }
  if (triage.needs_words) {
    appendTurn('turn-question', 'Please answer in words', triage.needs_words);
    renderQuickAnswers(triage.quick_answers);
    setTriageInput(true);
    return;
  }
  if (triage.is_final) {
    document.getElementById('quickAnswers').innerHTML = '';
    renderDecision(triage);
    return;
  }
  appendTurn('turn-question', 'Ask the patient', triage.next_question, triage.next_question_en, triage.checklist);
  renderQuickAnswers(triage.quick_answers);
  setTriageInput(true);
  speak(triage.next_question, triage.language);
}

function renderQuickAnswers(answers) {
  const host = document.getElementById('quickAnswers');
  host.innerHTML = (answers || []).map((a, i) => `<button type="button" class="btn btn-ghost btn-sm" data-i="${i}">${esc(a.label)}</button>`).join('');
  host.querySelectorAll('button').forEach((b) => {
    b.addEventListener('click', () => {
      host.innerHTML = '';
      sendTriage(answers[Number(b.dataset.i)].text);
    });
  });
}

function appendTurn(cls, label, text, subText, checks) {
  document.getElementById('conversation').insertAdjacentHTML('beforeend', `
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
  const canRefer = ['EMERGENCY', 'REFER'].includes(s.triage_level);
  panel.innerHTML = `
    <div class="panel-title">3. Decision</div>
    <div class="decision-card d-${esc(s.triage_level)}" style="margin-top: 10px;">
      <div class="decision-level">${esc(s.triage_label)}</div>
      <div class="decision-rationale">${esc(s.decision_rationale)}</div>
      ${s.is_red_flag_overridden ? `<div class="notice notice-red" style="margin-top: 12px;"><span>🛑</span><span><strong>Red-flag rule fired.</strong> The fixed safety rule decided this. Danger signs: ${(s.danger_signs.length ? s.danger_signs : s.symptoms).map((d) => esc(prettyCode(d))).join(', ')}</span></div>` : ''}
      ${s.uncertain ? `<div class="notice notice-amber" style="margin-top: 12px;"><span>❓</span><span><strong>Uncertain.</strong> ${esc(s.uncertainty_reason)}</span></div>` : ''}
      <div class="decision-section">
        <h4>Step-by-step checklist</h4>
        <ul class="checklist">${s.checklist.map((c) => `<li><label><input type="checkbox"><span>${esc(c)}</span></label></li>`).join('')}</ul>
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
    ${s.escalation_id ? `<div class="notice notice-green" style="margin-top: 10px;"><span>📤</span><span>Summary sent to the PHC doctor's queue (${esc(s.escalation_id)}).</span></div>` : ''}
    <div class="btn-row" style="margin-top: 14px;">
      ${s.triage_level === 'EMERGENCY' ? '<a href="tel:108" class="btn sos-btn">🚑 Call 108 now</a>' : ''}
      ${canRefer ? '<button type="button" class="btn btn-primary" id="referFromTriage">🏥 Refer to govt hospital</button>' : ''}
      ${s.summary_markdown ? '<button type="button" class="btn btn-ghost" id="toggleSummary">Doctor summary</button>' : ''}
      <button type="button" class="btn btn-ghost" id="newTriage">New triage</button>
    </div>
    ${s.summary_markdown ? `<div class="summary-doc hidden" id="triageSummary" style="margin-top: 14px;">${renderMarkdown(s.summary_markdown)}</div>` : ''}`;
  const toggle = document.getElementById('toggleSummary');
  if (toggle) toggle.addEventListener('click', () => document.getElementById('triageSummary').classList.toggle('hidden'));
  const refer = document.getElementById('referFromTriage');
  if (refer) {
    refer.addEventListener('click', () => openReferral({
      patientId: s.patient.id,
      encounterId: s.session_id,
      urgency: s.triage_level === 'EMERGENCY' ? 'EMERGENCY' : 'SAME_DAY',
      reason: `${s.triage_label}: ${s.symptoms.map(prettyCode).join(', ')}`,
      label: `${s.patient.pseudonym} (triage ${s.session_id})`
    }));
  }
  document.getElementById('newTriage').addEventListener('click', () => {
    triage = null;
    panel.classList.add('hidden');
    document.getElementById('conversation').innerHTML = '';
    document.getElementById('triageSessionBadge').classList.add('hidden');
    document.getElementById('triageConvSub').textContent = 'Start triage to begin.';
    setTriageInput(false);
    document.getElementById('triageSetupPanel').scrollIntoView({ behavior: 'smooth' });
  });
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ================= 3. REGISTRATION =================
function renderConditionChips() {
  const host = document.getElementById('regConditions');
  if (host.children.length) return;
  host.innerHTML = conditions.map((c) => `<label><input type="checkbox" value="${esc(c)}"> ${esc(c)}</label>`).join('');
}

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
    try {
      const res = await api('/api/v1/worker/patients', {
        name,
        mobile: document.getElementById('regMobile').value,
        age: document.getElementById('regAge').value,
        gender: document.getElementById('regGender').value,
        language: document.getElementById('regLanguage').value,
        next_visit: document.getElementById('regNextVisit').value || null,
        conditions: [...document.querySelectorAll('#regConditions input:checked')].map((i) => i.value),
        consent
      });
      e.target.reset();
      document.getElementById('registerResult').innerHTML = `
        <div class="panel-title">✅ Registered: ${esc(res.pseudonym)}</div>
        ${activationBox(name, res.activation_code, res.activation_hours)}
        <button type="button" class="btn btn-ghost" id="regDone">Open patient</button>`;
      document.getElementById('regDone').addEventListener('click', () => {
        selectedPatientId = res.id;
        renderPatientList();
        renderPatientDetail();
        switchTab('patients');
      });
      selectedPatientId = res.id;
      await loadPatients();
    } catch (err) {
      showToast(err.message);
    }
  });
}

// ================= 4. REFERRAL TO GOVERNMENT FACILITY =================
function setupReferral() {
  document.getElementById('referPatient').addEventListener('change', () => {
    referralEncounter = null;
    document.getElementById('referEncounterNote').textContent = '';
  });
  document.getElementById('findHereBtn').addEventListener('click', () => {
    const status = document.getElementById('hospitalStatus');
    if (!navigator.geolocation) {
      status.textContent = 'Location not available on this device. Use "Near my village".';
      return;
    }
    status.textContent = 'Getting your location…';
    navigator.geolocation.getCurrentPosition(
      (pos) => findHospitals(pos.coords.latitude, pos.coords.longitude),
      (err) => { status.textContent = `Could not get location (${err.message}). Allow location, or use "Near my village".`; },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 120000 }
    );
  });
  document.getElementById('findVillageBtn').addEventListener('click', () => findHospitals(null, null));
  document.getElementById('manUseBtn').addEventListener('click', () => {
    const name = document.getElementById('manName').value.trim();
    if (!name) { showToast('Enter the hospital name'); return; }
    chooseHospital({
      name, level: 'Government facility', address: document.getElementById('manAddress').value.trim(),
      phone: document.getElementById('manPhone').value.trim(), source: 'Entered by health worker'
    });
  });
}

function openReferral({ patientId, encounterId, urgency, reason, label }) {
  const select = document.getElementById('referPatient');
  select.value = patientId || '';
  referralEncounter = encounterId || null;
  document.getElementById('referEncounterNote').textContent = encounterId && !patientId ? `Walk-in: ${label}` : (encounterId ? `From triage ${encounterId}` : '');
  if (urgency) document.getElementById('referUrgency').value = urgency;
  if (reason) document.getElementById('referReason').value = reason;
  document.getElementById('referSlip').classList.add('hidden');
  switchTab('refer', () => loadReferrals());
}

async function findHospitals(lat, lon) {
  const status = document.getElementById('hospitalStatus');
  const radius = document.getElementById('referRadius').value;
  status.textContent = 'Searching government facilities…';
  document.getElementById('hospitalList').innerHTML = '<p class="empty-state">Searching…</p>';
  const params = new URLSearchParams({ radius });
  if (lat != null) { params.set('lat', lat); params.set('lon', lon); }
  try {
    const res = await api(`/api/v1/hospitals?${params}`);
    hospitals = res.facilities;
    status.textContent = `${hospitals.length} government facilities within ${res.radius_km} km (OpenStreetMap).`;
    renderHospitals();
  } catch (err) {
    status.textContent = err.message;
    document.getElementById('hospitalList').innerHTML = '<p class="empty-state">Could not search. Enter the hospital manually below.</p>';
  }
}

function renderHospitals() {
  const host = document.getElementById('hospitalList');
  if (!hospitals.length) {
    host.innerHTML = '<p class="empty-state">No government facilities found. Try 50 km, or enter the hospital manually.</p>';
    return;
  }
  host.innerHTML = hospitals.map((h, i) => `
    <div class="list-item hospital-item">
      <div class="list-main">
        <div class="list-title">${esc(h.name)}</div>
        <div class="list-meta">${esc(h.level)} · ${esc(h.distance_km)} km${h.emergency ? ' · 24×7 emergency' : ''}</div>
        ${h.address ? `<div class="list-meta">📍 ${esc(h.address)}</div>` : ''}
        <div class="list-meta">${h.phone ? `📞 ${esc(h.phone)}` : 'No phone listed'} · <a href="${esc(mapsLink(h.lat, h.lon))}" target="_blank" rel="noopener">Map</a></div>
      </div>
      <button type="button" class="btn btn-primary btn-sm" data-i="${i}">Choose</button>
    </div>`).join('');
  host.querySelectorAll('[data-i]').forEach((b) => b.addEventListener('click', () => chooseHospital(hospitals[Number(b.dataset.i)])));
}

function chooseHospital(h) {
  chosenHospital = { ...h };
  const slip = document.getElementById('referSlip');
  slip.classList.remove('hidden');
  slip.innerHTML = `
    <div class="panel-title">3. Confirm referral</div>
    <div class="list-title" style="margin-top: 8px;">${esc(h.name)}</div>
    <div class="list-meta">${esc(h.level || '')}${h.distance_km != null ? ` · ${esc(h.distance_km)} km` : ''}</div>
    <div class="form-group" style="margin-top: 10px;">
      <label for="slipPhone">Hospital phone (add if you know it)</label>
      <input id="slipPhone" class="form-input" type="tel" value="${esc(h.phone || '')}" placeholder="Phone">
    </div>
    <button type="button" class="btn btn-green btn-block" id="sendReferral">Send referral</button>`;
  document.getElementById('sendReferral').addEventListener('click', sendReferral);
  slip.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function sendReferral() {
  const patientId = document.getElementById('referPatient').value;
  if (!patientId && !referralEncounter) {
    showToast('Choose the patient to refer');
    return;
  }
  chosenHospital.phone = document.getElementById('slipPhone').value.trim();
  try {
    const res = await api('/api/v1/referrals', {
      patient_id: patientId || null,
      encounter_id: referralEncounter,
      hospital: chosenHospital,
      urgency: document.getElementById('referUrgency').value,
      reason: document.getElementById('referReason').value.trim()
    });
    showReferralSlip(res);
    loadReferrals();
  } catch (err) {
    showToast(err.message);
  }
}

function showReferralSlip(ref) {
  const h = ref.hospital;
  const patient = patients.find((p) => p.id === document.getElementById('referPatient').value);
  const reason = document.getElementById('referReason').value.trim();
  const message = [
    'ArogyaSaathi referral',
    patient ? `Patient: ${patient.name} (${ref.pseudonym})` : `Patient ID: ${ref.pseudonym}`,
    `Go to: ${h.name}${h.level ? ` (${h.level})` : ''}`,
    h.address ? `Address: ${h.address}` : '',
    h.phone ? `Hospital phone: ${h.phone}` : '',
    `Urgency: ${LEVEL_TEXT[ref.urgency] || ref.urgency}`,
    reason ? `Reason: ${reason}` : '',
    `Directions: ${mapsLink(h.lat, h.lon, h.name)}`,
    'Emergency ambulance: 108',
    `Referral ID: ${ref.id}`
  ].filter(Boolean).join('\n');
  const waNumber = patient ? `91${patient.mobile}` : '';
  document.getElementById('referSlip').innerHTML = `
    <div class="panel-title">✅ Referral sent (${esc(ref.id)})</div>
    <div class="summary-doc" style="margin-top: 10px; white-space: pre-wrap;">${esc(message)}</div>
    <div class="btn-row" style="margin-top: 12px;">
      <a class="btn btn-green btn-call" href="https://wa.me/${esc(waNumber)}?text=${encodeURIComponent(message)}" target="_blank" rel="noopener">💬 Send on WhatsApp</a>
      ${telLink(h.phone, 'Call hospital')}
      <a class="btn btn-ghost btn-call" href="${esc(mapsLink(h.lat, h.lon, h.name))}" target="_blank" rel="noopener">🧭 Directions</a>
      ${ref.urgency === 'EMERGENCY' ? '<a class="btn sos-btn btn-call" href="tel:108">🚑 Call 108</a>' : ''}
    </div>
    <div class="form-hint">${patient ? 'The patient also sees this referral in their app.' : 'Walk-in patient: share this slip on WhatsApp or show it to them.'}</div>`;
}

async function loadReferrals() {
  try {
    const rows = await api('/api/v1/worker/referrals');
    document.getElementById('referralHistory').innerHTML = rows.length ? rows.map((r) => `
      <div class="list-item"><div class="list-main">
        <div class="list-title">${esc(r.hospital.name)} ${levelBadge(r.urgency)}</div>
        <div class="list-meta">${esc(r.pseudonym)} · ${esc(formatDateTime(r.created_at))}${r.reason ? ` · ${esc(r.reason)}` : ''}</div>
      </div><button type="button" class="btn btn-ghost btn-delete" data-del-referral="${esc(r.id)}">🗑</button></div>`).join('') : '<p class="empty-state">No referrals yet.</p>';
  } catch (err) {
    showToast(err.message);
  }
}

// ================= 5. DAILY SURVEILLANCE REPORT =================
function setupSignals() {
  const today = new Date();
  const iso = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  const date = document.getElementById('sigDate');
  date.value = iso;
  date.max = iso;
  document.getElementById('signalForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const val = (id) => document.getElementById(id).value;
    try {
      await api('/api/v1/signals', {
        date: val('sigDate'),
        pharmacy_ors_sales: val('sigOrs'),
        pharmacy_fever_sales: val('sigFever'),
        school_absent: val('sigAbsent'),
        school_enrolled: val('sigEnrolled')
      });
      showToast('Report saved. Thank you!');
      loadSignals();
    } catch (err) {
      showToast(err.message);
    }
  });
}

async function loadSignals() {
  try {
    const rows = await api('/api/v1/worker/signals');
    document.getElementById('signalHistory').innerHTML = rows.length ? rows.map((r) => `
      <tr><td>${esc(r.date)}</td><td>${esc(r.pharmacy_ors_sales ?? '–')}</td><td>${esc(r.pharmacy_fever_sales ?? '–')}</td>
      <td>${esc(r.school_absent ?? '–')}${r.school_enrolled ? ` / ${esc(r.school_enrolled)}` : ''}</td>
      <td><button type="button" class="btn btn-ghost btn-delete" data-del-signal="${esc(r.id)}">🗑</button></td></tr>`).join('')
      : '<tr><td colspan="5" class="empty-state">No reports yet.</td></tr>';
  } catch (err) {
    showToast(err.message);
  }
}
