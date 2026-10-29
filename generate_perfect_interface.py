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
    .phone-bezel {{
      box-shadow: 0 0 0 10px #1e293b, 0 25px 60px -15px rgba(0,0,0,0.3);
    }}
    .tablet-bezel {{
      box-shadow: 0 0 0 14px #1e293b, 0 30px 70px -15px rgba(0,0,0,0.25);
    }}
  </style>
</head>
<body class="bg-[#DFEDE6] text-slate-800 antialiased min-h-screen p-2 sm:p-6 transition-all duration-300">

  <!-- ============================================================== -->
  <!-- TOP RESPONSIVE PREVIEW CONTROLS & RESIZER TOOLBAR -->
  <!-- ============================================================== -->
  <div class="max-w-5xl mx-auto mb-4 bg-white/95 backdrop-blur-md rounded-2xl border border-[#CCE2D6] p-3 shadow-md flex flex-wrap items-center justify-between gap-3 text-xs">
    
    <!-- Left: Preset Width Buttons -->
    <div class="flex items-center gap-2">
      <span class="font-extrabold text-[#007953] flex items-center gap-1">
        <span>📐</span>
        <span>Viewport:</span>
      </span>
      
      <!-- Mobile Button (Default Mobile View) -->
      <button onclick="setViewportWidth(390, 'mobile')" id="btnPresetMobile" class="px-3 py-1.5 rounded-xl font-extrabold bg-[#007953] text-white shadow-xs transition-all flex items-center gap-1.5">
        <span>📱</span>
        <span>Mobile (390px)</span>
      </button>

      <!-- Tablet Button -->
      <button onclick="setViewportWidth(768, 'tablet')" id="btnPresetTablet" class="px-3 py-1.5 rounded-xl font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all flex items-center gap-1.5">
        <span>📲</span>
        <span>Tablet (768px)</span>
      </button>

      <!-- Desktop Button -->
      <button onclick="setViewportWidth(1024, 'desktop')" id="btnPresetDesktop" class="px-3 py-1.5 rounded-xl font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all flex items-center gap-1.5">
        <span>💻</span>
        <span>Desktop (1024px)</span>
      </button>

      <!-- Fluid 100% Button -->
      <button onclick="setViewportWidth('100%', 'fluid')" id="btnPresetFluid" class="hidden sm:flex px-3 py-1.5 rounded-xl font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all items-center gap-1.5">
        <span>🖥️</span>
        <span>Fluid (100%)</span>
      </button>
    </div>

    <!-- Center/Right: Interactive Width Drag Slider & Current Width Badge -->
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="text-slate-500 font-semibold hidden md:inline">Drag to Resize:</span>
        <input type="range" id="widthSlider" min="360" max="1060" value="390" step="10" oninput="onSliderResize(this.value)" class="w-28 sm:w-40 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#007953]" />
      </div>

      <span id="widthLabel" class="px-2.5 py-1 rounded-lg bg-emerald-50 text-[#007953] font-black border border-emerald-200 text-[11px]">
        📱 390px (Mobile)
      </span>

      <!-- Frame Chassis Bezel Toggle -->
      <button onclick="toggleDeviceBezel()" id="btnBezelToggle" class="px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 font-bold text-[11px] flex items-center gap-1">
        <span>🔘</span>
        <span id="bezelLabel">Bezel: On</span>
      </button>
    </div>

  </div>

  <!-- ============================================================== -->
  <!-- MAIN RESIZABLE CONTAINER -->
  <!-- ============================================================== -->
  <div id="deviceWrapper" class="mx-auto transition-all duration-300 ease-out flex justify-center items-center" style="max-width: 390px;">
    
    <div id="deviceFrame" class="w-full bg-white rounded-[32px] sm:rounded-[36px] overflow-hidden border border-[#D5E8DE] shadow-[0_25px_60px_-15px_rgba(0,121,83,0.22)] relative phone-bezel">

      <!-- Mobile Simulated Status Bar (Clock, 5G, Battery) -->
      <div id="mobileStatusBar" class="bg-slate-900 text-slate-300 px-6 py-2 flex justify-between items-center text-[11px] font-semibold tracking-wider select-none">
        <span id="statusBarClock">09:41</span>
        <div class="w-16 h-4 bg-slate-800 rounded-full mx-auto"></div>
        <div class="flex items-center gap-1.5">
          <span class="text-emerald-400 font-bold">5G</span>
          <span>📶</span>
          <span>🔋 98%</span>
        </div>
      </div>

      <!-- ============================================================ -->
      <!-- VIEW 1: AUTH LOGIN SCREEN (RESPONSIVE FOR MOBILE & TABLET) -->
      <!-- ============================================================ -->
      <div id="viewLogin" class="w-full relative bg-white">
        
        <!-- =============================== -->
        <!-- MOBILE LAYOUT (Active < 720px) -->
        <!-- =============================== -->
        <div id="mobileLoginLayout" class="p-5 flex flex-col justify-between">
          
          <!-- Mobile Brand Header -->
          <div class="flex justify-between items-center mb-4">
            <div class="flex items-center gap-2.5">
              <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-[#00895D] to-[#005B3E] flex items-center justify-center text-white shadow-xs">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                  <path d="M12 9v6m-3-3h6"/>
                </svg>
              </div>
              <div>
                <h1 class="text-lg font-black text-[#0B4734] leading-tight">ArogyaSaathi</h1>
                <p class="text-[10px] text-[#52796F] font-bold">Healthy Villages • Stronger Communities</p>
              </div>
            </div>

            <!-- Language Switcher Dropdown (Mobile) -->
            <button onclick="toggleLangMenu()" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl border border-slate-200 bg-white text-[11px] font-bold text-slate-700 shadow-xs">
              <span>🌐</span>
              <span class="langCurrent">English</span>
              <span>▾</span>
            </button>
          </div>

          <!-- Mobile Hero Banner Card (Photo + Slogan) -->
          <div class="relative rounded-2xl overflow-hidden bg-gradient-to-br from-[#EAF5EF] to-[#D5EFE1] p-3.5 border border-[#C6E5D4] mb-4 shadow-xs">
            <div class="flex items-center gap-3">
              <div class="w-24 h-24 rounded-xl overflow-hidden shadow-sm shrink-0 border-2 border-white">
                <img src="data:image/jpeg;base64,{photo_b64}" alt="ASHA Worker" class="w-full h-full object-cover" />
              </div>
              <div>
                <h2 class="text-base font-black text-[#0C3829] leading-snug">
                  Better Care<br/>
                  <span class="text-[#007953]">Closer to Every Home</span>
                </h2>
                <div class="mt-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-white/90 border border-[#BEDECB] text-[10px] font-extrabold text-[#007953] italic">
                  <span>🌿 Swasth Gaon • Sashakt Bharat</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Welcome Header -->
          <div class="mb-4">
            <h3 class="text-xl font-black text-slate-900 tracking-tight">Welcome Back</h3>
            <p class="text-xs text-slate-500 font-medium">Sign in to continue to ArogyaSaathi</p>
          </div>

          <!-- 3 Role Tabs (Horizontal Row for Thumb Touch) -->
          <div class="grid grid-cols-3 gap-2 mb-4">
            <!-- ASHA / ANM -->
            <button type="button" onclick="selectRole('ASHA')" class="roleBtnMobileASHA p-2.5 rounded-xl bg-[#E8F7F0] border-2 border-[#007953] flex flex-col items-center text-center transition-all shadow-xs">
              <span class="text-base mb-0.5">👩‍⚕️</span>
              <span class="text-[11px] font-black text-[#007953] leading-tight">ASHA / ANM</span>
            </button>

            <!-- Doctor -->
            <button type="button" onclick="selectRole('DOCTOR')" class="roleBtnMobileDOCTOR p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center text-center transition-all">
              <span class="text-base mb-0.5">🩺</span>
              <span class="text-[11px] font-semibold text-slate-600 leading-tight">Doctor</span>
            </button>

            <!-- Health Officer -->
            <button type="button" onclick="selectRole('OFFICER')" class="roleBtnMobileOFFICER p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center text-center transition-all">
              <span class="text-base mb-0.5">👥</span>
              <span class="text-[11px] font-semibold text-slate-600 leading-tight">Health Officer</span>
            </button>
          </div>

          <!-- Form Fields -->
          <form onsubmit="handleFormSubmit(event)" class="space-y-3">
            <div>
              <div class="relative flex items-center">
                <span class="absolute left-3 text-slate-400 text-sm">👤</span>
                <input id="inputUserMobile" type="text" value="ASHA-RAMPUR-7821" required placeholder="Username / Mobile Number" class="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-300 focus:border-[#007953] focus:ring-2 focus:ring-[#007953]/20 text-xs font-semibold text-slate-800 placeholder-slate-400 outline-none" />
              </div>
            </div>

            <div>
              <div class="relative flex items-center">
                <span class="absolute left-3 text-slate-400 text-sm">🔒</span>
                <input id="inputPasswordMobile" type="password" value="1234" required placeholder="Password" class="w-full pl-9 pr-10 py-2.5 rounded-xl border border-slate-300 focus:border-[#007953] focus:ring-2 focus:ring-[#007953]/20 text-xs font-semibold text-slate-800 placeholder-slate-400 outline-none" />
                <button type="button" onclick="togglePasswordVisibilityMobile()" class="absolute right-3 text-slate-400 hover:text-slate-600 text-xs">👁️</button>
              </div>
            </div>

            <div class="flex items-center justify-between text-xs">
              <label class="flex items-center gap-1.5 text-slate-600 font-semibold cursor-pointer">
                <input type="checkbox" checked class="w-3.5 h-3.5 accent-[#007953] rounded" />
                <span>Remember me</span>
              </label>
              <button type="button" onclick="showToast('Password Reset', 'OTP dispatched to registered mobile')" class="font-bold text-[#007953] hover:underline text-[11px]">Forgot password?</button>
            </div>

            <button type="submit" class="w-full py-3 bg-[#007953] hover:bg-[#006646] active:scale-[0.98] text-white font-extrabold text-sm rounded-xl shadow-md shadow-[#007953]/20 flex items-center justify-center gap-2 transition-all">
              <span>Sign In</span>
              <span>➔</span>
            </button>
          </form>

          <!-- Mobile Security Pill -->
          <div class="mt-4 bg-[#F4FAF6] border border-[#D3EBDD] rounded-xl p-2.5 flex items-center gap-2.5">
            <span class="text-[#007953] text-lg shrink-0">🛡️</span>
            <div>
              <h4 class="text-[11px] font-extrabold text-slate-800">Secure • Private • For Better Healthcare</h4>
              <p class="text-[10px] text-slate-500 font-medium leading-tight">Your data is safe and used only for healthcare purposes.</p>
            </div>
          </div>

        </div>

        <!-- ============================================== -->
        <!-- TABLET & DESKTOP SPLIT LAYOUT (Active >= 720px) -->
        <!-- ============================================== -->
        <div id="desktopLoginLayout" class="hidden grid-cols-12 min-h-[600px]">
          
          <!-- Left Hero Section (60%) -->
          <div class="col-span-7 relative bg-gradient-to-br from-[#F4FAF6] via-[#E8F6EF] to-[#DDF1E7] p-8 flex flex-col justify-between overflow-hidden">
            <div class="relative z-10">
              <div class="flex items-center gap-3">
                <div class="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#00895D] to-[#005B3E] flex items-center justify-center text-white shadow-md">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                    <path d="M12 9v6m-3-3h6"/>
                  </svg>
                </div>
                <div>
                  <h1 class="text-2xl font-black text-[#0B4734] leading-none">ArogyaSaathi</h1>
                  <p class="text-xs text-[#52796F] font-bold mt-0.5">Healthy Villages • Stronger Communities</p>
                </div>
              </div>

              <div class="mt-8">
                <h2 class="text-3xl font-black text-[#0C3829] leading-tight">
                  Better Care<br/>
                  <span class="text-[#007953]">Closer to Every Home</span>
                </h2>
              </div>
            </div>

            <!-- Photo & Tricolor Badge -->
            <div class="relative z-10 mt-6 flex items-end justify-between gap-3">
              <div class="w-56 h-40 rounded-2xl overflow-hidden shadow-lg border-2 border-white">
                <img src="data:image/jpeg;base64,{photo_b64}" alt="ASHA Worker" class="w-full h-full object-cover" />
              </div>
              <div class="bg-white/95 p-3 rounded-2xl border border-[#CDE5D8] shadow-sm max-w-[180px]">
                <div class="text-[11px] font-black text-[#007953] italic">Swasth Gaon</div>
                <div class="text-[11px] font-black text-[#0C3829] italic">Sashakt Bharat</div>
                <div class="flex items-center gap-1 mt-1">
                  <span class="w-3 h-1 bg-[#FF9933] rounded-full"></span>
                  <span class="w-3 h-1 bg-white border border-slate-300 rounded-full"></span>
                  <span class="w-3 h-1 bg-[#138808] rounded-full"></span>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Login Form Section (40%) -->
          <div class="col-span-5 p-8 flex flex-col justify-between bg-white">
            <div>
              <div class="flex justify-end mb-4">
                <button onclick="toggleLangMenu()" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-700">
                  <span>🌐</span>
                  <span class="langCurrent">English</span>
                  <span>▾</span>
                </button>
              </div>

              <h3 class="text-2xl font-black text-slate-900 tracking-tight">Welcome Back</h3>
              <p class="text-xs text-slate-500 font-medium mt-0.5 mb-5">Sign in to continue to ArogyaSaathi</p>

              <!-- 3 Role Tabs -->
              <div class="grid grid-cols-3 gap-2 mb-4">
                <button type="button" onclick="selectRole('ASHA')" class="roleBtnDesktopASHA p-2.5 rounded-xl bg-[#E8F7F0] border-2 border-[#007953] flex flex-col items-center text-center shadow-xs">
                  <span class="text-sm mb-0.5">👩‍⚕️</span>
                  <span class="text-[11px] font-black text-[#007953]">ASHA / ANM</span>
                </button>
                <button type="button" onclick="selectRole('DOCTOR')" class="roleBtnDesktopDOCTOR p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center text-center">
                  <span class="text-sm mb-0.5">🩺</span>
                  <span class="text-[11px] font-semibold text-slate-600">Doctor</span>
                </button>
                <button type="button" onclick="selectRole('OFFICER')" class="roleBtnDesktopOFFICER p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center text-center">
                  <span class="text-sm mb-0.5">👥</span>
                  <span class="text-[11px] font-semibold text-slate-600">Health Officer</span>
                </button>
              </div>

              <!-- Form Inputs -->
              <form onsubmit="handleFormSubmit(event)" class="space-y-3">
                <input id="inputUserDesktop" type="text" value="ASHA-RAMPUR-7821" required placeholder="Username / Mobile Number" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-[#007953] text-xs font-semibold text-slate-800 outline-none" />
                <input id="inputPasswordDesktop" type="password" value="1234" required placeholder="Password" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:border-[#007953] text-xs font-semibold text-slate-800 outline-none" />

                <div class="flex items-center justify-between text-xs pt-1">
                  <label class="flex items-center gap-1.5 text-slate-600 font-semibold cursor-pointer">
                    <input type="checkbox" checked class="w-3.5 h-3.5 accent-[#007953] rounded" />
                    <span>Remember me</span>
                  </label>
                  <button type="button" onclick="showToast('Password Reset', 'OTP dispatched to registered mobile')" class="font-bold text-[#007953] hover:underline text-[11px]">Forgot password?</button>
                </div>

                <button type="submit" class="w-full py-3 bg-[#007953] hover:bg-[#006646] text-white font-extrabold text-sm rounded-xl shadow-md shadow-[#007953]/20 flex items-center justify-center gap-2">
                  <span>Sign In</span>
                  <span>➔</span>
                </button>
              </form>
            </div>

            <div class="mt-4 bg-[#F4FAF6] border border-[#D3EBDD] rounded-xl p-2.5 flex items-center gap-2.5">
              <span class="text-[#007953] text-base shrink-0">🛡️</span>
              <div>
                <h4 class="text-[11px] font-extrabold text-slate-800">Secure • Private • For Better Healthcare</h4>
                <p class="text-[10px] text-slate-500 font-medium">Your data is safe and used only for healthcare purposes.</p>
              </div>
            </div>
          </div>

        </div>

      </div>

      <!-- ============================================================ -->
      <!-- VIEW 2: AUTHENTICATED DECISION DASHBOARD (POST LOGIN) -->
      <!-- ============================================================ -->
      <div id="viewDashboard" class="hidden min-h-[580px] bg-slate-50 p-4 sm:p-6 animate-fade-in">
        
        <!-- Dashboard Top Header Bar -->
        <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-slate-200 shadow-xs mb-4">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-xl bg-[#007953] flex items-center justify-center text-white font-bold text-base shadow-sm">
              ⚕️
            </div>
            <div>
              <div class="flex items-center gap-1.5">
                <h2 class="font-extrabold text-sm text-slate-900 leading-tight">ArogyaSaathi Gateway</h2>
                <span class="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">DPDP 2023</span>
              </div>
              <p class="text-[10px] text-slate-500 font-semibold" id="dashUserSubtitle">Sunita Sharma (ASHA) • Rampur Sub-Centre Gateway</p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button onclick="triggerEmergency108()" class="px-2.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-black text-xs shadow-xs flex items-center gap-1 active:scale-95 transition-all">
              <span>🚨 108 SOS</span>
            </button>
            <button onclick="signOutToLogin()" class="px-2.5 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-1">
              <span>Sign Out</span>
              <span>➔</span>
            </button>
          </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="flex gap-1.5 overflow-x-auto pb-2 mb-4 text-xs font-bold">
          <button onclick="setDashTab('triage')" id="tabBtnTriage" class="px-3 py-1.5 rounded-xl bg-[#007953] text-white shadow-xs shrink-0">
            🎙️ Voice Triage
          </button>
          <button onclick="setDashTab('vitals')" id="tabBtnVitals" class="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shrink-0">
            📈 Vitals Curves
          </button>
          <button onclick="setDashTab('roster')" id="tabBtnRoster" class="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shrink-0">
            📋 ASHA Roster
          </button>
          <button onclick="setDashTab('outbreak')" id="tabBtnOutbreak" class="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shrink-0">
            🗺️ Outbreak Radar
          </button>
        </div>

        <!-- Tab 1: Voice Triage Screen -->
        <div id="dashTabTriage" class="space-y-3">
          <div id="triageAlertBanner" class="hidden p-3.5 rounded-2xl bg-red-50 border-2 border-red-500 text-red-900 shadow-xs">
            <div class="flex items-start gap-2.5">
              <span class="text-xl">🚨</span>
              <div class="flex-1">
                <span class="text-[10px] font-black uppercase text-red-600">CRITICAL RED FLAG DETECTED</span>
                <h4 class="font-extrabold text-xs text-red-950 mt-0.5">Acute Coronary Syndrome: Chest Pain + Sweating</h4>
                <p class="text-[11px] text-red-800 mt-0.5">Zero unvalidated prescription risk. Direct 108 ambulance transfer required.</p>
                <div class="mt-2 flex gap-2">
                  <button onclick="triggerEmergency108()" class="px-3 py-1.5 bg-red-600 text-white font-bold text-xs rounded-lg">Dispatch 108</button>
                  <button onclick="document.getElementById('triageAlertBanner').classList.add('hidden')" class="px-2.5 py-1.5 bg-red-100 text-red-800 font-bold text-xs rounded-lg">Dismiss</button>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-2xl p-5 border border-slate-200 text-center shadow-xs">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Speech Symptom Triage</span>
            <p class="text-xs text-slate-600 mb-3">Patient speaks symptoms in Hindi or English (Clause-aware negation)</p>

            <button id="micBtn" onclick="toggleTriageMic()" class="w-16 h-16 rounded-full bg-[#007953] hover:bg-[#006646] text-white flex items-center justify-center text-2xl shadow-md mx-auto active:scale-95 transition-transform">
              🎙️
            </button>
            <div class="mt-2 text-xs font-bold text-slate-700" id="micStatusText">Tap to Start Speech Triage</div>

            <div class="mt-4 pt-3 border-t border-slate-100 text-left">
              <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Preset Spoken Input:</span>
              <div class="flex flex-wrap gap-1.5">
                <button onclick="runTriageSpeech('सीने में बहुत तेज दर्द है और बहुत पसीना आ रहा है')" class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-[#E8F7F0] hover:text-[#007953] border border-slate-200">
                  "सीने में तेज दर्द + पसीना"
                </button>
                <button onclick="runTriageSpeech('3 दिन से तेज बुखार है लेकिन गर्दन में कोई अकड़न नहीं है')" class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-[#E8F7F0] hover:text-[#007953] border border-slate-200">
                  "3 दिन बुखार, अकड़न नहीं" (Negation)
                </button>
              </div>
            </div>
          </div>

          <!-- Guided Yes/No Question Card -->
          <div id="guidedQuestionCard" class="hidden bg-white border-2 border-[#007953] rounded-2xl p-4 shadow-xs">
            <span class="text-[9px] font-black uppercase text-[#007953] bg-[#E8F7F0] px-2 py-0.5 rounded">Guided Clinical Question</span>
            <h4 class="font-bold text-xs text-slate-900 mt-1">क्या सांस लेने में घरघराहट या पसलियां चलने की समस्या है?</h4>
            <div class="grid grid-cols-2 gap-2 mt-3">
              <button onclick="answerQuestion('हां (Yes)')" class="py-2.5 bg-[#007953] text-white font-bold text-xs rounded-xl shadow-xs">✓ हां (Yes)</button>
              <button onclick="answerQuestion('नहीं (No)')" class="py-2.5 bg-slate-100 text-slate-800 font-bold text-xs rounded-xl">✕ नहीं (No)</button>
            </div>
          </div>
        </div>

        <!-- Tab 2: Vitals Curves Screen -->
        <div id="dashTabVitals" class="hidden space-y-3">
          <div class="bg-amber-50 border border-amber-300 rounded-xl p-3 text-xs text-amber-900">
            <strong>12-Day Early Warning:</strong> Accelerating systolic velocity (+1.8 mmHg/day). Predicted crisis in 12 days.
          </div>
          <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
            <div class="flex justify-between items-center mb-2">
              <span class="text-xs font-bold text-slate-900">30-Day BP History (mmHg)</span>
              <span class="text-[9px] text-red-600 font-bold border border-red-200 bg-red-50 px-1.5 py-0.5 rounded">140 Limit</span>
            </div>
            <div class="w-full h-36 bg-slate-50 rounded-xl p-2 border border-slate-100">
              <svg class="w-full h-full" viewBox="0 0 320 120">
                <line x1="10" y1="48" x2="310" y2="48" stroke="#EF4444" stroke-width="1.5" stroke-dasharray="4" />
                <path d="M 20 75 Q 70 70 120 62 T 220 40 T 290 18" fill="none" stroke="#007953" stroke-width="3" />
                <circle cx="20" cy="75" r="4" fill="#007953" />
                <circle cx="120" cy="62" r="4" fill="#007953" />
                <circle cx="220" cy="40" r="4.5" fill="#EF4444" />
                <circle cx="290" cy="18" r="5" fill="#DC2626" />
                <text x="268" y="14" fill="#DC2626" font-size="10" font-weight="900">184</text>
              </svg>
            </div>
          </div>
        </div>

        <!-- Tab 3: Roster Screen -->
        <div id="dashTabRoster" class="hidden space-y-2.5">
          <div class="bg-white p-3.5 rounded-xl border-2 border-red-200 shadow-xs">
            <div class="flex justify-between items-start text-xs">
              <span class="px-1.5 py-0.5 rounded text-[9px] font-black bg-red-100 text-red-700">CRITICAL</span>
              <span class="font-bold text-slate-900">HASH-RAMPUR-101 (58y/M)</span>
            </div>
            <p class="text-[11px] text-slate-700 mt-1">BP spike (184/110) & severe headache. Home visit due today.</p>
            <div class="flex justify-end gap-2 mt-2">
              <button onclick="alert('Calling registered phone for HASH-RAMPUR-101')" class="text-[11px] font-bold px-2.5 py-1 rounded-lg border border-slate-200">📞 Call</button>
              <button onclick="showToast('Visit Logged', 'Completed visit for HASH-RAMPUR-101')" class="text-[11px] font-bold px-2.5 py-1 rounded-lg bg-[#007953] text-white">Mark Done</button>
            </div>
          </div>
        </div>

        <!-- Tab 4: Outbreak Radar Screen -->
        <div id="dashTabOutbreak" class="hidden space-y-3">
          <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs text-xs">
            <div class="flex justify-between items-center mb-2">
              <span class="font-bold text-slate-900">Spatio-Temporal Radar</span>
              <span class="text-[9px] font-black text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.5 rounded">Z = 3.42 WARNING</span>
            </div>
            <div class="w-full h-36 bg-slate-900 rounded-xl relative overflow-hidden flex items-center justify-center">
              <div class="absolute w-20 h-20 border border-emerald-500/30 rounded-full"></div>
              <div class="absolute w-32 h-32 border border-emerald-500/20 rounded-full"></div>
              <div class="absolute w-36 h-36 rounded-full pointer-events-none radar-sweep" style="background: conic-gradient(from 0deg, rgba(16, 185, 129, 0.4) 0deg, transparent 60deg, transparent 360deg);"></div>
              <div class="w-3 h-3 bg-emerald-400 rounded-full"></div>
              <div class="absolute top-4 right-10 flex flex-col items-center">
                <div class="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></div>
                <span class="text-[8px] text-red-400 font-bold mt-1">Rampur (Z=3.42)</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>

  </div>

  <!-- Toast Notification -->
  <div id="toastNotification" class="fixed bottom-4 right-4 z-50 transform translate-y-24 opacity-0 transition-all duration-300 max-w-xs bg-slate-900 text-white p-3 rounded-xl shadow-xl border border-slate-700 flex items-start gap-2.5 text-xs">
    <div id="toastIcon" class="text-emerald-400 text-lg font-bold">✓</div>
    <div>
      <div id="toastTitle" class="font-bold">Notice</div>
      <div id="toastMessage" class="text-slate-300 text-[11px] mt-0.5">Description</div>
    </div>
  </div>

  <script>
    let currentMode = 'mobile';
    let isBezelActive = true;
    let activeRole = 'ASHA';

    function setViewportWidth(val, mode) {{
      currentMode = mode;
      const wrapper = document.getElementById('deviceWrapper');
      const slider = document.getElementById('widthSlider');
      const label = document.getElementById('widthLabel');
      
      const buttons = ['Mobile', 'Tablet', 'Desktop', 'Fluid'];
      buttons.forEach(b => {{
        const btn = document.getElementById('btnPreset' + b);
        if (b.toLowerCase() === mode) {{
          btn.className = 'px-3 py-1.5 rounded-xl font-extrabold bg-[#007953] text-white shadow-xs transition-all flex items-center gap-1.5';
        }} else {{
          btn.className = 'px-3 py-1.5 rounded-xl font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all flex items-center gap-1.5';
        }}
      }});

      if (val === '100%') {{
        wrapper.style.maxWidth = '100%';
        slider.value = 1060;
        label.innerText = '🖥️ Fluid (100%)';
        adaptInternalLayout(1024);
      }} else {{
        wrapper.style.maxWidth = val + 'px';
        slider.value = val;
        label.innerText = (val < 500 ? '📱 ' : (val < 850 ? '📲 ' : '💻 ')) + val + 'px';
        adaptInternalLayout(val);
      }}
    }}

    function onSliderResize(val) {{
      const wrapper = document.getElementById('deviceWrapper');
      const label = document.getElementById('widthLabel');
      wrapper.style.maxWidth = val + 'px';
      label.innerText = (val < 500 ? '📱 ' : (val < 850 ? '📲 ' : '💻 ')) + val + 'px';
      adaptInternalLayout(val);
    }}

    function adaptInternalLayout(width) {{
      const mobileLayout = document.getElementById('mobileLoginLayout');
      const desktopLayout = document.getElementById('desktopLoginLayout');
      const statusBar = document.getElementById('mobileStatusBar');

      if (width < 720) {{
        mobileLayout.classList.remove('hidden');
        desktopLayout.classList.add('hidden');
        desktopLayout.classList.remove('grid');
        statusBar.classList.remove('hidden');
      }} else {{
        mobileLayout.classList.add('hidden');
        desktopLayout.classList.remove('hidden');
        desktopLayout.classList.add('grid');
        statusBar.classList.add('hidden');
      }}
    }}

    function toggleDeviceBezel() {{
      isBezelActive = !isBezelActive;
      const frame = document.getElementById('deviceFrame');
      const label = document.getElementById('bezelLabel');
      if (isBezelActive) {{
        frame.className = 'w-full bg-white rounded-[32px] sm:rounded-[36px] overflow-hidden border border-[#D5E8DE] shadow-[0_25px_60px_-15px_rgba(0,121,83,0.22)] relative phone-bezel';
        label.innerText = 'Bezel: On';
      }} else {{
        frame.className = 'w-full bg-white rounded-2xl overflow-hidden border border-[#D5E8DE] shadow-lg relative';
        label.innerText = 'Bezel: Off';
      }}
    }}

    function selectRole(role) {{
      activeRole = role;
      const roles = ['ASHA', 'DOCTOR', 'OFFICER'];
      roles.forEach(r => {{
        const mBtn = document.querySelector('.roleBtnMobile' + r);
        const dBtn = document.querySelector('.roleBtnDesktop' + r);
        const isSel = (r === role);

        if (mBtn) {{
          mBtn.className = isSel
            ? 'roleBtnMobile' + r + ' p-2.5 rounded-xl bg-[#E8F7F0] border-2 border-[#007953] flex flex-col items-center text-center shadow-xs'
            : 'roleBtnMobile' + r + ' p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center text-center';
        }}
        if (dBtn) {{
          dBtn.className = isSel
            ? 'roleBtnDesktop' + r + ' p-2.5 rounded-xl bg-[#E8F7F0] border-2 border-[#007953] flex flex-col items-center text-center shadow-xs'
            : 'roleBtnDesktop' + r + ' p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 flex flex-col items-center text-center';
        }}
      }});

      let defaultUser = 'ASHA-RAMPUR-7821';
      let title = 'Sunita Sharma (ASHA) • Rampur Sub-Centre Gateway';
      if (role === 'DOCTOR') {{
        defaultUser = 'DR-VERMA-PHC-402';
        title = 'Dr. Rajesh Verma (Medical Officer) • PHC Hub';
      }} else if (role === 'OFFICER') {{
        defaultUser = 'OFFICER-DIST-881';
        title = 'Pooja Singh (Health Officer) • Block Unit';
      }}

      document.getElementById('inputUserMobile').value = defaultUser;
      document.getElementById('inputUserDesktop').value = defaultUser;
      document.getElementById('dashUserSubtitle').innerText = title;
    }}

    function togglePasswordVisibilityMobile() {{
      const p = document.getElementById('inputPasswordMobile');
      p.type = p.type === 'password' ? 'text' : 'password';
    }}

    function toggleLangMenu() {{
      const labels = document.querySelectorAll('.langCurrent');
      const isEnglish = labels[0].innerText === 'English';
      labels.forEach(l => l.innerText = isEnglish ? 'हिन्दी' : 'English');
      showToast('Language Changed', isEnglish ? 'भाषा बदलकर हिन्दी कर दी गई है' : 'Language set to English');
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
          btn.className = 'px-3 py-1.5 rounded-xl bg-[#007953] text-white shadow-xs shrink-0';
          content.classList.remove('hidden');
        }} else {{
          btn.className = 'px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shrink-0';
          content.classList.add('hidden');
        }}
      }});
    }}

    function triggerEmergency108() {{
      alert("🚨 PRIORITY 108 AMBULANCE DISPATCH\\n\\nGPS: 25.3210° N, 82.9812° E (Rampur)\\n• Patient: HASH-RAMPUR-101\\n• ETA: 12 minutes");
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

    let isRecording = false;
    function toggleTriageMic() {{
      isRecording = !isRecording;
      const btn = document.getElementById('micBtn');
      const text = document.getElementById('micStatusText');
      if (isRecording) {{
        btn.className = 'w-16 h-16 rounded-full bg-red-600 text-white flex items-center justify-center text-2xl shadow-md mx-auto animate-pulse';
        text.innerText = 'Listening to patient speech (Hindi)...';
        setTimeout(() => {{
          runTriageSpeech('सीने में बहुत तेज दर्द है और बहुत पसीना आ रहा है');
        }}, 1800);
      }} else {{
        btn.className = 'w-16 h-16 rounded-full bg-[#007953] hover:bg-[#006646] text-white flex items-center justify-center text-2xl shadow-md mx-auto';
        text.innerText = 'Tap to Start Speech Triage';
      }}
    }}

    function runTriageSpeech(transcript) {{
      isRecording = false;
      const btn = document.getElementById('micBtn');
      const text = document.getElementById('micStatusText');
      btn.className = 'w-16 h-16 rounded-full bg-[#007953] hover:bg-[#006646] text-white flex items-center justify-center text-2xl shadow-md mx-auto';
      text.innerText = 'Processed: "' + transcript + '"';

      if (transcript.includes('सीने में बहुत तेज दर्द')) {{
        document.getElementById('triageAlertBanner').classList.remove('hidden');
        document.getElementById('guidedQuestionCard').classList.add('hidden');
        showToast('Red Flag Alert', 'Chest pain cluster detected. 108 activated.');
      }} else {{
        document.getElementById('triageAlertBanner').classList.add('hidden');
        document.getElementById('guidedQuestionCard').classList.remove('hidden');
        showToast('Negation Parsed', 'Clause-aware check verified.');
      }}
    }}

    function answerQuestion(ans) {{
      showToast('Logged', 'Recorded: ' + ans);
      document.getElementById('guidedQuestionCard').classList.add('hidden');
    }}

    // Init with 390px (Mobile mode)
    setViewportWidth(390, 'mobile');
  </script>
</body>
</html>
'''

with open('frontend/web/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

with open('/home/vivek/.gemini/antigravity/brain/d046502c-0133-47f6-9025-b3f5f77d8f92/arogya_interface.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Updated responsive mobile and tab-resizable interface created!')
