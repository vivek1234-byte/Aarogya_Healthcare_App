import base64
import os

with open('frontend/web/assets/exact_top_hero.jpg', 'rb') as f:
    exact_top_hero_b64 = base64.b64encode(f.read()).decode()

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ArogyaSaathi (आरोग्य साथी) • Healthcare and Public Health Access</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
    
    body {{
      font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }}
    
    @keyframes fadeInSlide {{
      0% {{ opacity: 0; transform: translateY(8px); }}
      100% {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes radarSweep {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}
    .animate-fade-in {{
      animation: fadeInSlide 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    .radar-sweep {{
      transform-origin: center center;
      animation: radarSweep 4s linear infinite;
    }}
    .phone-chassis {{
      box-shadow: 0 0 0 10px #1e293b, 0 25px 60px -15px rgba(0,0,0,0.3);
    }}
  </style>
</head>
<body class="bg-[#DFEDE6] text-slate-800 antialiased min-h-screen p-2 sm:p-6 transition-all duration-300">

  <!-- ============================================================== -->
  <!-- TOP RESPONSIVE PREVIEW & RESIZER TOOLBAR -->
  <!-- ============================================================== -->
  <div class="max-w-4xl mx-auto mb-4 bg-white/95 backdrop-blur-md rounded-2xl border border-[#CCE2D6] p-3 shadow-md flex flex-wrap items-center justify-between gap-3 text-xs">
    
    <!-- Viewport Preset Buttons -->
    <div class="flex items-center gap-2">
      <span class="font-extrabold text-[#1E824C] flex items-center gap-1">
        <span>📐</span>
        <span>Viewport:</span>
      </span>
      
      <button onclick="setViewportWidth(400, 'mobile')" id="btnPresetMobile" class="px-3 py-1.5 rounded-xl font-extrabold bg-[#1E824C] text-white shadow-xs transition-all flex items-center gap-1.5">
        <span>📱</span>
        <span>Mobile (400px)</span>
      </button>

      <button onclick="setViewportWidth(680, 'tablet')" id="btnPresetTablet" class="px-3 py-1.5 rounded-xl font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all flex items-center gap-1.5">
        <span>📲</span>
        <span>Tablet (680px)</span>
      </button>

      <button onclick="setViewportWidth(920, 'desktop')" id="btnPresetDesktop" class="px-3 py-1.5 rounded-xl font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all flex items-center gap-1.5">
        <span>💻</span>
        <span>Desktop (920px)</span>
      </button>
    </div>

    <!-- Drag Slider & Current Width Badge -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="text-slate-500 font-semibold hidden md:inline">Drag:</span>
        <input type="range" id="widthSlider" min="360" max="960" value="400" step="10" oninput="onSliderResize(this.value)" class="w-28 sm:w-36 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#1E824C]" />
      </div>

      <span id="widthLabel" class="px-2.5 py-1 rounded-lg bg-emerald-50 text-[#1E824C] font-black border border-emerald-200 text-[11px]">
        📱 400px (Mobile)
      </span>

      <!-- Bezel Toggle -->
      <button onclick="toggleDeviceBezel()" id="btnBezelToggle" class="px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 font-bold text-[11px]">
        <span id="bezelLabel">Bezel: On</span>
      </button>
    </div>

  </div>

  <!-- ============================================================== -->
  <!-- MAIN DEVICE FRAME CONTAINER -->
  <!-- ============================================================== -->
  <div id="deviceWrapper" class="mx-auto transition-all duration-300 ease-out flex justify-center items-center" style="max-width: 400px;">
    
    <div id="deviceFrame" class="w-full bg-[#E5F3EC] rounded-[36px] overflow-hidden border border-[#D5E8DE] shadow-[0_25px_60px_-15px_rgba(0,121,83,0.22)] relative phone-chassis">

      <!-- ============================================================ -->
      <!-- VIEW 1: AUTH LOGIN SCREEN (EXACT 100% MATCH TO USER IMAGE) -->
      <!-- ============================================================ -->
      <div id="viewLogin" class="w-full relative">
        
        <!-- 1. EXACT TOP ILLUSTRATED HERO SECTION -->
        <!-- Contains Status Bar 9:41, Leaves, Heart Pulse Logo, Title, Subtitle, Quote, and Village Clinic Landscape -->
        <div class="w-full relative select-none">
          <img src="data:image/jpeg;base64,{exact_top_hero_b64}" alt="ArogyaSaathi Healthcare Scenery" class="w-full block object-cover" />
        </div>

        <!-- 2. BOTTOM FLOATING WHITE LOGIN CARD (SLIDES UP OVER LOWER ARTWORK) -->
        <div class="bg-white rounded-t-[36px] -mt-6 sm:-mt-8 relative z-10 px-6 pt-6 pb-6 shadow-xl border-t border-slate-100">
          
          <!-- Card Header: Welcome Back -->
          <div class="text-center mb-4">
            <h2 class="text-2xl font-black text-slate-900 tracking-tight">Welcome Back</h2>
            <p class="text-xs text-slate-500 font-semibold mt-0.5">Log in to continue</p>
          </div>

          <!-- TWO TOGGLE PILLS: [ 👤 Patient ]   [ 🧑‍⚕️ Other Login ] -->
          <div class="p-1 rounded-2xl bg-slate-100 flex items-center gap-1 mb-4">
            
            <!-- Patient Pill (Active by default) -->
            <button type="button" onclick="setLoginType('patient')" id="tabPillPatient" class="flex-1 py-2.5 rounded-xl font-black text-xs bg-[#1E824C] text-white shadow-md shadow-[#1E824C]/25 flex items-center justify-center gap-1.5 transition-all">
              <span>👤</span>
              <span>Patient</span>
            </button>

            <!-- Other Login Pill (Inactive by default) -->
            <button type="button" onclick="setLoginType('other')" id="tabPillOther" class="flex-1 py-2.5 rounded-xl font-bold text-xs text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all">
              <span>🧑‍⚕️</span>
              <span>Other Login</span>
            </button>

          </div>

          <!-- FORM FIELDS -->
          <form onsubmit="handleLoginSubmit(event)" class="space-y-3">
            
            <!-- Mobile / ID Field -->
            <div>
              <div class="relative flex items-center">
                <span class="absolute left-3.5 text-slate-400 text-sm">📞</span>
                <input id="inputMobile" type="text" value="9876543210" required placeholder="Mobile Number" class="w-full pl-10 pr-3 py-3 rounded-2xl bg-slate-50/70 border border-slate-200 focus:bg-white focus:border-[#1E824C] focus:ring-2 focus:ring-[#1E824C]/20 text-xs font-semibold text-slate-800 placeholder-slate-400 outline-none transition-all" />
              </div>
            </div>

            <!-- Password Field -->
            <div>
              <div class="relative flex items-center">
                <span class="absolute left-3.5 text-slate-400 text-sm">🔒</span>
                <input id="inputPassword" type="password" value="1234" required placeholder="Password" class="w-full pl-10 pr-10 py-3 rounded-2xl bg-slate-50/70 border border-slate-200 focus:bg-white focus:border-[#1E824C] focus:ring-2 focus:ring-[#1E824C]/20 text-xs font-semibold text-slate-800 placeholder-slate-400 outline-none transition-all" />
                <button type="button" onclick="togglePasswordVisibility()" class="absolute right-3.5 text-slate-400 hover:text-slate-600 text-xs">
                  👁️‍🗨️
                </button>
              </div>
            </div>

            <!-- Log In Button -->
            <div class="pt-1">
              <button type="submit" class="w-full py-3.5 bg-[#1E824C] hover:bg-[#186A3E] active:scale-[0.99] text-white font-black text-sm rounded-2xl shadow-md shadow-[#1E824C]/30 flex items-center justify-center gap-2 transition-all">
                <span>Log In</span>
                <span>➔</span>
              </button>
            </div>

          </form>

          <!-- ============================================================== -->
          <!-- CONDITIONAL "OR Login as" ROLE SELECTOR -->
          <!-- RULE: VISIBLE ONLY WHEN "Other Login" IS CLICKED; OTHERWISE HIDDEN -->
          <!-- ============================================================== -->
          <div id="otherLoginSection" class="hidden animate-fade-in mt-5 pt-3">
            
            <!-- Divider: ─── OR ─── -->
            <div class="relative flex items-center justify-center mb-1">
              <div class="border-t border-slate-200 w-full"></div>
              <span class="bg-white px-3 text-[11px] font-black text-slate-400 tracking-wider uppercase">OR</span>
              <div class="border-t border-slate-200 w-full"></div>
            </div>
            <p class="text-center text-[11px] font-bold text-slate-500 mb-3">Login as</p>

            <!-- 4 Role Option Cards Row (Health Worker, Doctor, Health Officer, Patient / Family) -->
            <div class="grid grid-cols-4 gap-2">
              
              <!-- Health Worker (Selected) -->
              <button type="button" onclick="selectOtherRole('Health Worker', 'ASHA-RAMPUR-7821')" id="roleBtnWorker" class="p-2.5 rounded-2xl bg-[#E8F7F0] border-2 border-[#1E824C] flex flex-col items-center text-center transition-all shadow-xs">
                <span class="text-lg mb-0.5">👩‍⚕️</span>
                <span class="text-[10px] font-black text-[#1E824C] leading-tight">Health Worker</span>
              </button>

              <!-- Doctor -->
              <button type="button" onclick="selectOtherRole('Doctor', 'DR-VERMA-PHC-402')" id="roleBtnDoctor" class="p-2.5 rounded-2xl bg-[#F0F7F3] hover:bg-[#E8F7F0] border border-slate-200 flex flex-col items-center text-center transition-all">
                <span class="text-lg mb-0.5">🩺</span>
                <span class="text-[10px] font-bold text-slate-600 leading-tight">Doctor</span>
              </button>

              <!-- Health Officer -->
              <button type="button" onclick="selectOtherRole('Health Officer', 'OFFICER-DIST-881')" id="roleBtnOfficer" class="p-2.5 rounded-2xl bg-[#F0F7F3] hover:bg-[#E8F7F0] border border-slate-200 flex flex-col items-center text-center transition-all">
                <span class="text-lg mb-0.5">👮</span>
                <span class="text-[10px] font-bold text-slate-600 leading-tight">Health Officer</span>
              </button>

              <!-- Patient / Family -->
              <button type="button" onclick="selectOtherRole('Patient / Family', '9876543210')" id="roleBtnFamily" class="p-2.5 rounded-2xl bg-[#F0F7F3] hover:bg-[#E8F7F0] border border-slate-200 flex flex-col items-center text-center transition-all">
                <span class="text-lg mb-0.5">👥</span>
                <span class="text-[10px] font-bold text-slate-600 leading-tight">Patient / Family</span>
              </button>

            </div>

            <!-- Bottom Green Leaf Accent: ── 🌿 ── -->
            <div class="flex items-center justify-center gap-2 mt-4 text-slate-300">
              <div class="w-8 h-px bg-slate-300"></div>
              <span class="text-xs">🍃</span>
              <div class="w-8 h-px bg-slate-300"></div>
            </div>

          </div>

        </div>

      </div>

      <!-- ============================================================ -->
      <!-- VIEW 2: AUTHENTICATED DECISION DASHBOARD (POST LOGIN) -->
      <!-- ============================================================ -->
      <div id="viewDashboard" class="hidden min-h-[580px] bg-slate-50 p-4 animate-fade-in">
        
        <!-- Header -->
        <div class="flex items-center justify-between bg-white p-3 rounded-2xl border border-slate-200 shadow-xs mb-3">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-xl bg-[#1E824C] flex items-center justify-center text-white text-sm">⚕️</div>
            <div>
              <div class="font-black text-xs text-slate-900 leading-tight">ArogyaSaathi Gateway</div>
              <div class="text-[10px] text-slate-500 font-semibold" id="dashUserSubtitle">Sunita Sharma (ASHA) • Rampur</div>
            </div>
          </div>
          <button onclick="signOutToLogin()" class="px-2.5 py-1 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50">
            Sign Out ➔
          </button>
        </div>

        <!-- 4 Action Tabs -->
        <div class="flex gap-1 overflow-x-auto pb-1.5 mb-3 text-[11px] font-black">
          <button onclick="setDashTab('triage')" id="tabBtnTriage" class="px-2.5 py-1.5 rounded-xl bg-[#1E824C] text-white shadow-xs shrink-0">🎙️ Triage</button>
          <button onclick="setDashTab('vitals')" id="tabBtnVitals" class="px-2.5 py-1.5 rounded-xl bg-white text-slate-700 border border-slate-200 shrink-0">📈 Vitals</button>
          <button onclick="setDashTab('roster')" id="tabBtnRoster" class="px-2.5 py-1.5 rounded-xl bg-white text-slate-700 border border-slate-200 shrink-0">📋 Roster</button>
          <button onclick="setDashTab('outbreak')" id="tabBtnOutbreak" class="px-2.5 py-1.5 rounded-xl bg-white text-slate-700 border border-slate-200 shrink-0">🗺️ Outbreak</button>
        </div>

        <!-- Triage Tab -->
        <div id="dashTabTriage" class="space-y-3">
          <div id="triageAlertBanner" class="hidden p-3 rounded-xl bg-red-50 border-2 border-red-500 text-red-900 text-xs shadow-xs">
            <span class="font-black text-[10px] text-red-600 block">CRITICAL RED FLAG DETECTED</span>
            <strong>Chest Pain + Sweating</strong>. Transfer to PHC immediately.
            <div class="mt-2 flex gap-1.5">
              <button onclick="alert('Priority 108 Ambulance Dispatched!')" class="px-3 py-1 bg-red-600 text-white rounded-lg font-bold">108 SOS</button>
              <button onclick="document.getElementById('triageAlertBanner').classList.add('hidden')" class="px-2.5 py-1 bg-red-100 rounded-lg font-bold text-red-800">Dismiss</button>
            </div>
          </div>

          <div class="bg-white rounded-2xl p-4 border border-slate-200 text-center shadow-xs">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Speech Symptom Triage</span>
            <button onclick="simulateTriageMic()" id="micBtn" class="w-16 h-16 rounded-full bg-[#1E824C] hover:bg-[#186A3E] text-white flex items-center justify-center text-2xl shadow-md mx-auto active:scale-95 transition-transform">
              🎙️
            </button>
            <div class="mt-2 text-xs font-bold text-slate-700" id="micStatusText">Tap to Start Speech Triage</div>

            <div class="mt-3 pt-2 border-t border-slate-100 text-left">
              <span class="text-[10px] font-bold text-slate-400 block mb-1">Test Spoken Presets:</span>
              <div class="flex flex-wrap gap-1">
                <button onclick="runTriageSpeech('सीने में बहुत तेज दर्द है और बहुत पसीना आ रहा है')" class="text-[10px] font-semibold px-2 py-1 rounded bg-slate-100 hover:bg-emerald-50 border border-slate-200">
                  "सीने में दर्द + पसीना"
                </button>
                <button onclick="runTriageSpeech('3 दिन से तेज बुखार है लेकिन गर्दन में अकड़न नहीं है')" class="text-[10px] font-semibold px-2 py-1 rounded bg-slate-100 hover:bg-emerald-50 border border-slate-200">
                  "बुखार, अकड़न नहीं" (Negation)
                </button>
              </div>
            </div>
          </div>

          <div id="guidedQuestionCard" class="hidden bg-white border-2 border-[#1E824C] rounded-2xl p-3.5 shadow-xs">
            <span class="text-[9px] font-black uppercase text-[#1E824C] bg-emerald-50 px-2 py-0.5 rounded">Guided Clinical Question</span>
            <h4 class="font-bold text-xs text-slate-900 mt-1">क्या सांस लेने में घरघराहट या पसलियां चलने की समस्या है?</h4>
            <div class="grid grid-cols-2 gap-2 mt-2.5">
              <button onclick="answerQuestion('हां (Yes)')" class="py-2 bg-[#1E824C] text-white font-bold text-xs rounded-lg">✓ हां (Yes)</button>
              <button onclick="answerQuestion('नहीं (No)')" class="py-2 bg-slate-100 text-slate-800 font-bold text-xs rounded-lg">✕ नहीं (No)</button>
            </div>
          </div>
        </div>

        <!-- Vitals Tab -->
        <div id="dashTabVitals" class="hidden space-y-2.5">
          <div class="bg-amber-50 border border-amber-300 rounded-xl p-2.5 text-xs text-amber-900">
            <strong>12-Day Early Warning:</strong> BP velocity spike (+1.8 mmHg/day).
          </div>
          <div class="bg-white rounded-2xl p-3.5 border border-slate-200 shadow-xs">
            <div class="flex justify-between items-center mb-1 text-xs font-bold">
              <span>30-Day BP Curve</span>
              <span class="text-red-600 text-[10px]">140 Limit Line</span>
            </div>
            <div class="w-full h-32 bg-slate-50 rounded-xl p-2 border border-slate-100">
              <svg class="w-full h-full" viewBox="0 0 320 120">
                <line x1="10" y1="48" x2="310" y2="48" stroke="#EF4444" stroke-width="1.5" stroke-dasharray="4" />
                <path d="M 20 75 Q 70 70 120 62 T 220 40 T 290 18" fill="none" stroke="#1E824C" stroke-width="3" />
                <circle cx="290" cy="18" r="5" fill="#DC2626" />
                <text x="268" y="14" fill="#DC2626" font-size="10" font-weight="900">184</text>
              </svg>
            </div>
          </div>
        </div>

        <!-- Roster Tab -->
        <div id="dashTabRoster" class="hidden space-y-2">
          <div class="bg-white p-3 rounded-xl border-2 border-red-200 shadow-xs text-xs">
            <div class="flex justify-between">
              <span class="bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-black text-[9px]">CRITICAL</span>
              <strong>HASH-RAMPUR-101 (58y/M)</strong>
            </div>
            <p class="text-[11px] text-slate-600 mt-1">Severe BP spike (184/110). Home visit due.</p>
            <div class="flex justify-end gap-1.5 mt-2">
              <button onclick="alert('Calling HASH-RAMPUR-101...')" class="px-2 py-0.5 border rounded">Call</button>
              <button onclick="showToast('Done', 'Visit recorded')" class="px-2.5 py-0.5 bg-[#1E824C] text-white rounded">Done</button>
            </div>
          </div>
        </div>

        <!-- Outbreak Tab -->
        <div id="dashTabOutbreak" class="hidden space-y-2 text-xs">
          <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
            <div class="flex justify-between items-center mb-1 font-bold">
              <span>Village Radar</span>
              <span class="text-red-600 text-[10px]">Z = 3.42 WARNING</span>
            </div>
            <div class="w-full h-32 bg-slate-900 rounded-xl relative overflow-hidden flex items-center justify-center">
              <div class="absolute w-28 h-28 rounded-full border border-emerald-500/30"></div>
              <div class="absolute w-32 h-32 rounded-full pointer-events-none radar-sweep" style="background: conic-gradient(from 0deg, rgba(16, 185, 129, 0.4) 0deg, transparent 60deg, transparent 360deg);"></div>
              <div class="w-3 h-3 bg-emerald-400 rounded-full"></div>
              <div class="absolute top-4 right-10 flex flex-col items-center">
                <div class="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></div>
                <span class="text-[8px] text-red-400 font-bold mt-1">Rampur ADD</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>

  </div>

  <!-- Toast -->
  <div id="toastNotification" class="fixed bottom-4 right-4 z-50 transform translate-y-24 opacity-0 transition-all duration-300 max-w-xs bg-slate-900 text-white p-3 rounded-xl shadow-xl border border-slate-700 flex items-start gap-2.5 text-xs">
    <div id="toastIcon" class="text-emerald-400 text-lg font-bold">✓</div>
    <div>
      <div id="toastTitle" class="font-bold">Notice</div>
      <div id="toastMessage" class="text-slate-300 text-[11px] mt-0.5">Description</div>
    </div>
  </div>

  <script>
    let isOtherLoginActive = false;
    let selectedOtherRole = 'Health Worker';

    // Toggle Login Type: 'patient' vs 'other'
    function setLoginType(type) {{
      const pillPatient = document.getElementById('tabPillPatient');
      const pillOther = document.getElementById('tabPillOther');
      const otherSection = document.getElementById('otherLoginSection');
      const inputMobile = document.getElementById('inputMobile');

      if (type === 'other') {{
        isOtherLoginActive = true;
        // Other Login Pill becomes active green
        pillOther.className = 'flex-1 py-2.5 rounded-xl font-black text-xs bg-[#1E824C] text-white shadow-md shadow-[#1E824C]/25 flex items-center justify-center gap-1.5 transition-all';
        pillPatient.className = 'flex-1 py-2.5 rounded-xl font-bold text-xs text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all';

        // SHOW THE "OR Login as" SECTION
        otherSection.classList.remove('hidden');

        inputMobile.placeholder = 'Worker ID / Mobile Number';
        inputMobile.value = 'ASHA-RAMPUR-7821';
        showToast('Other Login Active', 'Choose your clinical role below.');
      }} else {{
        isOtherLoginActive = false;
        // Patient Pill becomes active green
        pillPatient.className = 'flex-1 py-2.5 rounded-xl font-black text-xs bg-[#1E824C] text-white shadow-md shadow-[#1E824C]/25 flex items-center justify-center gap-1.5 transition-all';
        pillOther.className = 'flex-1 py-2.5 rounded-xl font-bold text-xs text-slate-600 hover:text-slate-900 flex items-center justify-center gap-1.5 transition-all';

        // HIDE THE "OR Login as" SECTION (CRITICAL USER CONSTRAINT)
        otherSection.classList.add('hidden');

        inputMobile.placeholder = 'Mobile Number';
        inputMobile.value = '9876543210';
      }}
    }}

    function selectOtherRole(roleName, defaultId) {{
      selectedOtherRole = roleName;
      const roles = [
        {{ key: 'Worker', name: 'Health Worker' }},
        {{ key: 'Doctor', name: 'Doctor' }},
        {{ key: 'Officer', name: 'Health Officer' }},
        {{ key: 'Family', name: 'Patient / Family' }}
      ];

      roles.forEach(r => {{
        const btn = document.getElementById('roleBtn' + r.key);
        if (r.name === roleName) {{
          btn.className = 'p-2.5 rounded-2xl bg-[#E8F7F0] border-2 border-[#1E824C] flex flex-col items-center text-center transition-all shadow-xs';
          btn.children[1].className = 'text-[10px] font-black text-[#1E824C] leading-tight';
        }} else {{
          btn.className = 'p-2.5 rounded-2xl bg-[#F0F7F3] hover:bg-[#E8F7F0] border border-slate-200 flex flex-col items-center text-center transition-all';
          btn.children[1].className = 'text-[10px] font-bold text-slate-600 leading-tight';
        }}
      }});

      document.getElementById('inputMobile').value = defaultId;
      document.getElementById('dashUserSubtitle').innerText = `${{roleName}} • Rampur Gateway`;
    }}

    function togglePasswordVisibility() {{
      const p = document.getElementById('inputPassword');
      p.type = p.type === 'password' ? 'text' : 'password';
    }}

    function handleLoginSubmit(e) {{
      e.preventDefault();
      document.getElementById('viewLogin').classList.add('hidden');
      document.getElementById('viewDashboard').classList.remove('hidden');
      showToast('Authenticated', 'Welcome to ArogyaSaathi! DPDP Act 2023 session active.');
    }}

    function signOutToLogin() {{
      document.getElementById('viewDashboard').classList.add('hidden');
      document.getElementById('viewLogin').classList.remove('hidden');
      setLoginType('patient'); // Reset to default patient state with hidden other login
      showToast('Signed Out', 'Safely signed out.');
    }}

    function setDashTab(tab) {{
      const tabs = ['triage', 'vitals', 'roster', 'outbreak'];
      tabs.forEach(t => {{
        const btn = document.getElementById('tabBtn' + t.charAt(0).toUpperCase() + t.slice(1));
        const content = document.getElementById('dashTab' + t.charAt(0).toUpperCase() + t.slice(1));
        if (t === tab) {{
          btn.className = 'px-2.5 py-1.5 rounded-xl bg-[#1E824C] text-white shadow-xs shrink-0';
          content.classList.remove('hidden');
        }} else {{
          btn.className = 'px-2.5 py-1.5 rounded-xl bg-white text-slate-700 border border-slate-200 shrink-0';
          content.classList.add('hidden');
        }}
      }});
    }}

    function setViewportWidth(val, mode) {{
      const wrapper = document.getElementById('deviceWrapper');
      const slider = document.getElementById('widthSlider');
      const label = document.getElementById('widthLabel');
      
      const buttons = ['Mobile', 'Tablet', 'Desktop'];
      buttons.forEach(b => {{
        const btn = document.getElementById('btnPreset' + b);
        if (b.toLowerCase() === mode) {{
          btn.className = 'px-3 py-1.5 rounded-xl font-extrabold bg-[#1E824C] text-white shadow-xs transition-all flex items-center gap-1.5';
        }} else {{
          btn.className = 'px-3 py-1.5 rounded-xl font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all flex items-center gap-1.5';
        }}
      }});

      wrapper.style.maxWidth = val + 'px';
      slider.value = val;
      label.innerText = (val < 500 ? '📱 ' : (val < 800 ? '📲 ' : '💻 ')) + val + 'px';
    }}

    function onSliderResize(val) {{
      const wrapper = document.getElementById('deviceWrapper');
      const label = document.getElementById('widthLabel');
      wrapper.style.maxWidth = val + 'px';
      label.innerText = (val < 500 ? '📱 ' : (val < 800 ? '📲 ' : '💻 ')) + val + 'px';
    }}

    let isBezelOn = true;
    function toggleDeviceBezel() {{
      isBezelOn = !isBezelOn;
      const frame = document.getElementById('deviceFrame');
      const label = document.getElementById('bezelLabel');
      if (isBezelOn) {{
        frame.className = 'w-full bg-[#E5F3EC] rounded-[36px] overflow-hidden border border-[#D5E8DE] shadow-[0_25px_60px_-15px_rgba(0,121,83,0.22)] relative phone-chassis';
        label.innerText = 'Bezel: On';
      }} else {{
        frame.className = 'w-full bg-[#E5F3EC] rounded-3xl overflow-hidden border border-[#D5E8DE] shadow-md relative';
        label.innerText = 'Bezel: Off';
      }}
    }}

    function showToast(title, message) {{
      const toast = document.getElementById('toastNotification');
      document.getElementById('toastTitle').innerText = title;
      document.getElementById('toastMessage').innerText = message;
      toast.classList.remove('translate-y-24', 'opacity-0');
      setTimeout(() => {{
        toast.classList.add('translate-y-24', 'opacity-0');
      }}, 3000);
    }}

    function simulateTriageMic() {{
      const btn = document.getElementById('micBtn');
      const text = document.getElementById('micStatusText');
      btn.className = 'w-16 h-16 rounded-full bg-red-600 text-white flex items-center justify-center text-2xl shadow-md mx-auto animate-pulse';
      text.innerText = 'Listening to patient speech (Hindi)...';
      setTimeout(() => {{
        runTriageSpeech('सीने में बहुत तेज दर्द है और बहुत पसीना आ रहा है');
      }}, 1800);
    }}

    function runTriageSpeech(transcript) {{
      const btn = document.getElementById('micBtn');
      const text = document.getElementById('micStatusText');
      btn.className = 'w-16 h-16 rounded-full bg-[#1E824C] hover:bg-[#186A3E] text-white flex items-center justify-center text-2xl shadow-md mx-auto';
      text.innerText = 'Processed: "' + transcript + '"';

      if (transcript.includes('सीने में बहुत तेज दर्द')) {{
        document.getElementById('triageAlertBanner').classList.remove('hidden');
        document.getElementById('guidedQuestionCard').classList.add('hidden');
        showToast('Red Flag', 'Chest pain cluster detected.');
      }} else {{
        document.getElementById('triageAlertBanner').classList.add('hidden');
        document.getElementById('guidedQuestionCard').classList.remove('hidden');
        showToast('Negation Parsed', 'No neck stiffness confirmed.');
      }}
    }}

    function answerQuestion(ans) {{
      showToast('Logged', 'Recorded: ' + ans);
      document.getElementById('guidedQuestionCard').classList.add('hidden');
    }}
  </script>
</body>
</html>
'''

with open('frontend/web/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

with open('/home/vivek/.gemini/antigravity/brain/d046502c-0133-47f6-9025-b3f5f77d8f92/arogya_interface.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Exact top hero artwork integrated seamlessly!')
