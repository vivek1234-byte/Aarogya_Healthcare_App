/**
 * AROGYASAATHI - PATIENT PAGE CONTROLLER
 * Own readings and trends, daily medicine check-in, doctor notes, hospital referrals,
 * Hindi / English interface and the multilingual health assistant.
 */

const PATIENT = requireRole('PATIENT');

const I18N = {
  en: {
    role: 'My Health', tabHome: 'Home', tabReports: 'Doctor & Hospital', signOut: 'Sign Out', hello: 'Namaste',
    medToday: "Did you take today's medicine?", taken: 'Yes, taken', missed: 'No, missed', myAsha: 'My ASHA worker',
    myReadings: 'My readings', addReading: 'Add reading', bpTrend: 'Blood pressure', sugarTrend: 'Sugar',
    medHistory: 'Medicine (last 14 days)', history: 'Reading history', reportsTitle: 'Doctor notes & hospital referrals',
    referralsTitle: 'Hospital referrals', notesTitle: 'Notes from your doctor', bpLabel: 'Blood pressure (upper / lower)',
    sugarLabel: 'Sugar (mg/dL)', fasting: 'Empty stomach', afterMeal: 'After meal', random: 'Any time',
    pulseLabel: 'Pulse (per minute)', weightLabel: 'Weight (kg)', save: 'Save', askAssistant: 'Ask',
    assistant: 'Health assistant', assistantNote: 'Not a doctor. In an emergency call 108.',
    bp: 'Blood pressure', sugar: 'Sugar', pulse: 'Pulse', weight: 'Weight', noReading: 'No reading yet',
    normal: 'Normal', high: 'High', veryHigh: 'Very high', low: 'Low',
    doseSaved: 'Saved. Thank you!', doseTodayTaken: "Today's medicine: taken ✅", doseTodayMissed: "Today's medicine: missed ❌",
    doseNone: 'Not recorded yet today.', readingSaved: 'Reading saved.', teamAlerted: 'Your ASHA worker and doctor have been informed.',
    riskHigh: 'Your recent readings need attention. Your ASHA worker has been informed and will contact you.',
    riskCritical: 'Your reading is dangerously high or low. If you feel unwell (chest pain, breathlessness, fainting), call 108 now. Your ASHA worker and doctor have been informed.',
    noAsha: 'Not assigned', callAsha: 'Call ASHA', noReferrals: 'No hospital referrals.', noReports: 'No notes from the doctor yet.',
    callHospital: 'Call hospital', directions: 'Directions', referredOn: 'Referred on', reason: 'Reason', urgency: 'Urgency',
    by: 'by', new: 'New', noHistory: 'No readings yet. Your ASHA worker records them at each visit.', placeholder: 'Type or speak…',
    thinking: 'Thinking…', readAloud: 'Read aloud', call108: 'Call 108', voiceMissing: 'This phone has no voice for this language, so replies will not be read aloud.',
    enterReading: 'Enter at least one reading.', years: 'yrs', next: 'Next visit',
    urgencyLevels: { EMERGENCY: 'Emergency – go now', SAME_DAY: 'Go today', WITHIN_WEEK: 'Within a week' }
  },
  hi: {
    role: 'मेरा स्वास्थ्य', tabHome: 'होम', tabReports: 'डॉक्टर और अस्पताल', signOut: 'लॉग आउट', hello: 'नमस्ते',
    medToday: 'क्या आज की दवा ली?', taken: 'हाँ, ली', missed: 'नहीं ली', myAsha: 'मेरी आशा कार्यकर्ता',
    myReadings: 'मेरी जाँच', addReading: 'जाँच जोड़ें', bpTrend: 'ब्लड प्रेशर (बीपी)', sugarTrend: 'शुगर',
    medHistory: 'दवा (पिछले 14 दिन)', history: 'पुरानी जाँचें', reportsTitle: 'डॉक्टर की सलाह और अस्पताल रेफ़रल',
    referralsTitle: 'अस्पताल रेफ़रल', notesTitle: 'डॉक्टर की सलाह', bpLabel: 'ब्लड प्रेशर (ऊपर / नीचे)',
    sugarLabel: 'शुगर (mg/dL)', fasting: 'खाली पेट', afterMeal: 'खाने के बाद', random: 'कभी भी',
    pulseLabel: 'नब्ज़ (प्रति मिनट)', weightLabel: 'वज़न (किलो)', save: 'सेव करें', askAssistant: 'पूछें',
    assistant: 'स्वास्थ्य सहायक', assistantNote: 'यह डॉक्टर नहीं है। आपातकाल में 108 पर कॉल करें।',
    bp: 'बीपी', sugar: 'शुगर', pulse: 'नब्ज़', weight: 'वज़न', noReading: 'अभी कोई जाँच नहीं',
    normal: 'सामान्य', high: 'ज़्यादा', veryHigh: 'बहुत ज़्यादा', low: 'कम',
    doseSaved: 'सेव हो गया। धन्यवाद!', doseTodayTaken: 'आज की दवा: ली ✅', doseTodayMissed: 'आज की दवा: नहीं ली ❌',
    doseNone: 'आज अभी दर्ज नहीं किया।', readingSaved: 'जाँच सेव हो गई।', teamAlerted: 'आपकी आशा कार्यकर्ता और डॉक्टर को सूचना भेज दी गई है।',
    riskHigh: 'आपकी हाल की जाँचों पर ध्यान देना ज़रूरी है। आपकी आशा कार्यकर्ता को सूचना दी गई है, वे आपसे संपर्क करेंगी।',
    riskCritical: 'आपकी जाँच ख़तरनाक रूप से ज़्यादा या कम है। तबीयत ख़राब लगे (सीने में दर्द, सांस फूलना, बेहोशी) तो अभी 108 पर कॉल करें। आशा और डॉक्टर को सूचना दी गई है।',
    noAsha: 'नहीं जुड़ी', callAsha: 'आशा को कॉल करें', noReferrals: 'कोई अस्पताल रेफ़रल नहीं।', noReports: 'डॉक्टर की कोई सलाह अभी नहीं।',
    callHospital: 'अस्पताल को कॉल करें', directions: 'रास्ता देखें', referredOn: 'रेफ़र की तारीख़', reason: 'कारण', urgency: 'कितनी जल्दी',
    by: '—', new: 'नया', noHistory: 'अभी कोई जाँच नहीं। आपकी आशा कार्यकर्ता हर विज़िट पर जाँच दर्ज करती हैं।', placeholder: 'लिखें या बोलें…',
    thinking: 'सोच रहा है…', readAloud: 'सुनें', call108: '108 पर कॉल करें', voiceMissing: 'इस फ़ोन में इस भाषा की आवाज़ नहीं है, इसलिए जवाब पढ़कर नहीं सुनाए जाएंगे।',
    enterReading: 'कम से कम एक जाँच भरें।', years: 'वर्ष', next: 'अगली विज़िट',
    urgencyLevels: { EMERGENCY: 'आपातकाल – अभी जाएं', SAME_DAY: 'आज ही जाएं', WITHIN_WEEK: 'एक हफ़्ते में' }
  }
};

const SUGGESTIONS = {
  hi: ['मेरा बीपी कैसा है?', 'शुगर कम करने के लिए क्या खाएं?', 'दवा भूल जाऊं तो क्या करूं?'],
  en: ['How is my BP?', 'What should I eat to control sugar?', 'What if I forget my medicine?'],
  bn: ['আমার রক্তচাপ কেমন?', 'সুগার কমাতে কী খাব?', 'ওষুধ ভুলে গেলে কী করব?'],
  mr: ['माझा बीपी कसा आहे?', 'साखर कमी करण्यासाठी काय खावे?', 'औषध विसरलो तर काय करावे?'],
  te: ['నా బీపీ ఎలా ఉంది?', 'షుగర్ తగ్గడానికి ఏమి తినాలి?', 'మందు మర్చిపోతే ఏమి చేయాలి?']
};

let uiLang = 'hi';
let chatLang = 'hi';
let speakReplies = true;
let dashboard = null;
let chatLoaded = false;

const t = (key) => (I18N[uiLang] && I18N[uiLang][key]) || I18N.en[key] || key;

// ================= 1. INIT =================
document.addEventListener('DOMContentLoaded', () => {
  if (!PATIENT) return;
  try {
    uiLang = localStorage.getItem('arogya_ui_lang') || (PATIENT.language === 'en' ? 'en' : 'hi');
    speakReplies = localStorage.getItem('arogya_speak') !== 'off';
  } catch (e) { /* defaults */ }
  chatLang = PATIENT.language || uiLang;

  setupTabs((tab) => { if (tab === 'reports') markReportsRead(); });
  document.querySelectorAll('[data-ui-lang]').forEach((btn) => btn.addEventListener('click', () => setUiLang(btn.dataset.uiLang)));
  document.querySelectorAll('.dose-btn').forEach((btn) => btn.addEventListener('click', () => saveDose(btn.dataset.dose)));
  setupAssistant();
  applyUiLang();
  loadDashboard();
});

function setUiLang(lang) {
  uiLang = lang;
  try { localStorage.setItem('arogya_ui_lang', lang); } catch (e) { /* ignore */ }
  applyUiLang();
  if (dashboard) renderAll();
}

function applyUiLang() {
  document.documentElement.lang = uiLang;
  document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-ui-lang]').forEach((b) => b.classList.toggle('active', b.dataset.uiLang === uiLang));
  document.getElementById('chatInput').placeholder = t('placeholder');
}

// ================= 2. DATA =================
async function loadDashboard() {
  try {
    dashboard = await api('/api/v1/me/dashboard');
  } catch (err) {
    showToast(err.message);
    return;
  }
  renderAll();
}

function renderAll() {
  const p = dashboard.patient;
  document.querySelectorAll('[data-user-name]').forEach((el) => { el.textContent = p.name; });
  document.getElementById('patientMeta').textContent =
    `${p.pseudonym} · ${p.age} ${t('years')} · ${p.village_name}${p.next_visit ? ` · ${t('next')}: ${p.next_visit}` : ''}`;
  renderRisk(p.risk);
  renderDose(dashboard.today_dose);
  renderAsha(dashboard.asha);
  renderVitalTiles(p.latest);
  renderTrendCharts(p.trend, document.getElementById('bpChart'), document.getElementById('sugarChart'));
  renderDoseStrip(document.getElementById('doseStrip'), p.dose_strip.doses, p.dose_strip.days);
  renderHistory(dashboard.vitals_history);
  renderReferrals(dashboard.referrals);
  renderReports(dashboard.reports);
}

function renderRisk(risk) {
  const host = document.getElementById('riskNotice');
  if (risk.risk_level === 'CRITICAL') {
    host.innerHTML = `<div class="notice notice-red" style="margin-bottom:16px;"><span>🚨</span><span>${esc(t('riskCritical'))}
      <br><a href="tel:108" class="btn sos-btn btn-sm" style="margin-top:8px;">🚑 ${esc(t('call108'))}</a></span></div>`;
  } else if (risk.risk_level === 'HIGH') {
    host.innerHTML = `<div class="notice notice-amber" style="margin-bottom:16px;"><span>⚠️</span><span>${esc(t('riskHigh'))}</span></div>`;
  } else {
    host.innerHTML = '';
  }
}

function renderDose(status) {
  document.querySelectorAll('.dose-btn').forEach((b) => {
    b.classList.toggle('selected-TAKEN', status === 'TAKEN' && b.dataset.dose === 'TAKEN');
    b.classList.toggle('selected-MISSED', status === 'MISSED' && b.dataset.dose === 'MISSED');
  });
  document.getElementById('doseStatus').textContent =
    status === 'TAKEN' ? t('doseTodayTaken') : status === 'MISSED' ? t('doseTodayMissed') : t('doseNone');
}

function renderAsha(asha) {
  document.getElementById('ashaInfo').innerHTML = asha
    ? `<div class="list-title">${esc(asha.name)}</div><div class="btn-row" style="margin-top:10px;">${telLink(asha.mobile, t('callAsha'))}</div>`
    : esc(t('noAsha'));
}

function bpStatus(sys, dia) {
  if (sys >= 180 || dia >= 120) return ['veryHigh', 'CRITICAL'];
  if (sys >= 140 || dia >= 90) return ['high', 'HIGH'];
  if (sys < 90 || dia < 60) return ['low', 'MODERATE'];
  return ['normal', 'LOW'];
}

function sugarStatus(value, context) {
  if (value < 70) return ['low', 'CRITICAL'];
  if (value >= 300) return ['veryHigh', 'CRITICAL'];
  const limit = context === 'FASTING' ? 126 : 200;
  return value >= limit ? ['high', 'HIGH'] : ['normal', 'LOW'];
}

function pulseStatus(value) {
  if (value > 120 || value < 45) return ['veryHigh', 'CRITICAL'];
  if (value > 100) return ['high', 'HIGH'];
  if (value < 55) return ['low', 'MODERATE'];
  return ['normal', 'LOW'];
}

function latestOf(field) {
  return (dashboard.vitals_history || []).find((v) => v[field] !== null && v[field] !== undefined);
}

function renderVitalTiles() {
  const bp = latestOf('systolic');
  const sugar = latestOf('glucose');
  const pulse = latestOf('pulse');
  const weight = latestOf('weight_kg');
  const tile = (icon, label, value, unit, reading, status) => `
    <div class="stat-tile">
      <div class="stat-label"><span class="vital-icon">${icon}</span> ${esc(t(label))}</div>
      <div class="stat-value">${reading ? esc(value) : '–'} <span class="stat-note">${reading ? esc(unit) : ''}</span></div>
      <div class="stat-note">${reading ? esc(formatDateTime(reading.recorded_at)) : esc(t('noReading'))}</div>
      ${status ? `<div class="vital-status"><span class="badge lvl-${status[1]}">${esc(t(status[0]))}</span></div>` : ''}
    </div>`;
  document.getElementById('vitalsTiles').innerHTML = [
    tile('🩸', 'bp', bp ? `${bp.systolic}/${bp.diastolic}` : '', 'mmHg', bp, bp && bpStatus(bp.systolic, bp.diastolic)),
    tile('🍬', 'sugar', sugar ? Math.round(sugar.glucose) : '', 'mg/dL', sugar, sugar && sugarStatus(sugar.glucose, sugar.glucose_context)),
    tile('💓', 'pulse', pulse ? pulse.pulse : '', '/min', pulse, pulse && pulseStatus(pulse.pulse)),
    tile('⚖️', 'weight', weight ? weight.weight_kg : '', 'kg', weight, null)
  ].join('');
}

function renderHistory(rows) {
  const host = document.getElementById('historyList');
  if (!rows.length) {
    host.innerHTML = `<p class="empty-state">${esc(t('noHistory'))}</p>`;
    return;
  }
  host.innerHTML = rows.slice(0, 15).map((v) => {
    const parts = [];
    if (v.systolic) parts.push(`${t('bp')} ${v.systolic}/${v.diastolic}`);
    if (v.glucose) parts.push(`${t('sugar')} ${Math.round(v.glucose)}`);
    if (v.pulse) parts.push(`${t('pulse')} ${v.pulse}`);
    if (v.weight_kg) parts.push(`${t('weight')} ${v.weight_kg} kg`);
    return `<div class="list-item"><div class="list-main reading-row">
      <span class="list-title">${esc(parts.join(' · '))}</span>
      <span class="list-meta">${esc(formatDateTime(v.recorded_at))}${v.source === 'ASHA' ? ' · ASHA' : ''}</span></div></div>`;
  }).join('');
}

function renderReferrals(rows) {
  const host = document.getElementById('referralList');
  if (!rows.length) {
    host.innerHTML = `<p class="empty-state">${esc(t('noReferrals'))}</p>`;
    return;
  }
  const urgency = t('urgencyLevels');
  host.innerHTML = rows.map((r) => {
    const h = r.hospital || {};
    const maps = mapsLink(h.lat, h.lon, h.name);
    return `<div class="list-item"><div class="list-main">
      <div class="list-title">${esc(h.name)} ${levelBadge(r.urgency)}</div>
      <div class="list-meta">${esc(h.level || '')}${h.distance_km != null ? ` · ${esc(h.distance_km)} km` : ''}</div>
      ${h.address ? `<div class="list-meta">📍 ${esc(h.address)}</div>` : ''}
      <div class="list-meta"><strong>${esc(t('urgency'))}:</strong> ${esc(urgency[r.urgency] || r.urgency)}${r.reason ? ` · <strong>${esc(t('reason'))}:</strong> ${esc(r.reason)}` : ''}</div>
      <div class="list-meta">${esc(t('referredOn'))}: ${esc(formatDateTime(r.created_at))}</div>
      <div class="btn-row" style="margin-top:10px;">
        ${telLink(h.phone, t('callHospital'))}
        ${maps ? `<a class="btn btn-ghost btn-call" href="${esc(maps)}" target="_blank" rel="noopener">🧭 ${esc(t('directions'))}</a>` : ''}
        <a class="btn sos-btn btn-call" href="tel:108">🚑 108</a>
      </div>
    </div></div>`;
  }).join('');
}

function renderReports(rows) {
  const unread = rows.filter((r) => !r.read_at).length + (dashboard.referrals || []).filter((r) => r.status === 'REFERRED' && isRecent(r.created_at)).length;
  const badge = document.getElementById('reportsCount');
  badge.textContent = unread;
  badge.classList.toggle('hidden', unread === 0);
  const host = document.getElementById('reportList');
  if (!rows.length) {
    host.innerHTML = `<p class="empty-state">${esc(t('noReports'))}</p>`;
    return;
  }
  host.innerHTML = rows.map((r) => `
    <div class="list-item"><div class="list-main">
      <div class="list-title">${esc(r.title)} ${r.read_at ? '' : `<span class="badge lvl-PENDING">${esc(t('new'))}</span>`}</div>
      <div class="list-meta">${esc(r.doctor_name)}${r.facility ? ` · ${esc(r.facility)}` : ''} · ${esc(formatDateTime(r.created_at))}</div>
      <p style="margin-top:8px; font-size:14.5px; line-height:1.55;">${esc(r.summary)}</p>
      <div class="msg-actions"><button type="button" class="btn btn-ghost btn-sm" data-read-aloud="${esc(r.id)}">🔊 ${esc(t('readAloud'))}</button></div>
    </div></div>`).join('');
  host.querySelectorAll('[data-read-aloud]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const r = rows.find((x) => x.id === btn.dataset.readAloud);
      speak(`${r.title}. ${r.summary}`, detectLanguage(r.summary, uiLang));
    });
  });
}

function isRecent(ts) {
  return Date.now() - new Date(ts.replace(' ', 'T')).getTime() < 3 * 86400000;
}

async function markReportsRead() {
  if (!dashboard) return;
  const unread = dashboard.reports.filter((r) => !r.read_at);
  await Promise.all(unread.map((r) => api(`/api/v1/me/reports/${r.id}/read`, {}).catch(() => {})));
  if (unread.length) {
    unread.forEach((r) => { r.read_at = 'now'; });
    document.getElementById('reportsCount').classList.add('hidden');
  }
}

// ================= 3. MEDICINE & READINGS =================
async function saveDose(status) {
  try {
    const res = await api('/api/v1/me/dose', { status });
    dashboard.today_dose = status;
    dashboard.patient = res.patient;
    renderAll();
    showToast(res.alerted_health_team ? t('teamAlerted') : t('doseSaved'));
  } catch (err) {
    showToast(err.message);
  }
}

// ================= 4. HEALTH ASSISTANT =================
function setupAssistant() {
  const panel = document.getElementById('assistantPanel');
  const input = document.getElementById('chatInput');
  document.getElementById('assistantFab').addEventListener('click', () => {
    panel.classList.remove('hidden');
    if (!chatLoaded) loadChat();
    input.focus();
  });
  document.getElementById('assistantClose').addEventListener('click', () => {
    panel.classList.add('hidden');
    if ('speechSynthesis' in window) speechSynthesis.cancel();
  });

  const speakBtn = document.getElementById('speakToggle');
  speakBtn.setAttribute('aria-pressed', String(speakReplies));
  speakBtn.addEventListener('click', () => {
    speakReplies = !speakReplies;
    speakBtn.setAttribute('aria-pressed', String(speakReplies));
    try { localStorage.setItem('arogya_speak', speakReplies ? 'on' : 'off'); } catch (e) { /* ignore */ }
    if (!speakReplies && 'speechSynthesis' in window) speechSynthesis.cancel();
  });

  renderLanguageChips(document.getElementById('chatLangs'), chatLang, (code) => {
    chatLang = code;
    renderSuggestions();
    api('/api/v1/me/language', { language: code }).catch(() => {});
  });
  renderSuggestions();

  attachDictation(document.getElementById('chatMic'), input, () => chatLang, (text) => sendChat(text));
  document.getElementById('chatForm').addEventListener('submit', (e) => {
    e.preventDefault();
    sendChat(input.value.trim());
  });
}

function renderSuggestions() {
  const host = document.getElementById('chatSuggestions');
  host.innerHTML = (SUGGESTIONS[chatLang] || SUGGESTIONS.en).map((s) => `<button type="button">${esc(s)}</button>`).join('');
  host.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => sendChat(b.textContent)));
}

async function loadChat() {
  chatLoaded = true;
  try {
    const history = await api('/api/v1/me/chat');
    history.forEach((m) => appendMessage(m.role, m.content, Boolean(m.flagged), m.language));
  } catch (err) {
    showToast(err.message);
  }
}

function appendMessage(role, text, emergency, lang) {
  const log = document.getElementById('chatLog');
  const div = document.createElement('div');
  div.className = `msg msg-${role}${emergency ? ' msg-emergency' : ''}`;
  div.textContent = text;
  if (role === 'assistant') {
    const actions = document.createElement('div');
    actions.className = 'msg-actions';
    actions.innerHTML = `${emergency ? '<a class="btn sos-btn" href="tel:108">🚑 108</a>' : ''}
      <button type="button" class="btn btn-ghost">🔊 ${esc(t('readAloud'))}</button>`;
    actions.querySelector('button').addEventListener('click', () => speak(text, lang || chatLang));
    div.appendChild(actions);
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

let voiceWarningShown = false;

async function sendChat(text) {
  if (!text) return;
  const input = document.getElementById('chatInput');
  const send = document.getElementById('chatSend');
  const lang = detectLanguage(text, chatLang);
  input.value = '';
  send.disabled = true;
  appendMessage('user', text);
  const typing = appendMessage('assistant-typing', t('thinking'));
  typing.className = 'msg msg-assistant msg-typing';
  try {
    const res = await api('/api/v1/me/chat', { message: text, language: lang });
    typing.remove();
    appendMessage('assistant', res.reply, res.emergency, lang);
    if (speakReplies || res.emergency) {
      const spoken = await speak(res.reply, lang);
      if (!spoken && !voiceWarningShown) {
        voiceWarningShown = true;
        showToast(t('voiceMissing'));
      }
    }
  } catch (err) {
    typing.remove();
    showToast(err.message);
  } finally {
    send.disabled = false;
  }
}
