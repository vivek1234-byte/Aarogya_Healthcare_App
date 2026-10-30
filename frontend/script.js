// ArogyaSaathi Login, patient activation and staff sign-up

const API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8080';
const ROLE_PAGES = {
  PATIENT: 'patient_dashboard.html',
  HEALTH_WORKER: 'health_worker.html',
  DOCTOR: 'doctor.html',
  HEALTH_OFFICER: 'officer.html'
};

let audience = 'patient';          // 'patient' | 'staff'
let staffRole = 'HEALTH_WORKER';
let gps = null;

const $ = (id) => document.getElementById(id);

async function post(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function saveSession({ token, user }) {
  try {
    localStorage.setItem('arogya_token', token);
    localStorage.setItem('arogya_user', JSON.stringify(user));
  } catch (e) { /* storage blocked: the session will last only this page */ }
  window.location.replace(ROLE_PAGES[user.role]);
}

function showError(message) {
  const box = $('formError');
  box.textContent = message;
  box.classList.toggle('hidden', !message);
}

function showForm(name) {
  ['loginForm', 'activateForm', 'signupForm'].forEach((id) => $(id).classList.toggle('hidden', id !== name));
  showError('');
  const titles = {
    loginForm: ['Welcome · स्वागत है', 'Log in to continue · लॉग इन करें'],
    activateForm: ['Activate account', 'खाता चालू करें'],
    signupForm: ['Create staff account', 'For ASHA / ANM, doctors and health officers']
  };
  $('formTitle').textContent = titles[name][0];
  $('formSubtitle').textContent = titles[name][1];
  $('audiencePills').classList.toggle('hidden', name !== 'loginForm');
}

function setAudience(next) {
  audience = next;
  $('pillPatient').classList.toggle('active', next === 'patient');
  $('pillStaff').classList.toggle('active', next === 'staff');
  $('staffRoles').classList.toggle('hidden', next !== 'staff');
  $('toActivate').classList.toggle('hidden', next !== 'patient');
  $('toSignup').classList.toggle('hidden', next !== 'staff');
  showError('');
}

function setStaffRole(role) {
  staffRole = role;
  document.querySelectorAll('.role-btn').forEach((b) => b.classList.toggle('active', b.dataset.role === role));
  $('suVillageBlock').classList.toggle('hidden', role !== 'HEALTH_WORKER');
  $('suFacilityBlock').classList.toggle('hidden', role !== 'DOCTOR');
}

async function withBusy(form, fn) {
  const btn = form.querySelector('.btn-submit');
  btn.disabled = true;
  showError('');
  try {
    await fn();
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
  }
}

async function loadVillages() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/public/villages`);
    const villages = await res.json();
    const select = $('suVillageSelect');
    select.innerHTML = villages.map((v) => `<option value="${v.id}">${v.name}, ${v.district}</option>`).join('')
      + '<option value="__new">+ Add my village</option>';
    select.value = villages.length ? villages[0].id : '__new';
    $('suNewVillage').classList.toggle('hidden', select.value !== '__new');
  } catch (e) { /* keep "Add my village" */ }
}

document.addEventListener('DOMContentLoaded', () => {
  // Already logged in on this device: go straight to the right page
  try {
    const user = JSON.parse(localStorage.getItem('arogya_user') || 'null');
    if (localStorage.getItem('arogya_token') && user && ROLE_PAGES[user.role]) {
      window.location.replace(ROLE_PAGES[user.role]);
      return;
    }
  } catch (e) { /* ignore */ }

  $('pillPatient').addEventListener('click', () => setAudience('patient'));
  $('pillStaff').addEventListener('click', () => setAudience('staff'));
  document.querySelectorAll('.role-btn').forEach((b) => b.addEventListener('click', () => setStaffRole(b.dataset.role)));
  $('toActivate').addEventListener('click', () => { $('actMobile').value = $('loginMobile').value; showForm('activateForm'); });
  $('toSignup').addEventListener('click', () => { showForm('signupForm'); loadVillages(); });
  document.querySelectorAll('[data-back]').forEach((b) => b.addEventListener('click', () => showForm('loginForm')));
  document.querySelectorAll('[data-eye]').forEach((b) => {
    b.addEventListener('click', () => {
      const input = $(b.dataset.eye);
      input.type = input.type === 'password' ? 'text' : 'password';
      b.textContent = input.type === 'password' ? '👁️' : '🙈';
    });
  });
  $('suVillageSelect').addEventListener('change', (e) => $('suNewVillage').classList.toggle('hidden', e.target.value !== '__new'));

  $('suGpsBtn').addEventListener('click', () => {
    if (!navigator.geolocation) {
      $('suGpsStatus').textContent = 'Location is not available on this device.';
      return;
    }
    $('suGpsStatus').textContent = 'Getting location…';
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        gps = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        $('suGpsStatus').textContent = `📍 Saved: ${gps.lat.toFixed(4)}, ${gps.lon.toFixed(4)}`;
      },
      (err) => { $('suGpsStatus').textContent = `Could not get location (${err.message}). You can continue without it.`; },
      { enableHighAccuracy: true, timeout: 15000 }
    );
  });

  $('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    withBusy(e.target, async () => {
      saveSession(await post('/api/v1/auth/login', {
        role: audience === 'patient' ? 'PATIENT' : staffRole,
        mobile: $('loginMobile').value,
        password: $('loginPassword').value
      }));
    });
  });

  $('activateForm').addEventListener('submit', (e) => {
    e.preventDefault();
    withBusy(e.target, async () => {
      saveSession(await post('/api/v1/auth/activate', {
        mobile: $('actMobile').value,
        code: $('actCode').value,
        password: $('actPassword').value
      }));
    });
  });

  $('signupForm').addEventListener('submit', (e) => {
    e.preventDefault();
    withBusy(e.target, async () => {
      const body = {
        role: staffRole,
        name: $('suName').value,
        mobile: $('suMobile').value,
        password: $('suPassword').value,
        access_code: $('suCode').value.trim(),
        facility: $('suFacility').value
      };
      if (staffRole === 'HEALTH_WORKER') {
        const selected = $('suVillageSelect').value;
        body.village = selected !== '__new'
          ? { id: selected }
          : {
            name: $('suVillageName').value, block: $('suBlock').value, district: $('suDistrict').value,
            state: $('suState').value, lat: gps && gps.lat, lon: gps && gps.lon
          };
      }
      saveSession(await post('/api/v1/auth/signup', body));
    });
  });

  setAudience('patient');
  setStaffRole('HEALTH_WORKER');
});

// Offline app shell (network first; see service-worker.js)
if ('serviceWorker' in navigator && window.location.protocol !== 'file:') {
  window.addEventListener('load', () => navigator.serviceWorker.register('service-worker.js').catch(() => {}));
}
