import base64
import os

with open('frontend/web/assets/left_hero.jpg', 'rb') as f:
    left_hero_b64 = base64.b64encode(f.read()).decode()

with open('frontend/web/assets/logo_badge.png', 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode()

with open('frontend/web/assets/slogan_badge.png', 'rb') as f:
    slogan_b64 = base64.b64encode(f.read()).decode()

with open('frontend/web/assets/asha_patient_photo.jpg', 'rb') as f:
    photo_b64 = base64.b64encode(f.read()).decode()

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ArogyaSaathi (आरोग्य साथी) • Better Care Closer to Every Home</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    body {{
      font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }}
    
    @keyframes pulseGlow {{
      0%, 100% {{ transform: scale(1); opacity: 0.9; }}
      50% {{ transform: scale(1.05); opacity: 1; }}
    }}
    @keyframes radarSweep {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}
    @keyframes fadeInScale {{
      0% {{ opacity: 0; transform: scale(0.97) translateY(8px); }}
      100% {{ opacity: 1; transform: scale(1) translateY(0); }}
    }}
    .animate-fade-in {{
      animation: fadeInScale 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    .radar-sweep {{
      transform-origin: center center;
      animation: radarSweep 4s linear infinite;
    }}
    .hide-scrollbar::-webkit-scrollbar {{
      display: none;
    }}
    .hide-scrollbar {{
      -ms-overflow-style: none;
      scrollbar-width: none;
    }}
  </style>
</head>
<body class="bg-[#EAF3EE] text-slate-800 antialiased min-h-screen flex items-center justify-center p-2 sm:p-6 transition-colors duration-200">

  <!-- Main Container Frame matching the reference mockup -->
  <div class="w-full max-w-5xl mx-auto shadow-[0_20px_60px_-15px_rgba(0,121,83,0.18)] rounded-[32px] overflow-hidden bg-white border border-[#D5E8DE]">
    
    <!-- ============================================================ -->
    <!-- VIEW 1: AUTH LOGIN SCREEN (EXACT MATCH TO USER REFERENCE) -->
    <!-- ============================================================ -->
    <div id="viewLogin" class="grid grid-cols-1 lg:grid-cols-12 min-h-[640px] relative bg-white">
      
      <!-- LEFT HERO SECTION (60% on desktop) -->
      <div class="lg:col-span-7 relative bg-gradient-to-br from-[#F4FAF6] via-[#E8F6EF] to-[#DDF1E7] p-8 sm:p-12 flex flex-col justify-between overflow-hidden">
        
        <!-- Background Organic Wave Curves -->
        <div class="absolute -bottom-24 -left-24 w-96 h-96 rounded-full bg-[#10B981]/15 blur-2xl pointer-events-none"></div>
        <div class="absolute top-1/2 -right-20 w-80 h-80 rounded-full bg-[#059669]/10 blur-xl pointer-events-none"></div>

        <!-- Top Left: ArogyaSaathi Brand Logo & Subtitle -->
        <div class="relative z-10">
          <div class="flex items-center gap-3.5">
            <!-- Stylized Emerald Heart + Cross Icon -->
            <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#00895D] to-[#005B3E] flex items-center justify-center text-white shadow-md shadow-[#00895D]/25">
              <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                <path d="M12 9v6m-3-3h6"/>
              </svg>
            </div>
            <div>
              <h1 class="text-2xl sm:text-3xl font-extrabold text-[#0B4734] tracking-tight leading-none">ArogyaSaathi</h1>
              <p class="text-xs text-[#52796F] font-semibold mt-1">Healthy Villages • Stronger Communities</p>
            </div>
          </div>

          <!-- Bold Main Headline -->
          <div class="mt-8 sm:mt-10">
            <h2 class="text-3xl sm:text-4xl font-extrabold text-[#0C3829] leading-[1.18] tracking-tight">
              Better Care<br/>
              <span class="text-[#007953]">Closer to Every Home</span>
            </h2>
          </div>
        </div>

        <!-- Center/Bottom Visual: ASHA Worker with Rural Patient & Slogan -->
        <div class="relative z-10 mt-8 sm:mt-12 flex flex-col sm:flex-row items-end justify-between gap-4">
          
          <!-- Image of ASHA Worker in Pink Saree helping Village Woman -->
          <div class="relative group">
            <div class="w-64 sm:w-72 h-44 sm:h-52 rounded-3xl overflow-hidden shadow-xl border-4 border-white/90 bg-slate-200">
              <img src="data:image/jpeg;base64,{photo_b64}" alt="ASHA Worker with Rural Patient" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
            </div>
            <!-- Decorative Green Leaf Accent -->
            <div class="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-[#007953] text-white flex items-center justify-center text-sm shadow-md">
              🌿
            </div>
          </div>

          <!-- Swasth Gaon Sashakt Bharat Banner Badge -->
          <div class="sm:mb-2 bg-white/90 backdrop-blur-md p-3.5 rounded-2xl border border-[#CDE5D8] shadow-md flex items-center gap-3 max-w-[210px]">
            <img src="data:image/png;base64,{slogan_b64}" alt="Swasth Gaon Sashakt Bharat" class="w-14 h-14 object-contain" />
            <div>
              <div class="text-xs font-black text-[#007953] leading-tight italic">Swasth Gaon</div>
              <div class="text-xs font-black text-[#0C3829] leading-tight italic">Sashakt Bharat</div>
              <div class="flex items-center gap-1 mt-1">
                <span class="w-3 h-1 bg-[#FF9933] rounded-full"></span>
                <span class="w-3 h-1 bg-white border border-slate-300 rounded-full"></span>
                <span class="w-3 h-1 bg-[#138808] rounded-full"></span>
              </div>
            </div>
          </div>

        </div>

      </div>

      <!-- RIGHT FORM SECTION (50% on desktop) -->
      <div class="lg:col-span-5 p-8 sm:p-10 flex flex-col justify-between bg-white">
        
        <div>
          <!-- Top Right Language Dropdown Selector -->
          <div class="flex justify-end mb-6">
            <div class="relative inline-block text-left">
              <button onclick="toggleLangMenu()" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 hover:border-slate-300 bg-white text-xs font-bold text-slate-700 shadow-xs">
                <span>🌐</span>
                <span id="selectedLangLabel">English</span>
                <svg class="w-3.5 h-3.5 text-slate-400 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
              </button>
              
              <div id="langDropdown" class="hidden absolute right-0 mt-1 w-32 rounded-xl bg-white shadow-xl border border-slate-100 py-1 z-50 text-xs">
                <button onclick="setLang('en', 'English')" class="w-full text-left px-3 py-2 hover:bg-slate-50 font-bold text-slate-700">English</button>
                <button onclick="setLang('hi', 'हिन्दी (Hindi)')" class="w-full text-left px-3 py-2 hover:bg-slate-50 font-bold text-slate-700">हिन्दी (Hindi)</button>
              </div>
            </div>
          </div>

          <!-- Welcome Header -->
          <div class="mb-6">
            <h3 class="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight" id="txtWelcome">Welcome Back</h3>
            <p class="text-xs sm:text-sm text-slate-500 mt-1 font-medium" id="txtSignSub">Sign in to continue to ArogyaSaathi</p>
          </div>

          <!-- Role Selector Tabs (3 In A Row matching design) -->
          <div class="grid grid-cols-3 gap-2.5 mb-5">
            <!-- ASHA / ANM (Selected State) -->
            <button type="button" onclick="selectRole('ASHA')" id="roleBtnASHA" class="p-3 rounded-2xl bg-[#E8F7F0] border-2 border-[#007953] flex flex-col items-center justify-center text-center transition-all shadow-xs">
              <div class="w-8 h-8 rounded-full bg-[#007953]/15 flex items-center justify-center text-[#007953] mb-1 text-sm font-bold">
                👩‍⚕️
              </div>
              <span class="text-xs font-extrabold text-[#007953] leading-tight">ASHA / ANM</span>
            </button>

            <!-- Doctor Tab -->
            <button type="button" onclick="selectRole('DOCTOR')" id="roleBtnDOCTOR" class="p-3 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center justify-center text-center transition-all">
              <div class="w-8 h-8 rounded-full bg-slate-200/80 flex items-center justify-center text-slate-600 mb-1 text-sm font-bold">
                🩺
              </div>
              <span class="text-xs font-semibold text-slate-600 leading-tight">Doctor</span>
            </button>

            <!-- Health Officer Tab -->
            <button type="button" onclick="selectRole('OFFICER')" id="roleBtnOFFICER" class="p-3 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center justify-center text-center transition-all">
              <div class="w-8 h-8 rounded-full bg-slate-200/80 flex items-center justify-center text-slate-600 mb-1 text-sm font-bold">
                👥
              </div>
              <span class="text-xs font-semibold text-slate-600 leading-tight">Health Officer</span>
            </button>
          </div>

          <!-- Input Fields Form -->
          <form onsubmit="handleFormSubmit(event)" class="space-y-3.5">
            
            <!-- Username / Mobile Number Input -->
            <div>
              <div class="relative flex items-center">
                <span class="absolute left-3.5 text-slate-400">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
                </span>
                <input id="inputUser" type="text" value="ASHA-RAMPUR-7821" required placeholder="Username / Mobile Number" class="w-full pl-11 pr-4 py-3 rounded-xl border border-slate-300 focus:border-[#007953] focus:ring-2 focus:ring-[#007953]/20 text-xs sm:text-sm font-medium text-slate-800 placeholder-slate-400 outline-none transition-all" />
              </div>
            </div>

            <!-- Password Input with Eye Icon -->
            <div>
              <div class="relative flex items-center">
                <span class="absolute left-3.5 text-slate-400">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                </span>
                <input id="inputPassword" type="password" value="1234" required placeholder="Password" class="w-full pl-11 pr-11 py-3 rounded-xl border border-slate-300 focus:border-[#007953] focus:ring-2 focus:ring-[#007953]/20 text-xs sm:text-sm font-medium text-slate-800 placeholder-slate-400 outline-none transition-all" />
                <button type="button" onclick="togglePasswordVisibility()" class="absolute right-3.5 text-slate-400 hover:text-slate-600">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                </button>
              </div>
            </div>

            <!-- Remember me & Forgot Password Row -->
            <div class="flex items-center justify-between text-xs pt-1">
              <label class="flex items-center gap-2 cursor-pointer select-none text-slate-600 font-medium">
                <input type="checkbox" checked class="w-4 h-4 rounded text-[#007953] focus:ring-[#007953] border-slate-300 accent-[#007953]" />
                <span id="txtRemember">Remember me</span>
              </label>
              <button type="button" onclick="showToast('Password Reset', 'OTP sent to registered ASHA mobile number (+91 98765 43210)')" class="font-bold text-[#007953] hover:underline" id="txtForgot">Forgot password?</button>
            </div>

            <!-- Main Sign In Button -->
            <div class="pt-2">
              <button type="submit" class="w-full py-3.5 px-6 rounded-xl bg-[#007953] hover:bg-[#006646] active:scale-[0.99] text-white font-extrabold text-sm sm:text-base shadow-md shadow-[#007953]/25 flex items-center justify-center gap-2.5 transition-all">
                <span id="txtSignIn">Sign In</span>
                <span>➔</span>
              </button>
            </div>
          </form>
        </div>

        <!-- Bottom Security Pill Box (Exact Match to Reference Mockup) -->
        <div class="mt-8 bg-[#F4FAF6] border border-[#D3EBDD] rounded-2xl p-3 sm:p-3.5 flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-white shadow-xs border border-[#C4E4D1] flex items-center justify-center text-emerald-700 shrink-0">
            <svg class="w-5 h-5 text-[#007953]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          </div>
          <div>
            <h4 class="text-xs font-extrabold text-slate-800" id="txtSecTitle">Secure • Private • For Better Healthcare</h4>
            <p class="text-[11px] text-slate-500 font-medium" id="txtSecSub">Your data is safe and used only for healthcare purposes.</p>
          </div>
        </div>

      </div>

    </div>

    <!-- ============================================================ -->
    <!-- VIEW 2: AUTHENTICATED CLINICAL DASHBOARD (POST LOGIN) -->
    <!-- ============================================================ -->
    <div id="viewDashboard" class="hidden min-h-[640px] bg-slate-50 p-4 sm:p-8 animate-fade-in">
      
      <!-- Dashboard Top Header Bar -->
      <div class="flex flex-wrap items-center justify-between gap-4 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-sm mb-6">
        <div class="flex items-center gap-3.5">
          <div class="w-11 h-11 rounded-2xl bg-[#007953] flex items-center justify-center text-white font-bold text-xl shadow-md">
            ⚕️
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="font-extrabold text-lg text-slate-900 leading-tight">ArogyaSaathi Gateway</h2>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">DPDP 2023 AES-256</span>
            </div>
            <p class="text-xs text-slate-500 font-medium" id="dashUserSubtitle">Sunita Sharma (ASHA) • Rampur Sub-Centre Gateway</p>
          </div>
        </div>

        <div class="flex items-center gap-2.5">
          <!-- 108 Emergency Trigger -->
          <button onclick="triggerEmergency108()" class="px-3.5 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-black text-xs shadow-md flex items-center gap-1.5 active:scale-95 transition-all">
            <span>🚨</span>
            <span>108 SOS</span>
          </button>

          <!-- Sign Out Button -->
          <button onclick="signOutToLogin()" class="px-3.5 py-2 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1.5 transition-all">
            <span>Sign Out</span>
            <span>➔</span>
          </button>
        </div>
      </div>

      <!-- Main Navigation Tabs -->
      <div class="flex gap-2 overflow-x-auto pb-2 mb-6">
        <button onclick="setDashTab('triage')" id="tabBtnTriage" class="px-4 py-2 rounded-xl font-bold text-xs bg-[#007953] text-white shadow-sm transition-all flex items-center gap-1.5">
          <span>🎙️</span>
          <span>Voice Triage & Danger Signs</span>
        </button>
        <button onclick="setDashTab('vitals')" id="tabBtnVitals" class="px-4 py-2 rounded-xl font-bold text-xs bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all flex items-center gap-1.5">
          <span>📈</span>
          <span>Chronic Vitals Curves</span>
        </button>
        <button onclick="setDashTab('roster')" id="tabBtnRoster" class="px-4 py-2 rounded-xl font-bold text-xs bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all flex items-center gap-1.5">
          <span>📋</span>
          <span>ASHA Action Roster</span>
        </button>
        <button onclick="setDashTab('outbreak')" id="tabBtnOutbreak" class="px-4 py-2 rounded-xl font-bold text-xs bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all flex items-center gap-1.5">
          <span>🗺️</span>
          <span>Village Outbreak Radar</span>
        </button>
      </div>

      <!-- TAB 1: VOICE TRIAGE (ZERO CHATBOT - GUIDED CLINICAL PROTOCOL) -->
      <div id="dashTabTriage" class="space-y-4">
        
        <!-- Emergency Alert Banner (when red flag is detected) -->
        <div id="triageAlertBanner" class="hidden p-4 rounded-2xl bg-red-50 border-2 border-red-500 text-red-900 shadow-md">
          <div class="flex items-start gap-3">
            <span class="text-2xl animate-bounce">🚨</span>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span class="text-xs font-extrabold uppercase tracking-wider text-red-600">CRITICAL RED FLAG DETECTED</span>
                <span class="text-[10px] bg-red-600 text-white font-bold px-2 py-0.5 rounded-full">EMERGENCY</span>
              </div>
              <h4 class="font-extrabold text-sm mt-0.5">Acute Coronary / Chest Pain Syndrome</h4>
              <p class="text-xs text-red-800 mt-1">Clause-aware extracted: <strong>सीने में तेज दर्द + अत्यधिक पसीना (Chest pain with profuse sweating)</strong>. Zero unvalidated prescription risk: immediate 108 ambulance referral required.</p>
              
              <div class="mt-3 flex gap-2">
                <button onclick="triggerEmergency108()" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-xl shadow-sm flex items-center gap-2">
                  <span>📞 Dispatch 108 Ambulance</span>
                </button>
                <button onclick="document.getElementById('triageAlertBanner').classList.add('hidden')" class="px-3 py-2 bg-red-100 text-red-800 font-bold text-xs rounded-xl">Dismiss</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Voice Recording Panel -->
        <div class="bg-white rounded-3xl p-6 border border-slate-200 text-center shadow-sm">
          <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Hands-Free Speech Symptom Triage</span>
          <p class="text-xs text-slate-600 mb-4">Patient speaks symptoms naturally in Hindi or English (Clause-aware negation & danger sign evaluation)</p>

          <!-- Central Mic Button with Waveform Visualizer -->
          <div class="relative inline-block my-2">
            <button id="micBtn" onclick="toggleTriageMic()" class="w-20 h-20 rounded-full bg-[#007953] hover:bg-[#006646] text-white flex items-center justify-center text-3xl shadow-lg shadow-[#007953]/30 transition-transform active:scale-95">
              🎙️
            </button>
          </div>

          <div class="mt-3">
            <span id="micStatusText" class="text-xs font-bold text-slate-700">Tap to Start Speech Symptom Check</span>
          </div>

          <!-- Quick Spoken Transcript Simulators -->
          <div class="mt-5 pt-4 border-t border-slate-100 text-left">
            <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Simulate Patient Speech Input:</span>
            <div class="flex flex-wrap gap-2">
              <button onclick="runTriageSpeech('सीने में बहुत तेज दर्द है और बहुत पसीना आ रहा है')" class="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-[#E8F7F0] hover:text-[#007953] border border-slate-200 transition-all">
                "सीने में तेज दर्द और पसीना" (Emergency)
              </button>
              <button onclick="runTriageSpeech('3 दिन से तेज बुखार है लेकिन गर्दन में कोई अकड़न नहीं है')" class="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-[#E8F7F0] hover:text-[#007953] border border-slate-200 transition-all">
                "3 दिन बुखार, गर्दन में अकड़न नहीं" (Negation)
              </button>
              <button onclick="runTriageSpeech('बच्चे को 2 दिन से दस्त है और पानी नहीं पी रहा')" class="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-[#E8F7F0] hover:text-[#007953] border border-slate-200 transition-all">
                "बच्चा सुस्त + दस्त" (Child Danger Sign)
              </button>
            </div>
          </div>
        </div>

        <!-- Guided Clinical Question Card (YES/NO TOUCH BUTTONS) -->
        <div id="guidedQuestionCard" class="hidden bg-white border-2 border-[#007953] rounded-3xl p-5 shadow-sm">
          <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#007953] bg-[#E8F7F0] px-2.5 py-0.5 rounded-full">Guided Clinical Question</span>
          <h4 id="guidedQuestionText" class="font-extrabold text-sm text-slate-900 mt-2">क्या सांस लेने में घरघराहट या पसलियां चलने की समस्या है?</h4>
          <p class="text-xs text-slate-500 mt-1">Tap a direct answer below. No typing required.</p>

          <div class="grid grid-cols-2 gap-3 mt-4">
            <button onclick="answerQuestion('हां (Yes)')" class="py-3 px-4 bg-[#007953] hover:bg-[#006646] text-white font-extrabold text-sm rounded-xl flex items-center justify-center gap-2 shadow-sm transition-transform active:scale-95">
              ✓ हां (Yes)
            </button>
            <button onclick="answerQuestion('नहीं (No)')" class="py-3 px-4 bg-slate-100 hover:bg-slate-200 text-slate-800 font-extrabold text-sm rounded-xl flex items-center justify-center gap-2 transition-transform active:scale-95">
              ✕ नहीं (No)
            </button>
          </div>
        </div>

      </div>

      <!-- TAB 2: CHRONIC VITALS & BP CURVES -->
      <div id="dashTabVitals" class="hidden space-y-4">
        
        <!-- 12-Day Early Warning Banner -->
        <div class="bg-amber-50 border-2 border-amber-400 rounded-2xl p-4 text-amber-950 shadow-sm flex items-start gap-3">
          <span class="text-2xl">⚠️</span>
          <div>
            <span class="text-[10px] font-black uppercase tracking-wider text-amber-800 bg-amber-200 px-2 py-0.5 rounded-full">12-DAY EARLY LEAD TIME</span>
            <h4 class="font-extrabold text-sm mt-1">Accelerating Systolic Velocity (+1.8 mmHg/day)</h4>
            <p class="text-xs text-amber-800 mt-0.5">Patient HASH-RAMPUR-101 missed 3 consecutive medication doses due to village PHC stockout. Early crisis intervention recommended.</p>
          </div>
        </div>

        <!-- 30-Day BP Curve Canvas/SVG Card -->
        <div class="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-red-500"></span>
              <span class="text-sm font-extrabold text-slate-900">30-Day Blood Pressure History (mmHg)</span>
              <span class="text-[10px] text-red-600 font-bold border border-red-200 bg-red-50 px-1.5 py-0.5 rounded">140 Limit Line</span>
            </div>
            <span class="text-xs font-semibold text-slate-400">Synthea Longitudinal Curve</span>
          </div>

          <!-- SVG Chart with 140 mmHg line -->
          <div class="w-full h-44 bg-slate-50 rounded-2xl p-2 border border-slate-100">
            <svg class="w-full h-full" viewBox="0 0 320 120">
              <line x1="10" y1="48" x2="310" y2="48" stroke="#EF4444" stroke-width="1.5" stroke-dasharray="4" />
              <text x="15" y="43" fill="#EF4444" font-size="8.5" font-weight="bold">140 mmHg (Stage 2 Hypertension Line)</text>

              <line x1="10" y1="84" x2="310" y2="84" stroke="#10B981" stroke-width="1" stroke-dasharray="3" opacity="0.6"/>
              <text x="15" y="79" fill="#10B981" font-size="8">120 mmHg Normal</text>

              <path d="M 20 75 Q 70 70 120 62 T 220 40 T 290 18" fill="none" stroke="#007953" stroke-width="3.5" />
              <circle cx="20" cy="75" r="4.5" fill="#007953" />
              <circle cx="120" cy="62" r="4.5" fill="#007953" />
              <circle cx="220" cy="40" r="5" fill="#EF4444" />
              <circle cx="290" cy="18" r="6" fill="#DC2626" stroke="#FFFFFF" stroke-width="2" />
              <text x="268" y="14" fill="#DC2626" font-size="10" font-weight="900">184</text>
            </svg>
          </div>

          <div class="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-100 text-center">
            <div>
              <span class="text-[10px] text-slate-400 font-bold uppercase block">Latest BP</span>
              <span class="text-sm font-extrabold text-red-600">184 / 110</span>
            </div>
            <div>
              <span class="text-[10px] text-slate-400 font-bold uppercase block">Adherence</span>
              <span class="text-sm font-extrabold text-amber-600">50% (Missed)</span>
            </div>
            <div>
              <span class="text-[10px] text-slate-400 font-bold uppercase block">Blood Sugar</span>
              <span class="text-sm font-extrabold text-slate-800">168 mg/dL</span>
            </div>
          </div>
        </div>

      </div>

      <!-- TAB 3: ASHA ACTION ROSTER -->
      <div id="dashTabRoster" class="hidden space-y-3">
        <div class="flex justify-between items-center mb-1">
          <h4 class="font-extrabold text-sm text-slate-900">Today's Prioritized Home Visits</h4>
          <span class="text-xs font-semibold text-slate-500">1 of 3 Completed</span>
        </div>

        <!-- Patient 1 -->
        <div class="bg-white p-4 rounded-2xl border-2 border-red-200 shadow-sm">
          <div class="flex justify-between items-start">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-black bg-red-100 text-red-700">CRITICAL</span>
              <h5 class="font-extrabold text-sm text-slate-900">HASH-RAMPUR-101</h5>
            </div>
            <span class="text-xs text-slate-500 font-semibold">58y / M</span>
          </div>
          <p class="text-xs text-slate-700 mt-2 font-medium bg-slate-50 p-2.5 rounded-xl border border-slate-100">Immediate home visit: Blood pressure spike (184/110) & severe headache.</p>
          <div class="flex justify-between items-center mt-3 pt-2 border-t border-slate-100">
            <button onclick="alert('Calling registered phone for HASH-RAMPUR-101 (Decrypted under DPDP role permissions)')" class="text-xs font-bold text-slate-700 flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50">
              📞 Call
            </button>
            <button onclick="showToast('Visit Logged', 'Home visit recorded for HASH-RAMPUR-101')" class="text-xs font-bold px-3 py-1.5 rounded-lg bg-[#007953] hover:bg-[#006646] text-white shadow-xs">
              Mark Visit Done
            </button>
          </div>
        </div>

        <!-- Patient 2 -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <div class="flex justify-between items-start">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded text-[10px] font-black bg-amber-100 text-amber-700">HIGH</span>
              <h5 class="font-extrabold text-sm text-slate-900">HASH-RAMPUR-102</h5>
            </div>
            <span class="text-xs text-slate-500 font-semibold">52y / F</span>
          </div>
          <p class="text-xs text-slate-700 mt-2 font-medium bg-slate-50 p-2.5 rounded-xl border border-slate-100">Visit within 24-48h: 3 consecutive missed diabetes doses reported.</p>
          <div class="flex justify-between items-center mt-3 pt-2 border-t border-slate-100">
            <button onclick="alert('Calling registered phone for HASH-RAMPUR-102')" class="text-xs font-bold text-slate-700 flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50">
              📞 Call
            </button>
            <button onclick="showToast('Visit Logged', 'Home visit recorded for HASH-RAMPUR-102')" class="text-xs font-bold px-3 py-1.5 rounded-lg bg-[#007953] hover:bg-[#006646] text-white shadow-xs">
              Mark Visit Done
            </button>
          </div>
        </div>
      </div>

      <!-- TAB 4: VILLAGE OUTBREAK RADAR -->
      <div id="dashTabOutbreak" class="hidden space-y-4">
        <div class="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-extrabold text-sm text-slate-900">Spatio-Temporal Village Radar</h4>
            <span class="text-xs font-black text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded">Z = 3.42 WARNING</span>
          </div>

          <div class="w-full h-44 bg-slate-900 rounded-2xl relative overflow-hidden flex items-center justify-center">
            <div class="absolute w-20 h-20 border border-emerald-500/30 rounded-full"></div>
            <div class="absolute w-36 h-36 border border-emerald-500/20 rounded-full"></div>
            
            <div class="absolute w-44 h-44 rounded-full pointer-events-none radar-sweep" style="background: conic-gradient(from 0deg, rgba(16, 185, 129, 0.4) 0deg, transparent 60deg, transparent 360deg);"></div>

            <div class="w-3.5 h-3.5 bg-emerald-400 rounded-full z-10 shadow-lg"></div>
            <span class="absolute text-[9px] text-emerald-300 font-bold bottom-12">PHC Hub</span>

            <div class="absolute top-6 right-16 flex flex-col items-center">
              <div class="w-6 h-6 rounded-full bg-red-500/30 animate-ping absolute"></div>
              <div class="w-3 h-3 rounded-full bg-red-500 shadow-md"></div>
              <span class="text-[9px] text-red-400 font-black mt-1">Rampur (Z=3.42)</span>
            </div>
          </div>

          <p class="text-xs text-slate-600 mt-3 font-medium">
            <strong>Rampur Alert:</strong> 19 acute diarrheal disease cases detected (+352% spike). Triangulated with local pharmacy ORS spikes (+420%) and school absenteeism.
          </p>
        </div>
      </div>

    </div>

  </div>

  <!-- Interactive Toast Notification -->
  <div id="toastNotification" class="fixed bottom-6 right-6 z-50 transform translate-y-24 opacity-0 transition-all duration-300 max-w-sm bg-slate-900 text-white p-4 rounded-2xl shadow-xl border border-slate-700 flex items-start gap-3">
    <div id="toastIcon" class="text-emerald-400 text-xl font-bold">✓</div>
    <div>
      <div id="toastTitle" class="font-extrabold text-sm">Action Complete</div>
      <div id="toastMessage" class="text-xs text-slate-300 mt-0.5">Notification description.</div>
    </div>
  </div>

  <script>
    let activeRole = 'ASHA';
    let currentLang = 'en';

    function toggleLangMenu() {{
      const d = document.getElementById('langDropdown');
      d.classList.toggle('hidden');
    }}

    function setLang(code, label) {{
      currentLang = code;
      document.getElementById('selectedLangLabel').innerText = label;
      document.getElementById('langDropdown').classList.add('hidden');

      if (code === 'hi') {{
        document.getElementById('txtWelcome').innerText = 'वापसी पर स्वागत है';
        document.getElementById('txtSignSub').innerText = 'आरोग्य साथी में जारी रखने के लिए साइन इन करें';
        document.getElementById('txtRemember').innerText = 'मुझे याद रखें';
        document.getElementById('txtForgot').innerText = 'पासवर्ड भूल गए?';
        document.getElementById('txtSignIn').innerText = 'साइन इन करें';
        document.getElementById('txtSecTitle').innerText = 'सुरक्षित • निजी • बेहतर स्वास्थ्य के लिए';
        document.getElementById('txtSecSub').innerText = 'आपका डेटा सुरक्षित है और केवल स्वास्थ्य सेवा के लिए उपयोग किया जाता है।';
      }} else {{
        document.getElementById('txtWelcome').innerText = 'Welcome Back';
        document.getElementById('txtSignSub').innerText = 'Sign in to continue to ArogyaSaathi';
        document.getElementById('txtRemember').innerText = 'Remember me';
        document.getElementById('txtForgot').innerText = 'Forgot password?';
        document.getElementById('txtSignIn').innerText = 'Sign In';
        document.getElementById('txtSecTitle').innerText = 'Secure • Private • For Better Healthcare';
        document.getElementById('txtSecSub').innerText = 'Your data is safe and used only for healthcare purposes.';
      }}
    }}

    function selectRole(role) {{
      activeRole = role;
      const roles = ['ASHA', 'DOCTOR', 'OFFICER'];
      roles.forEach(r => {{
        const btn = document.getElementById('roleBtn' + r);
        if (r === role) {{
          btn.className = 'p-3 rounded-2xl bg-[#E8F7F0] border-2 border-[#007953] flex flex-col items-center justify-center text-center transition-all shadow-xs';
          btn.children[0].className = 'w-8 h-8 rounded-full bg-[#007953]/15 flex items-center justify-center text-[#007953] mb-1 text-sm font-bold';
          btn.children[1].className = 'text-xs font-extrabold text-[#007953] leading-tight';
        }} else {{
          btn.className = 'p-3 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center justify-center text-center transition-all';
          btn.children[0].className = 'w-8 h-8 rounded-full bg-slate-200/80 flex items-center justify-center text-slate-600 mb-1 text-sm font-bold';
          btn.children[1].className = 'text-xs font-semibold text-slate-600 leading-tight';
        }}
      }});

      const inputUser = document.getElementById('inputUser');
      if (role === 'ASHA') {{
        inputUser.value = 'ASHA-RAMPUR-7821';
        document.getElementById('dashUserSubtitle').innerText = 'Sunita Sharma (ASHA) • Rampur Sub-Centre Gateway';
      }} else if (role === 'DOCTOR') {{
        inputUser.value = 'DR-VERMA-PHC-402';
        document.getElementById('dashUserSubtitle').innerText = 'Dr. Rajesh Verma (Medical Officer) • PHC Primary Hub';
      }} else {{
        inputUser.value = 'OFFICER-DIST-881';
        document.getElementById('dashUserSubtitle').innerText = 'Pooja Singh (Block Health Officer) • Surveillance Unit';
      }}
    }}

    function togglePasswordVisibility() {{
      const p = document.getElementById('inputPassword');
      p.type = p.type === 'password' ? 'text' : 'password';
    }}

    function handleFormSubmit(e) {{
      e.preventDefault();
      document.getElementById('viewLogin').classList.add('hidden');
      document.getElementById('viewDashboard').classList.remove('hidden');
      showToast('Authenticated', 'Welcome to ArogyaSaathi! DPDP Act 2023 session active.');
    }}

    function signOutToLogin() {{
      document.getElementById('viewDashboard').classList.add('hidden');
      document.getElementById('viewLogin').classList.remove('hidden');
      showToast('Signed Out', 'Safely signed out from clinical session.');
    }}

    function setDashTab(tab) {{
      const tabs = ['triage', 'vitals', 'roster', 'outbreak'];
      tabs.forEach(t => {{
        const btn = document.getElementById('tabBtn' + t.charAt(0).toUpperCase() + t.slice(1));
        const content = document.getElementById('dashTab' + t.charAt(0).toUpperCase() + t.slice(1));
        if (t === tab) {{
          btn.className = 'px-4 py-2 rounded-xl font-bold text-xs bg-[#007953] text-white shadow-sm transition-all flex items-center gap-1.5';
          content.classList.remove('hidden');
        }} else {{
          btn.className = 'px-4 py-2 rounded-xl font-bold text-xs bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-all flex items-center gap-1.5';
          content.classList.add('hidden');
        }}
      }});
    }}

    function triggerEmergency108() {{
      alert("🚨 PRIORITY 108 AMBULANCE DISPATCH\\n\\nGPS Coordinates Transmitted: 25.3210° N, 82.9812° E (Rampur)\\n• Patient Pseudonym: HASH-RAMPUR-101\\n• Suspected Diagnosis: Acute Coronary Syndrome\\n• Ambulance ETA: 12 minutes");
    }}

    function showToast(title, message, isAlert = false) {{
      const toast = document.getElementById('toastNotification');
      document.getElementById('toastTitle').innerText = title;
      document.getElementById('toastMessage').innerText = message;
      document.getElementById('toastIcon').innerText = isAlert ? '⚠️' : '✓';
      toast.classList.remove('translate-y-24', 'opacity-0');
      setTimeout(() => {{
        toast.classList.add('translate-y-24', 'opacity-0');
      }}, 3200);
    }}

    // Triage simulation
    let isRecording = false;
    function toggleTriageMic() {{
      isRecording = !isRecording;
      const btn = document.getElementById('micBtn');
      const text = document.getElementById('micStatusText');
      if (isRecording) {{
        btn.className = 'w-20 h-20 rounded-full bg-red-600 text-white flex items-center justify-center text-3xl shadow-lg shadow-red-500/40 animate-pulse';
        text.innerText = 'Listening to patient speech input (Hindi)...';
        setTimeout(() => {{
          runTriageSpeech('सीने में बहुत तेज दर्द है और बहुत पसीना आ रहा है');
        }}, 2000);
      }} else {{
        btn.className = 'w-20 h-20 rounded-full bg-[#007953] hover:bg-[#006646] text-white flex items-center justify-center text-3xl shadow-lg shadow-[#007953]/30';
        text.innerText = 'Tap to Start Speech Symptom Check';
      }}
    }}

    function runTriageSpeech(transcript) {{
      isRecording = false;
      const btn = document.getElementById('micBtn');
      const text = document.getElementById('micStatusText');
      btn.className = 'w-20 h-20 rounded-full bg-[#007953] hover:bg-[#006646] text-white flex items-center justify-center text-3xl shadow-lg shadow-[#007953]/30';
      text.innerText = 'Processed: "' + transcript + '"';

      if (transcript.includes('सीने में बहुत तेज दर्द')) {{
        document.getElementById('triageAlertBanner').classList.remove('hidden');
        document.getElementById('guidedQuestionCard').classList.add('hidden');
        showToast('Red Flag Alert', 'Chest pain cluster detected. 108 activated.', true);
      }} else if (transcript.includes('बुखार')) {{
        document.getElementById('triageAlertBanner').classList.add('hidden');
        document.getElementById('guidedQuestionCard').classList.remove('hidden');
        showToast('Negation Parsed', 'Clause-aware check verified: no neck stiffness.');
      }} else {{
        document.getElementById('triageAlertBanner').classList.remove('hidden');
        document.getElementById('guidedQuestionCard').classList.add('hidden');
        showToast('Child Danger Sign', 'Dehydration red flag detected.', true);
      }}
    }}

    function answerQuestion(ans) {{
      showToast('Logged', 'Recorded: ' + ans + '. Decision updated.');
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

print('Both web files written successfully!')
