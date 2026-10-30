/**
 * AROGYASAATHI - DOCTOR (PHC / TELEMEDICINE HUB) CONTROLLER
 * Escalation queue with one-page summaries, agree/override review saved as
 * labelled feedback, patient trends with notes to the patient, and the audit trail.
 */

const DOCTOR = requireRole('DOCTOR');

let escalations = [];
let queueFilter = 'PENDING';
let selectedCaseId = null;
let patients = [];
let selectedTrendId = null;

const SOURCE_TEXT = { TRIAGE: 'Voice triage', CHRONIC: 'Chronic care', CHAT: 'Patient chat' };
const LEVEL_ORDER = { EMERGENCY: 0, CRITICAL: 1, REFER: 2, HIGH: 3 };

document.addEventListener('DOMContentLoaded', () => {
  if (!DOCTOR) return;
  setupTabs((tab) => {
    if (tab === 'audit') refreshAudit();
    if (tab === 'patients') loadPatients();
    if (tab === 'queue') loadEscalations();
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
  document.addEventListener('click', async (ev) => {
    if (ev.target.closest('#delCaseBtn')) {
      if (await confirmAndDelete(`/api/v1/escalations/${selectedCaseId}/delete`, 'Delete this reviewed case? The review will no longer count as labelled data.')) {
        selectedCaseId = null;
        loadEscalations();
      }
    }
    if (ev.target.closest('#delPatientBtn')) {
      const p = patients.find((x) => x.id === selectedTrendId);
      if (p && await confirmAndDelete(`/api/v1/doctor/patients/${p.id}/delete`,
        `Delete ${p.name || p.pseudonym}'s record for good? Readings, notes, referrals, chat and their cases are erased. This cannot be undone.`)) {
        selectedTrendId = null;
        await loadPatients();
        loadEscalations();
      }
    }
  });
  loadEscalations();
  if (window.location.hash === '#audit') refreshAudit();
  if (window.location.hash === '#patients') loadPatients();
  // New escalations arrive while the doctor keeps the queue open
  setInterval(() => { if (document.getElementById('view-queue').classList.contains('active')) loadEscalations(); }, 60000);
});

// ================= 1. ESCALATION QUEUE =================
async function loadEscalations() {
  try {
    escalations = await api('/api/v1/escalations');
  } catch (err) {
    document.getElementById('queueList').innerHTML = `<p class="empty-state">${esc(err.message)}</p>`;
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

function renderQueue() {
  const list = document.getElementById('queueList');
  const items = escalations
    .filter((e) => queueFilter === 'ALL' || e.status === queueFilter)
    .sort((a, b) => (LEVEL_ORDER[a.level] ?? 9) - (LEVEL_ORDER[b.level] ?? 9) || b.created_at.localeCompare(a.created_at));
  if (!items.length) {
    list.innerHTML = `<p class="empty-state">${queueFilter === 'PENDING' ? 'No pending escalations.' : 'Nothing here yet.'}</p>`;
    selectedCaseId = null;
    renderCase();
    return;
  }
  if (!selectedCaseId || !items.some((e) => e.id === selectedCaseId)) selectedCaseId = items[0].id;
  list.innerHTML = items.map((e) => {
    const p = e.details.patient || {};
    return `
    <button type="button" class="list-item ${e.id === selectedCaseId ? 'selected' : ''}" data-id="${esc(e.id)}">
      <div class="list-main">
        <div class="list-title">${esc(e.title)}</div>
        <div class="list-meta">${e.patient_name ? `<strong>${esc(e.patient_name)}</strong> · ` : ''}${esc(e.pseudonym)} · ${esc(p.age ?? '')} yrs / ${esc(p.gender ?? '')} · ${esc(e.village_name)}</div>
        <div class="list-meta">${esc(SOURCE_TEXT[e.source] || e.source)} · ${esc(formatDateTime(e.created_at))}</div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end;">
        ${levelBadge(e.level)}
        ${levelBadge(e.status)}
      </div>
    </button>`;
  }).join('');
  list.querySelectorAll('.list-item').forEach((item) => {
    item.addEventListener('click', () => {
      selectedCaseId = item.dataset.id;
      renderQueue();
      if (window.innerWidth < 1100) document.getElementById('caseDetail').scrollIntoView({ behavior: 'smooth' });
    });
  });
  renderCase();
}

function overrideOptions(e) {
  return e.source === 'CHRONIC' ? ['CRITICAL', 'HIGH', 'MODERATE', 'LOW'] : ['EMERGENCY', 'REFER', 'TREAT_LOCALLY', 'HOME_CARE'];
}

function renderCase() {
  const host = document.getElementById('caseDetail');
  const e = escalations.find((x) => x.id === selectedCaseId);
  if (!e) {
    host.innerHTML = '<div class="panel"><p class="empty-state">Select a case to review.</p></div>';
    return;
  }
  const d = e.details;
  const p = d.patient || {};
  const ref = d.referral;

  const reviewBlock = e.review ? `
    <div class="panel">
      <div class="panel-title">Review ${levelBadge('REVIEWED')}</div>
      <div class="notice ${e.review.decision === 'AGREE' ? 'notice-green' : 'notice-amber'}" style="margin-top: 10px;">
        <span>${e.review.decision === 'AGREE' ? '✅' : '✏️'}</span>
        <span><strong>${e.review.decision === 'AGREE' ? 'Agreed' : 'Overridden'}</strong>: system said ${esc(LEVEL_TEXT[e.level])}, final ${esc(LEVEL_TEXT[e.review.final_level] || e.review.final_level)}.
        ${e.review.note ? `<br>Note: ${esc(e.review.note)}` : ''}<br>${esc(e.review.reviewer_name || e.review.reviewer)} · ${esc(formatDateTime(e.review.reviewed_at))}</span>
      </div>
      <div class="btn-row" style="margin-top: 12px;"><button type="button" class="btn btn-ghost btn-delete" id="delCaseBtn">🗑 Delete this case</button></div>
    </div>` : `
    <form class="panel" id="reviewForm">
      <div class="panel-title">Your review</div>
      <div class="panel-sub">Saved to the audit trail and as a labelled case.</div>
      <div class="form-group">
        <div class="segmented" id="reviewDecision">
          <button type="button" class="active" data-decision="AGREE">Agree: ${esc(LEVEL_TEXT[e.level])}</button>
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
        <textarea id="reviewNote" class="form-textarea" placeholder="e.g. Bring the patient to the PHC tomorrow morning."></textarea>
      </div>
      <button type="submit" class="btn btn-primary btn-block">Submit Review</button>
    </form>`;

  host.innerHTML = `
    <div class="panel">
      <div class="view-head" style="margin-bottom: 10px;">
        <div>
          <div class="panel-title">${esc(e.title)}</div>
          <div class="list-meta">${e.patient_name ? `<strong>${esc(e.patient_name)}</strong> · ` : ''}${esc(e.pseudonym)} · ${esc(e.id)} · ${esc(p.age ?? '')} yrs / ${esc(p.gender ?? '')} · ${esc(e.village_name)}</div>
        </div>
        ${levelBadge(e.level)}
      </div>
      <div class="notice ${['EMERGENCY', 'CRITICAL'].includes(e.level) ? 'notice-red' : 'notice-amber'}"><span>📋</span><span>${esc(e.rationale)}</span></div>
      ${d.flags && d.flags.length ? `<div class="list-flags" style="margin-top: 12px;">${d.flags.map((f) => `<span class="chip chip-red">${esc(prettyCode(f))}</span>`).join('')}</div>` : ''}
      ${ref ? `<div class="notice notice-blue" style="margin-top: 12px;"><span>🏥</span><span>Referred by ASHA to <strong>${esc(ref.hospital.name)}</strong> (${esc(ref.hospital.level || '')}) · ${esc(LEVEL_TEXT[ref.urgency] || ref.urgency)}${ref.hospital.phone ? ` · 📞 ${esc(ref.hospital.phone)}` : ''}</span></div>` : ''}
      ${d.transcripts && d.transcripts.length ? `
        <div class="decision-section"><h4>What the patient said</h4>
          ${d.transcripts.map((tx) => `<div class="turn turn-input" style="margin-bottom: 6px;">${esc(tx)}</div>`).join('')}
        </div>` : ''}
      ${d.trend ? `
        <div class="grid-2" style="margin-top: 14px;">
          <div><div class="panel-title">Blood pressure</div><div class="chart-box" id="caseBpChart"></div></div>
          <div><div class="panel-title">Sugar</div><div class="chart-box" id="caseSugarChart"></div></div>
        </div>
        <div style="margin-top: 10px;"><div class="panel-title">Medicine doses</div><div id="caseDoseStrip"></div></div>` : ''}
    </div>

    <div class="panel">
      <div class="panel-title">One-page summary ${d.summary_seconds !== undefined ? `<span class="badge badge-plain">Generated in ${esc(d.summary_seconds)} s</span>` : ''}</div>
      <div class="summary-doc" style="margin-top: 10px;">${renderMarkdown(d.summary_markdown)}</div>
      <div class="btn-row" style="margin-top: 12px;">
        <button type="button" class="btn btn-ghost" id="printSummaryBtn">🖨️ Print summary</button>
        ${e.patient_id ? '<button type="button" class="btn btn-ghost" id="notePatientBtn">✉️ Send note to patient</button>' : ''}
      </div>
    </div>

    ${reviewBlock}`;

  if (d.trend) {
    renderTrendCharts(d.trend, document.getElementById('caseBpChart'), document.getElementById('caseSugarChart'));
    const doses = d.dose_strip || { doses: [], days: [] };
    renderDoseStrip(document.getElementById('caseDoseStrip'), doses.doses, doses.days);
  }

  document.getElementById('printSummaryBtn').addEventListener('click', () => {
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`<html><head><title>${esc(e.id)} summary</title><link rel="stylesheet" href="app.css"></head><body style="padding:24px;background:#fff"><div class="summary-doc" style="max-height:none">${renderMarkdown(d.summary_markdown)}</div></body></html>`);
    w.document.close();
    w.onload = () => w.print();
  });
  const noteBtn = document.getElementById('notePatientBtn');
  if (noteBtn) {
    noteBtn.addEventListener('click', async () => {
      if (!patients.length) await loadPatients(false);
      selectedTrendId = e.patient_id;
      switchTab('patients', () => renderTrendList());
      document.getElementById('noteTitle')?.focus();
    });
  }

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
          note: document.getElementById('reviewNote').value.trim()
        });
        showToast(decision === 'AGREE' ? 'Review saved' : 'Override saved and logged');
        await loadEscalations();
      } catch (err) {
        showToast(err.message);
      }
    });
  }
}

// ================= 2. PATIENT TRENDS & NOTES =================
async function loadPatients(render = true) {
  try {
    patients = await api('/api/v1/doctor/patients');
  } catch (err) {
    document.getElementById('trendList').innerHTML = `<p class="empty-state">${esc(err.message)}</p>`;
    return;
  }
  if (!selectedTrendId && patients.length) selectedTrendId = patients[0].id;
  if (render) renderTrendList();
}

function renderTrendList() {
  const list = document.getElementById('trendList');
  if (!patients.length) {
    list.innerHTML = '<p class="empty-state">No patients registered yet.</p>';
    document.getElementById('trendDetail').innerHTML = '<p class="empty-state">No patient selected.</p>';
    return;
  }
  list.innerHTML = patients.map((p) => `
    <button type="button" class="list-item ${p.id === selectedTrendId ? 'selected' : ''}" data-id="${esc(p.id)}">
      <div class="list-main">
        <div class="list-title">${esc(p.name || p.pseudonym)}</div>
        <div class="list-meta">${esc(p.pseudonym)} · ${esc(p.age)} yrs / ${esc(p.gender)} · ${esc(p.village_name)} · ${esc(p.conditions.join(', ') || '—')}</div>
      </div>
      ${levelBadge(p.risk.risk_level)}
    </button>`).join('');
  list.querySelectorAll('.list-item').forEach((item) => {
    item.addEventListener('click', () => {
      selectedTrendId = item.dataset.id;
      renderTrendList();
      if (window.innerWidth < 1100) document.getElementById('trendDetail').scrollIntoView({ behavior: 'smooth' });
    });
  });

  const p = patients.find((x) => x.id === selectedTrendId);
  const host = document.getElementById('trendDetail');
  if (!p) return;
  const r = p.risk;
  host.innerHTML = `
    <div class="view-head" style="margin-bottom: 10px;">
      <div>
        <div class="panel-title">${esc(p.name || p.pseudonym)} ${levelBadge(r.risk_level)}</div>
        <div class="list-meta">${esc(p.pseudonym)} · ${esc(p.conditions.join(', ') || 'No condition recorded')}${p.next_visit ? ` · Next visit ${esc(p.next_visit)}` : ''}
          ${r.risk_level !== 'NO_DATA' ? ` · Avg BP ${esc(r.average_systolic ?? '–')}/${esc(r.average_diastolic ?? '–')} · Avg sugar ${esc(r.average_glucose ?? '–')} · Adherence ${esc(r.adherence_rate_pct)}%` : ''}</div>
      </div>
      <button type="button" class="btn btn-ghost btn-delete" id="delPatientBtn">🗑 Delete record</button>
    </div>
    <div class="list-flags" style="margin-bottom: 12px;">${r.flags.map((f) => `<span class="chip chip-red">${esc(prettyCode(f))}</span>`).join('') || '<span class="chip">No flags</span>'}</div>
    <div class="grid-2">
      <div><div class="panel-title">Blood pressure</div><div class="chart-box" id="trendBpChart"></div></div>
      <div><div class="panel-title">Sugar</div><div class="chart-box" id="trendSugarChart"></div></div>
    </div>
    <div style="margin-top: 10px;"><div class="panel-title">Medicine doses</div><div id="trendDoseStrip"></div></div>

    <form id="noteForm" style="margin-top: 20px; border-top: 1px solid var(--border-light); padding-top: 16px;">
      <div class="panel-title">✉️ Send a note to this patient</div>
      <div class="panel-sub">The patient sees it under "Doctor &amp; Hospital" and can have it read aloud. Write in the patient's language if you can.</div>
      <div class="form-row two-col">
        <div class="form-group">
          <label for="noteTitle">Title</label>
          <input id="noteTitle" class="form-input" placeholder="e.g. BP review" required>
        </div>
        <div class="form-group">
          <label for="noteCategory">Type</label>
          <select id="noteCategory" class="form-select">
            <option>Advice</option>
            <option>Lab result</option>
            <option>Follow-up visit</option>
            <option>Prescription (visit PHC to collect)</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label for="noteBody">Note</label>
        <textarea id="noteBody" class="form-textarea" placeholder="e.g. Your BP is high. Please come to the PHC on Monday morning." required></textarea>
      </div>
      <button type="submit" class="btn btn-primary">Send to patient</button>
    </form>`;
  renderTrendCharts(p.trend, document.getElementById('trendBpChart'), document.getElementById('trendSugarChart'));
  renderDoseStrip(document.getElementById('trendDoseStrip'), p.dose_strip.doses, p.dose_strip.days);
  document.getElementById('noteForm').addEventListener('submit', async (ev) => {
    ev.preventDefault();
    try {
      await api('/api/v1/doctor/reports', {
        patient_id: p.id,
        title: document.getElementById('noteTitle').value.trim(),
        category: document.getElementById('noteCategory').value,
        summary: document.getElementById('noteBody').value.trim()
      });
      ev.target.reset();
      showToast('Sent to the patient');
    } catch (err) {
      showToast(err.message);
    }
  });
}

// ================= 3. AUDIT =================
function refreshAudit() {
  loadAuditTrail(document.getElementById('auditBody'), document.getElementById('auditStatus'));
}
