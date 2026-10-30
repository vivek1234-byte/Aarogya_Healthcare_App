/**
 * AROGYASAATHI - DOCTOR (PHC / TELEMEDICINE HUB) CONTROLLER
 * Escalation queue with one-page summaries, agree/override review saved as
 * labelled feedback, chronic patient trends and the audit trail.
 */

const DOCTOR_ID = requireStaffRole('Doctor');

let escalations = [];
let queueFilter = 'PENDING';
let selectedCaseId = null;
let patients = [];
let selectedTrendId = null;

document.addEventListener('DOMContentLoaded', () => {
  if (!DOCTOR_ID) return;
  setupTabs((tab) => {
    if (tab === 'audit') refreshAudit();
    if (tab === 'patients') loadPatients();
  });

  document.querySelectorAll('#queueFilter button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#queueFilter button').forEach((b) => b.classList.toggle('active', b === btn));
      queueFilter = btn.dataset.filter;
      renderQueue();
    });
  });
  document.getElementById('refreshQueueBtn').addEventListener('click', loadEscalations);
  document.getElementById('refreshAuditBtn').addEventListener('click', refreshAudit);

  loadEscalations();
  if (window.location.hash === '#audit') refreshAudit();
  if (window.location.hash === '#patients') loadPatients();
});

// ================= 1. ESCALATION QUEUE =================
async function loadEscalations() {
  try {
    escalations = await api('/api/v1/escalations');
  } catch (err) {
    document.getElementById('queueList').innerHTML = `<p class="empty-state">Could not load escalations: ${esc(err.message)}</p>`;
    return;
  }
  renderStats();
  renderQueue();
}

function renderStats() {
  const pending = escalations.filter((e) => e.status === 'PENDING');
  const reviewed = escalations.filter((e) => e.review);
  const agreed = reviewed.filter((e) => e.review.decision === 'AGREE').length;
  document.getElementById('statPending').textContent = pending.length;
  document.getElementById('statEmergency').textContent = pending.filter((e) => ['EMERGENCY', 'CRITICAL'].includes(e.level)).length;
  document.getElementById('statLabelled').textContent = reviewed.length;
  document.getElementById('statAgreement').textContent = reviewed.length ? `${Math.round((agreed / reviewed.length) * 100)}%` : '–';
  const count = document.getElementById('pendingCount');
  count.textContent = pending.length;
  count.classList.toggle('hidden', pending.length === 0);
}

const LEVEL_ORDER = { EMERGENCY: 0, CRITICAL: 1, REFER: 2, HIGH: 3 };

function renderQueue() {
  const list = document.getElementById('queueList');
  const items = escalations
    .filter((e) => queueFilter === 'ALL' || e.status === queueFilter)
    .sort((a, b) => (LEVEL_ORDER[a.level] ?? 9) - (LEVEL_ORDER[b.level] ?? 9));
  if (!items.length) {
    list.innerHTML = `<p class="empty-state">${queueFilter === 'PENDING' ? 'No pending escalations. 🎉' : 'Nothing here yet.'}</p>`;
    selectedCaseId = null;
    renderCase();
    return;
  }
  if (!selectedCaseId || !items.some((e) => e.id === selectedCaseId)) selectedCaseId = items[0].id;
  list.innerHTML = items.map((e) => `
    <button type="button" class="list-item ${e.id === selectedCaseId ? 'selected' : ''}" data-id="${esc(e.id)}">
      <div class="list-main">
        <div class="list-title">${esc(e.title)}</div>
        <div class="list-meta">${esc(e.patient.pseudonym)} · ${esc(e.patient.age)} yrs / ${esc(e.patient.gender)} · ${esc(e.patient.village_name)}</div>
        <div class="list-meta">${esc(e.id)} · ${esc(e.source === 'TRIAGE' ? 'Voice triage' : 'Chronic care')} · ${esc(e.created_at)}</div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end;">
        ${levelBadge(e.level)}
        ${levelBadge(e.status)}
      </div>
    </button>`).join('');
  list.querySelectorAll('.list-item').forEach((item) => {
    item.addEventListener('click', () => {
      selectedCaseId = item.dataset.id;
      renderQueue();
    });
  });
  renderCase();
}

function overrideOptions(e) {
  return e.source === 'TRIAGE'
    ? ['EMERGENCY', 'REFER', 'TREAT_LOCALLY', 'HOME_CARE']
    : ['CRITICAL', 'HIGH', 'MODERATE', 'LOW'];
}

function renderCase() {
  const host = document.getElementById('caseDetail');
  const e = escalations.find((x) => x.id === selectedCaseId);
  if (!e) {
    host.innerHTML = '<div class="panel"><p class="empty-state">Select a case to review.</p></div>';
    return;
  }

  const reviewBlock = e.review ? `
    <div class="panel">
      <div class="panel-title">Your review ${levelBadge('REVIEWED')}</div>
      <div class="notice ${e.review.decision === 'AGREE' ? 'notice-green' : 'notice-amber'}" style="margin-top: 10px;">
        <span>${e.review.decision === 'AGREE' ? '✅' : '✏️'}</span>
        <span><strong>${e.review.decision === 'AGREE' ? 'Agreed' : 'Overridden'}</strong>: system said ${esc(LEVEL_TEXT[e.level])}, final ${esc(LEVEL_TEXT[e.review.final_level] || e.review.final_level)}.
        ${e.review.note ? `<br>Note: ${esc(e.review.note)}` : ''}<br>${esc(e.review.reviewer)} · ${esc(e.review.reviewed_at)}</span>
      </div>
    </div>` : `
    <form class="panel" id="reviewForm">
      <div class="panel-title">Your review</div>
      <div class="panel-sub">Saved to the audit trail and as a labelled case.</div>
      <div class="form-group">
        <div class="segmented" id="reviewDecision">
          <button type="button" class="active" data-decision="AGREE">Agree with ${esc(LEVEL_TEXT[e.level])}</button>
          <button type="button" data-decision="OVERRIDE">Override</button>
        </div>
      </div>
      <div class="form-group hidden" id="overrideGroup">
        <label for="overrideLevel">Correct level</label>
        <select id="overrideLevel" class="form-select">
          ${overrideOptions(e).filter((l) => l !== e.level).map((l) => `<option value="${l}">${esc(LEVEL_TEXT[l])}</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label for="reviewNote">Clinical note / instructions for the health worker</label>
        <textarea id="reviewNote" class="form-textarea" placeholder="e.g. Bring patient to PHC tomorrow morning for examination."></textarea>
      </div>
      <button type="submit" class="btn btn-primary btn-block">Submit Review</button>
    </form>`;

  host.innerHTML = `
    <div class="panel">
      <div class="view-head" style="margin-bottom: 10px;">
        <div>
          <div class="panel-title">${esc(e.title)}</div>
          <div class="list-meta">${esc(e.id)} · ${esc(e.patient.pseudonym)} · ${esc(e.patient.age)} yrs / ${esc(e.patient.gender)} · ${esc(e.patient.village_name)}</div>
        </div>
        ${levelBadge(e.level)}
      </div>
      <div class="notice ${['EMERGENCY', 'CRITICAL'].includes(e.level) ? 'notice-red' : 'notice-amber'}"><span>📋</span><span>${esc(e.rationale)}</span></div>
      ${e.flags && e.flags.length ? `<div class="list-flags" style="margin-top: 12px;">${e.flags.map((f) => `<span class="chip chip-red">${esc(prettyCode(f))}</span>`).join('')}</div>` : ''}
      ${e.transcripts && e.transcripts.length ? `
        <div class="decision-section"><h4>What the patient said</h4>
          ${e.transcripts.map((t) => `<div class="turn turn-input" style="margin-bottom: 6px;">${esc(t)}</div>`).join('')}
        </div>` : ''}
      ${e.trend ? `
        <div class="grid-2" style="margin-top: 14px;">
          <div><div class="panel-title">Blood pressure</div><div class="chart-box" id="caseBpChart"></div></div>
          <div><div class="panel-title">Fasting sugar</div><div class="chart-box" id="caseSugarChart"></div></div>
        </div>
        <div style="margin-top: 10px;"><div class="panel-title">Medicine doses</div><div id="caseDoseStrip"></div></div>` : ''}
    </div>

    <div class="panel">
      <div class="panel-title">One-page summary ${e.summary_seconds !== undefined ? `<span class="badge badge-plain">Generated in ${esc(e.summary_seconds)} s</span>` : ''}</div>
      <div class="summary-doc" style="margin-top: 10px;">${renderMarkdown(e.summary_markdown)}</div>
      <div class="btn-row" style="margin-top: 12px;">
        <button type="button" class="btn btn-ghost" id="printSummaryBtn">🖨️ Print summary</button>
      </div>
    </div>

    ${reviewBlock}`;

  if (e.trend) renderTrendCharts(e.trend, 'caseBpChart', 'caseSugarChart', 'caseDoseStrip');

  document.getElementById('printSummaryBtn').addEventListener('click', () => {
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`<html><head><title>${esc(e.id)} summary</title><link rel="stylesheet" href="staff.css"></head><body style="padding:24px;background:#fff"><div class="summary-doc" style="max-height:none">${renderMarkdown(e.summary_markdown)}</div></body></html>`);
    w.document.close();
    w.onload = () => w.print();
  });

  const form = document.getElementById('reviewForm');
  if (form) {
    document.querySelectorAll('#reviewDecision button').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#reviewDecision button').forEach((b) => b.classList.toggle('active', b === btn));
        document.getElementById('overrideGroup').classList.toggle('hidden', btn.dataset.decision !== 'OVERRIDE');
      });
    });
    form.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const decision = document.querySelector('#reviewDecision button.active').dataset.decision;
      try {
        await api(`/api/v1/escalations/${e.id}/review`, {
          decision,
          final_level: decision === 'OVERRIDE' ? document.getElementById('overrideLevel').value : e.level,
          note: document.getElementById('reviewNote').value.trim(),
          reviewer: DOCTOR_ID
        });
        showToast(decision === 'AGREE' ? 'Review saved' : 'Override saved and logged');
        await loadEscalations();
      } catch (err) {
        showToast(err.message);
      }
    });
  }
}

function renderTrendCharts(t, bpId, sugarId, doseId) {
  renderLineChart(document.getElementById(bpId), {
    labels: t.days,
    series: [
      { name: 'Systolic', color: '#EF4444', values: t.systolic },
      { name: 'Diastolic', color: '#3B82F6', values: t.diastolic }
    ],
    bands: [{ from: 140, to: 400, color: 'rgba(239, 68, 68, 0.06)' }],
    unit: ' mmHg'
  });
  renderLineChart(document.getElementById(sugarId), {
    labels: t.days,
    series: [{ name: 'Fasting glucose', color: '#10B981', values: t.glucose }],
    bands: [{ from: 126, to: 600, color: 'rgba(245, 158, 11, 0.08)' }],
    unit: ' mg/dL'
  });
  renderDoseStrip(document.getElementById(doseId), t.doses, t.days);
}

// ================= 2. PATIENT TRENDS =================
async function loadPatients() {
  try {
    patients = await api('/api/v1/worker/roster');
  } catch (err) {
    document.getElementById('trendList').innerHTML = `<p class="empty-state">Could not load patients: ${esc(err.message)}</p>`;
    return;
  }
  if (!selectedTrendId && patients.length) selectedTrendId = patients[0].id;
  renderTrendList();
}

function renderTrendList() {
  const list = document.getElementById('trendList');
  list.innerHTML = patients.map((p) => `
    <button type="button" class="list-item ${p.id === selectedTrendId ? 'selected' : ''}" data-id="${esc(p.id)}">
      <div class="list-main">
        <div class="list-title">${esc(p.pseudonym)}</div>
        <div class="list-meta">${esc(p.age)} yrs / ${esc(p.gender)} · ${esc(p.village_name)} · ${esc(p.condition)}</div>
      </div>
      ${levelBadge(p.risk.risk_level)}
    </button>`).join('');
  list.querySelectorAll('.list-item').forEach((item) => {
    item.addEventListener('click', () => {
      selectedTrendId = item.dataset.id;
      renderTrendList();
    });
  });

  const p = patients.find((x) => x.id === selectedTrendId);
  const host = document.getElementById('trendDetail');
  if (!p) return;
  const r = p.risk;
  host.innerHTML = `
    <div class="view-head" style="margin-bottom: 10px;">
      <div>
        <div class="panel-title">${esc(p.pseudonym)} ${levelBadge(r.risk_level)}</div>
        <div class="list-meta">${esc(p.condition)} · Next visit ${esc(p.next_visit)} · Avg BP ${esc(r.average_systolic)}/${esc(r.average_diastolic)} · Avg sugar ${esc(r.average_glucose)} · Adherence ${esc(r.adherence_rate_pct)}%</div>
      </div>
    </div>
    <div class="list-flags" style="margin-bottom: 12px;">${r.flags.map((f) => `<span class="chip chip-red">${esc(prettyCode(f))}</span>`).join('') || '<span class="chip">No flags</span>'}</div>
    <div class="grid-2">
      <div><div class="panel-title">Blood pressure</div><div class="chart-box" id="trendBpChart"></div></div>
      <div><div class="panel-title">Fasting sugar</div><div class="chart-box" id="trendSugarChart"></div></div>
    </div>
    <div style="margin-top: 10px;"><div class="panel-title">Medicine doses</div><div id="trendDoseStrip"></div></div>`;
  renderTrendCharts(p.trend, 'trendBpChart', 'trendSugarChart', 'trendDoseStrip');
}

// ================= 3. AUDIT =================
function refreshAudit() {
  loadAuditTrail(document.getElementById('auditBody'), document.getElementById('auditStatus'));
}
