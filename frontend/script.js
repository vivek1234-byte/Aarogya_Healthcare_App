// ArogyaSaathi Login Logic

document.addEventListener('DOMContentLoaded', () => {
  // 1. Element Selectors
  const pillPatient = document.getElementById('pillPatient');
  const pillOther = document.getElementById('pillOther');
  const otherLoginSection = document.getElementById('otherLoginSection');
  const inputMobile = document.getElementById('inputMobile');
  const inputPassword = document.getElementById('inputPassword');
  const toggleEye = document.getElementById('toggleEye');
  const loginForm = document.getElementById('loginForm');
  const roleButtons = document.querySelectorAll('.role-btn');

  let currentLoginType = 'patient'; // 'patient' or 'other'
  let selectedOtherRole = 'Health Worker';

  // 2. Toggle Login Type (Patient / Family vs Other Login)
  pillPatient.addEventListener('click', () => {
    currentLoginType = 'patient';
    pillPatient.classList.add('active');
    pillOther.classList.remove('active');

    // RULE: "Patient / Family" hides the other login role options
    otherLoginSection.classList.add('hidden');

    inputMobile.placeholder = 'Mobile Number';
    inputMobile.value = '9876543210';
  });

  pillOther.addEventListener('click', () => {
    currentLoginType = 'other';
    pillOther.classList.add('active');
    pillPatient.classList.remove('active');

    // RULE: "Other Login" reveals the other login role options
    otherLoginSection.classList.remove('hidden');

    inputMobile.placeholder = 'Worker ID / Mobile Number';
    selectRole('Health Worker', 'ASHA-RAMPUR-7821');
  });

  // 3. Select Role in Other Login Options (Health Worker, Doctor, Health Officer)
  roleButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const roleName = btn.getAttribute('data-role');
      const defaultId = btn.getAttribute('data-id');
      selectRole(roleName, defaultId);
    });
  });

  function selectRole(roleName, defaultId) {
    selectedOtherRole = roleName;

    roleButtons.forEach((btn) => {
      if (btn.getAttribute('data-role') === roleName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    inputMobile.value = defaultId;
    inputMobile.placeholder = `${roleName} ID / Mobile Number`;
  }

  // 4. Password Show / Hide Visibility Toggle
  toggleEye.addEventListener('click', () => {
    if (inputPassword.type === 'password') {
      inputPassword.type = 'text';
      toggleEye.textContent = '👁️';
    } else {
      inputPassword.type = 'password';
      toggleEye.textContent = '👁️‍🗨️';
    }
  });

  // 5. Form Submission Handler
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const mobileOrId = inputMobile.value.trim();
    const password = inputPassword.value;

    if (!mobileOrId || !password) {
      alert('Please fill in both fields.');
      return;
    }

    if (currentLoginType === 'patient') {
      sessionStorage.setItem('meditek_logged_in', 'true');
      window.location.href = 'patient_dashboard.html';
    } else {
      alert(`🎉 Logged In as ${selectedOtherRole}\n• Identifier: ${mobileOrId}\n• Session Authenticated under DPDP Act 2023`);
    }
  });
});
