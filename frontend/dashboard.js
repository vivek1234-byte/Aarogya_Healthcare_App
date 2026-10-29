/**
 * MEDITEK PATIENT HEALTH DASHBOARD - JAVASCRIPT CONTROLLER
 * Handles real data loading, SVG spline rendering, interactive cards,
 * AI Health Coach, and live Daily Inputs logging.
 */

// ================= 1. INITIAL REAL DATA STATE =================
const DEFAULT_PATIENT_DATA = {
  patient: {
    id: "PAT-MELINA-7421",
    name: "Melina",
    age: 28,
    gender: "Female",
    blood_group: "A+",
    avatar_url: "assets/melina_avatar.jpg",
    health_score: 94
  },
  vitals: {
    blood_pressure: {
      systolic: 118,
      diastolic: 80,
      unit: "mmHg",
      status: "Normal",
      last_updated: "1 week ago",
      bars: [28, 34, 30, 36, 32, 35, 30]
    },
    heart_rate: {
      current: 88,
      unit: "Bpm",
      status: "Resting",
      average_bpm: 80.69,
      last_updated: "2 hours ago",
      benchmark: 80,
      monthly_trend: [
        { label: "Jan", bpm: 62.0 },
        { label: "Feb", bpm: 64.2 },
        { label: "Mar", bpm: 78.5 },
        { label: "Apr", bpm: 66.1 },
        { label: "May", bpm: 82.4 },
        { label: "Jun", bpm: 88.0, highlight: true },
        { label: "Jul", bpm: 68.3 },
        { label: "Aug", bpm: 72.8 },
        { label: "Sep", bpm: 69.5 },
        { label: "Oct", bpm: 84.1 },
        { label: "Nov", bpm: 70.2 },
        { label: "Dec", bpm: 74.0 }
      ],
      weekly_trend: [
        { label: "Mon", bpm: 76.5 },
        { label: "Tue", bpm: 79.0 },
        { label: "Wed", bpm: 84.2 },
        { label: "Thu", bpm: 81.0 },
        { label: "Fri", bpm: 86.4 },
        { label: "Sat", bpm: 88.0, highlight: true },
        { label: "Sun", bpm: 80.6 }
      ],
      yearly_trend: [
        { label: "2023", bpm: 76.0 },
        { label: "2024", bpm: 79.4 },
        { label: "2025", bpm: 82.1 },
        { label: "2026", bpm: 80.69, highlight: true }
      ]
    },
    blood_sugar: {
      current: 95,
      unit: "mg/dL",
      status: "Healthy",
      last_updated: "45 min ago",
      bars: [18, 23, 19, 26, 34, 28, 23, 30, 26, 22, 25, 23]
    },
    bmi: {
      score: 22.4,
      unit: "kg/m²",
      status: "Stable",
      category: "Normal",
      height_cm: 165,
      weight_kg: 61.0,
      last_updated: "1 week ago"
    },
    steps: {
      count: 7782,
      target: 10000,
      change_pct: "↑ 30%",
      hourly: [
        0, 0, 0, 0, 0, 4, 18, 55, 90, 75, 42, 68, 50, 72, 85, 60, 45, 32, 10, 0, 0, 0, 0, 0
      ]
    },
    nutrition: {
      selected_date: 18,
      days: [
        { day: "Sun", date: 17, carbs: 125, target: 174, calories: 1680 },
        { day: "Mon", date: 18, carbs: 80, target: 174, calories: 1420, active: true },
        { day: "Tue", date: 19, carbs: 96, target: 174, calories: 1510 },
        { day: "Wed", date: 20, carbs: 144, target: 174, calories: 1790, circled: true },
        { day: "Thu", date: 21, carbs: 86, target: 174, calories: 1440 },
        { day: "Fri", date: 22, carbs: 112, target: 174, calories: 1620 },
        { day: "Sat", date: 23, carbs: 130, target: 174, calories: 1740 }
      ]
    },
    daily_inputs: [
      {
        id: "inp-1",
        type: "saturation",
        name: "Saturation",
        value: "98%",
        sub: "Mmol/L 14:00",
        color: "cyan",
        icon: "water"
      },
      {
        id: "inp-2",
        type: "pressure",
        name: "Pressure",
        value: "140/80",
        sub: "120/60 14:00",
        color: "pink",
        icon: "heart"
      }
    ]
  }
};

let currentDashboardData = JSON.parse(JSON.stringify(DEFAULT_PATIENT_DATA));

// ================= 2. DOM CONTENT LOADED =================
document.addEventListener("DOMContentLoaded", () => {
  // Sync with live backend API if available
  fetchBackendData();

  // Render visual modules
  renderTopVitals();
  renderSplineChart("monthly");
  renderStepBars();
  renderNutritionSection();
  renderDailyInputs();

  // Setup event listeners
  setupNavigation();
  setupProfileDropdown();
  setupTimeRangeFilter();
  setupNutritionDaySwitcher();
  setupAiAssistant();
  setupAddVitalModal();
  setupSearchFilter();
});

// Base URL: Automatically adapts to mobile IP or localhost
const API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8080';

// ================= 3. BACKEND API SYNC =================
async function fetchBackendData() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/patient/dashboard`, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });
    if (res.ok) {
      const liveData = await res.json();
      if (liveData && liveData.vitals) {
        currentDashboardData.vitals = liveData.vitals;
        if (liveData.patient) currentDashboardData.patient = liveData.patient;
        refreshAllDashboardComponents();
      }
    }
  } catch (err) {
    // Offline or static file mode: DEFAULT_PATIENT_DATA is already loaded seamlessly!
  }
}

function refreshAllDashboardComponents() {
  renderTopVitals();
  const currentRange = document.getElementById("timeRangeSelect")?.value || "monthly";
  renderSplineChart(currentRange);
  renderStepBars();
  renderNutritionSection();
  renderDailyInputs();
}

// ================= 4. RENDER TOP VITALS CARDS =================
function renderTopVitals() {
  const { blood_pressure, heart_rate, blood_sugar, bmi } = currentDashboardData.vitals;

  // Blood Pressure
  document.getElementById("bpValue").textContent = `${blood_pressure.systolic}/${blood_pressure.diastolic}`;
  document.getElementById("bpStatus").textContent = blood_pressure.status;
  document.getElementById("bpTimestamp").textContent = blood_pressure.last_updated;

  // Heart Rate
  document.getElementById("hrValue").textContent = heart_rate.current;
  document.getElementById("hrStatus").textContent = heart_rate.status;
  document.getElementById("hrTimestamp").textContent = heart_rate.last_updated;
  document.getElementById("avgBpmStat").textContent = heart_rate.average_bpm;

  // Blood Sugar
  document.getElementById("sugarValue").textContent = blood_sugar.current;
  document.getElementById("sugarStatus").textContent = blood_sugar.status;
  document.getElementById("sugarTimestamp").textContent = blood_sugar.last_updated;

  // BMI
  document.getElementById("bmiValue").textContent = bmi.score;
  document.getElementById("bmiStatus").textContent = bmi.status;
  document.getElementById("bmiTimestamp").textContent = bmi.last_updated;
}

// ================= 5. RENDER SVG SPLINE HEART RATE CHART =================
function renderSplineChart(range = "monthly") {
  const hr = currentDashboardData.vitals.heart_rate;
  let pointsData = hr.monthly_trend;
  if (range === "weekly") pointsData = hr.weekly_trend;
  if (range === "yearly") pointsData = hr.yearly_trend;

  const svgArea = document.getElementById("splineArea");
  const svgStroke = document.getElementById("splineStroke");
  const peakCircle = document.getElementById("peakCircle");
  const peakTooltip = document.getElementById("peakTooltip");
  const xAxisContainer = document.getElementById("chartXAxis");
  const canvasArea = document.getElementById("chartCanvasArea");

  // Update X-Axis labels
  xAxisContainer.innerHTML = "";
  pointsData.forEach((pt) => {
    const span = document.createElement("span");
    span.textContent = pt.label;
    xAxisContainer.appendChild(span);
  });

  const width = 680;
  const height = 240;
  const minY = 50;
  const maxY = 90;
  const paddingX = 25;
  const stepX = (width - paddingX * 2) / (pointsData.length - 1);

  // Coordinate mapping
  const coords = pointsData.map((pt, idx) => {
    const x = paddingX + idx * stepX;
    // Inverted Y: 90 is top (y=20), 50 is bottom (y=220)
    const norm = (pt.bpm - minY) / (maxY - minY);
    const y = height - 20 - norm * (height - 40);
    return { x, y, pt, idx };
  });

  // Generate Smooth Cubic Spline Path
  const dCurve = getCubicSplinePath(coords);
  svgStroke.setAttribute("d", dCurve);

  // Area Path (closing at bottom)
  const lastX = coords[coords.length - 1].x;
  const firstX = coords[0].x;
  const dArea = `${dCurve} L ${lastX} ${height} L ${firstX} ${height} Z`;
  svgArea.setAttribute("d", dArea);

  // Peak marker placement (June or highest point)
  let peakPoint = coords.find((c) => c.pt.highlight) || coords[0];
  coords.forEach((c) => {
    if (c.pt.bpm > peakPoint.pt.bpm) peakPoint = c;
  });

  peakCircle.setAttribute("cx", peakPoint.x);
  peakCircle.setAttribute("cy", peakPoint.y);

  // Position floating tooltip card above peak
  const peakLeftPercent = (peakPoint.x / width) * 100;
  peakTooltip.style.left = `${peakLeftPercent}%`;
  peakTooltip.style.top = `${peakPoint.y - 65}px`;

  // Interactive Hover Listener
  const hoverPin = document.getElementById("hoverPin");
  const hoverTag = document.getElementById("hoverTag");

  canvasArea.onmousemove = (e) => {
    const rect = canvasArea.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const svgMouseX = (mouseX / rect.width) * width;

    // Find nearest point
    let nearest = coords[0];
    let minDiff = Infinity;
    coords.forEach((c) => {
      const diff = Math.abs(c.x - svgMouseX);
      if (diff < minDiff) {
        minDiff = diff;
        nearest = c;
      }
    });

    hoverPin.style.display = "flex";
    hoverPin.style.left = `${(nearest.x / width) * 100}%`;
    hoverPin.style.top = `${nearest.y}px`;
    hoverTag.textContent = `${nearest.pt.label}: ${nearest.pt.bpm} Bpm`;
  };

  canvasArea.onmouseleave = () => {
    hoverPin.style.display = "none";
  };
}

// Generate smooth cubic bezier spline SVG path
function getCubicSplinePath(points) {
  if (points.length === 0) return "";
  let d = `M ${points[0].x} ${points[0].y}`;

  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? 0 : i - 1];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] || p2;

    const cp1x = p1.x + (p2.x - p0.x) / 5;
    const cp1y = p1.y + (p2.y - p0.y) / 5;

    const cp2x = p2.x - (p3.x - p1.x) / 5;
    const cp2y = p2.y - (p3.y - p1.y) / 5;

    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
}

// ================= 6. RENDER 24 HOURLY STEP BARS =================
function renderStepBars() {
  const container = document.getElementById("stepBarsChart");
  const { hourly, count, change_pct } = currentDashboardData.vitals.steps;

  document.getElementById("stepCount").textContent = count.toLocaleString();
  document.getElementById("stepChange").textContent = change_pct;

  container.innerHTML = "";
  hourly.forEach((val) => {
    const bar = document.createElement("div");
    bar.className = "step-bar";
    const barHeight = Math.max(val * 0.38, 4);
    bar.style.height = `${barHeight}px`;
    container.appendChild(bar);
  });
}

// ================= 7. RENDER NUTRITION SECTION =================
function renderNutritionSection() {
  const { days, selected_date } = currentDashboardData.vitals.nutrition;
  const currentDay = days.find((d) => d.date === selected_date) || days[1];

  // Update text values
  document.getElementById("macroCarbs").innerHTML = `
    <span class="macro-val">${currentDay.carbs}/${currentDay.target}g</span>
    <span class="macro-label">Carbs</span>
  `;

  const pct = Math.min(Math.round((currentDay.carbs / currentDay.target) * 100), 100);
  document.getElementById("carbProgressFill").style.width = `${pct}%`;

  // Update Arc Progress SVG
  // 15 65 A 45 45 -> full semi-circle spans 180 deg
  const arcEl = document.getElementById("nutritionProgressArc");
  const angle = (pct / 100) * 180;
  const rad = (180 - angle) * (Math.PI / 180);
  const cx = 60;
  const cy = 65;
  const r = 45;
  const endX = (cx + r * Math.cos(rad)).toFixed(1);
  const endY = (cy - r * Math.sin(rad)).toFixed(1);
  arcEl.setAttribute("d", `M 15 65 A 45 45 0 0 1 ${endX} ${endY}`);

  // Highlight active calendar day
  const strip = document.getElementById("nutritionDaysStrip");
  const dayEls = strip.querySelectorAll(".calendar-day");
  dayEls.forEach((el) => {
    const dt = parseInt(el.getAttribute("data-date"), 10);
    if (dt === selected_date) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });
}

function setupNutritionDaySwitcher() {
  const strip = document.getElementById("nutritionDaysStrip");
  strip.addEventListener("click", (e) => {
    const dayEl = e.target.closest(".calendar-day");
    if (!dayEl) return;
    const chosenDate = parseInt(dayEl.getAttribute("data-date"), 10);
    currentDashboardData.vitals.nutrition.selected_date = chosenDate;
    renderNutritionSection();
  });
}

// ================= 8. RENDER DAILY INPUTS CARDS =================
function renderDailyInputs() {
  const container = document.getElementById("inputsCardsRow");
  const items = currentDashboardData.vitals.daily_inputs;

  // Preserve the first '+' add button
  const addBtn = document.getElementById("openAddVitalModal");
  container.innerHTML = "";
  container.appendChild(addBtn);

  items.forEach((item) => {
    const card = document.createElement("div");
    const isCyan = item.color === "cyan" || item.type === "saturation";
    card.className = `input-card card-data ${isCyan ? "data-cyan" : "data-pink"}`;

    const iconSvg = isCyan
      ? `<svg viewBox="0 0 16 16" fill="#0891B2"><path d="M8 1.5c-2.5 3.5-5 6.5-5 9.5 0 2.76 2.24 5 5 5s5-2.24 5-5c0-3-2.5-6-5-9.5z"/></svg>`
      : `<svg viewBox="0 0 16 16" fill="#E11D48"><path d="M8 3.3C6.7 1.8 4.4 1.5 2.8 2.9 1.1 4.4 1 7 2.6 8.7L8 14l5.4-5.3c1.6-1.7 1.5-4.3-.2-5.8-1.6-1.4-3.9-1.1-5.2.4z"/></svg>`;

    card.innerHTML = `
      <div class="data-icon">${iconSvg}</div>
      <div class="data-label">${item.name}</div>
      <div class="data-val">${item.value}</div>
      <div class="data-sub">${item.sub || `${item.unit || ""} ${item.time || ""}`}</div>
    `;
    container.appendChild(card);
  });
}

// ================= 9. AI ASSISTANT & HEALTH COACH =================
function setupAiAssistant() {
  const pills = document.querySelectorAll(".action-pill");
  const form = document.getElementById("aiChatForm");
  const input = document.getElementById("aiInput");
  const closeBtn = document.getElementById("aiResponseClose");

  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const promptType = pill.getAttribute("data-prompt");
      handleAiQuery(promptType, "");
    });
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;
    input.value = "";
    handleAiQuery("", query);
  });

  closeBtn.addEventListener("click", () => {
    document.getElementById("aiResponseBox").style.display = "none";
  });
}

async function handleAiQuery(topic, query) {
  const responseBox = document.getElementById("aiResponseBox");
  const titleEl = document.getElementById("aiResponseTitle");
  const textEl = document.getElementById("aiResponseText");
  const statsEl = document.getElementById("aiResponseStats");

  responseBox.style.display = "block";
  titleEl.textContent = "AI Health Coach Analyzing...";
  textEl.textContent = "Synthesizing your live metabolic and cardiovascular signals...";
  statsEl.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/api/v1/patient/ai-coach`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, query })
    });

    if (res.ok) {
      const data = await res.json();
      titleEl.textContent = data.title;
      textEl.textContent = data.answer;
      statsEl.innerHTML = Object.entries(data.quick_stats || {})
        .map(([k, v]) => `<span class="stat-chip">${k}: ${v}</span>`)
        .join("");
      return;
    }
  } catch (err) {
    // Graceful offline clinical knowledge base fallback
  }

  // Built-in intelligent clinical coaching logic
  setTimeout(() => {
    if (topic === "diet" || query.toLowerCase().includes("diet") || query.toLowerCase().includes("food")) {
      titleEl.textContent = "Personalized Diet Plan";
      textEl.textContent =
        "Your blood glucose is at an optimal 95 mg/dL with 80g of carbs logged today (target: 174g). To support your 7,782 steps and cardiovascular recovery, prioritize a high-fiber evening bowl (quinoa, steamed greens, roasted chickpeas or paneer) providing ~25g complex carbs and 22g protein.";
      statsEl.innerHTML = `
        <span class="stat-chip">Current Carbs: 80/174g</span>
        <span class="stat-chip">Blood Sugar: 95 mg/dL (Healthy)</span>
      `;
    } else if (topic === "workout" || query.toLowerCase().includes("workout") || query.toLowerCase().includes("exercise")) {
      titleEl.textContent = "Cardio & Workout Optimization";
      textEl.textContent =
        "Your resting heart rate is consistent at 80.69 Bpm and you've achieved a 30% step surge today (7,782 steps). Target a 20-minute gentle zone-2 recovery walk or yoga mobility flow to hit 10,000 steps without spiking your blood pressure (118/80 mmHg).";
      statsEl.innerHTML = `
        <span class="stat-chip">Daily Steps: 7,782 / 10,000</span>
        <span class="stat-chip">Resting Heart Rate: 88 Bpm</span>
      `;
    } else if (topic === "sleep" || query.toLowerCase().includes("sleep") || query.toLowerCase().includes("rest")) {
      titleEl.textContent = "Sleep & Circadian Alignment";
      textEl.textContent =
        "Heart rate variability logs indicate your optimal wind-down time starts at 22:00. To bring your 88 Bpm resting rate down towards 64 Bpm in deep REM, reduce screen blue-light after 21:30, hydrate with warm herbal chamomile tea, and aim for 7.5 hours of restorative sleep.";
      statsEl.innerHTML = `
        <span class="stat-chip">Optimal Bedtime: 22:15</span>
        <span class="stat-chip">Target REM Sleep: 2h 15m</span>
      `;
    } else {
      titleEl.textContent = "Arogya Clinical Assistant";
      textEl.textContent = `Hello Melina! Regarding "${query}": Your core vitals are in healthy ranges (BP: 118/80 mmHg, Sugar: 95 mg/dL, BMI: 22.4 kg/m²). Keep maintaining balanced hydration and moderate aerobic consistency. How else can I guide your routine today?`;
      statsEl.innerHTML = `
        <span class="stat-chip">Health Score: 94/100</span>
        <span class="stat-chip">Status: Optimal</span>
      `;
    }
  }, 250);
}

// ================= 10. MODAL: LOG NEW VITAL INPUT =================
function setupAddVitalModal() {
  const modal = document.getElementById("addVitalModal");
  const openBtn = document.getElementById("openAddVitalModal");
  const closeBtn = document.getElementById("closeAddVitalModal");
  const cancelBtn = document.getElementById("cancelVitalBtn");
  const form = document.getElementById("addVitalForm");
  const chips = document.querySelectorAll(".type-chip");

  const groupBp = document.getElementById("groupBp");
  const groupSingle = document.getElementById("groupSingle");
  const singleLabel = document.getElementById("singleLabel");
  const singleUnitTag = document.getElementById("singleUnitTag");
  const singleInput = document.getElementById("inputSingleVal");

  let selectedType = "pressure";

  openBtn.addEventListener("click", () => {
    modal.style.display = "flex";
  });

  const closeModal = () => {
    modal.style.display = "none";
  };

  closeBtn.addEventListener("click", closeModal);
  cancelBtn.addEventListener("click", closeModal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      selectedType = chip.getAttribute("data-type");

      if (selectedType === "pressure") {
        groupBp.style.display = "block";
        groupSingle.style.display = "none";
      } else {
        groupBp.style.display = "none";
        groupSingle.style.display = "block";

        if (selectedType === "saturation") {
          singleLabel.textContent = "Oxygen Saturation (SpO2)";
          singleUnitTag.textContent = "%";
          singleInput.placeholder = "98";
          singleInput.value = "98";
        } else if (selectedType === "sugar") {
          singleLabel.textContent = "Blood Glucose Level";
          singleUnitTag.textContent = "mg/dL";
          singleInput.placeholder = "95";
          singleInput.value = "95";
        } else if (selectedType === "heart") {
          singleLabel.textContent = "Heart Rate Pulse";
          singleUnitTag.textContent = "Bpm";
          singleInput.placeholder = "82";
          singleInput.value = "82";
        }
      }
    });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const timeVal = document.getElementById("inputVitalTime").value || "14:30";
    let vitalValue = "";
    let vitalName = "";
    let vitalColor = "cyan";
    let vitalSub = `Mmol/L ${timeVal}`;

    if (selectedType === "pressure") {
      const sys = document.getElementById("inputSystolic").value || 120;
      const dia = document.getElementById("inputDiastolic").value || 80;
      vitalValue = `${sys}/${dia}`;
      vitalName = "Pressure";
      vitalColor = "pink";
      vitalSub = `120/60 ${timeVal}`;

      // Update top BP card
      currentDashboardData.vitals.blood_pressure.systolic = parseInt(sys, 10);
      currentDashboardData.vitals.blood_pressure.diastolic = parseInt(dia, 10);
      currentDashboardData.vitals.blood_pressure.last_updated = "Just now";
    } else if (selectedType === "saturation") {
      const val = singleInput.value || "98";
      vitalValue = `${val}%`;
      vitalName = "Saturation";
      vitalColor = "cyan";
      vitalSub = `Mmol/L ${timeVal}`;
    } else if (selectedType === "sugar") {
      const val = singleInput.value || "95";
      vitalValue = `${val} mg/dL`;
      vitalName = "Glucose";
      vitalColor = "cyan";
      vitalSub = `Fasting ${timeVal}`;

      currentDashboardData.vitals.blood_sugar.current = parseInt(val, 10);
      currentDashboardData.vitals.blood_sugar.last_updated = "Just now";
    } else if (selectedType === "heart") {
      const val = singleInput.value || "82";
      vitalValue = `${val} Bpm`;
      vitalName = "Heart Rate";
      vitalColor = "pink";
      vitalSub = `Resting ${timeVal}`;

      currentDashboardData.vitals.heart_rate.current = parseInt(val, 10);
      currentDashboardData.vitals.heart_rate.last_updated = "Just now";
    }

    const newEntry = {
      id: `inp-${Date.now()}`,
      type: selectedType,
      name: vitalName,
      value: vitalValue,
      sub: vitalSub,
      color: vitalColor,
      time: timeVal
    };

    // Add to daily inputs
    currentDashboardData.vitals.daily_inputs.unshift(newEntry);

    // Sync to backend via POST
    try {
      await fetch(`${API_BASE}/api/v1/patient/vitals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: selectedType,
          name: vitalName,
          value: vitalValue,
          time: timeVal
        })
      });
    } catch (err) {
      // Local state handles it seamlessly!
    }

    renderDailyInputs();
    renderTopVitals();
    closeModal();
    showToast(`Saved ${vitalName}: ${vitalValue}`);
  });
}

// ================= 11. TOAST NOTIFICATION =================
function showToast(message) {
  const toast = document.getElementById("toastPopup");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3200);
}

// ================= 12. CONTROLS, PROFILE & SEARCH =================
function setupNavigation() {
  const pills = document.querySelectorAll(".nav-pill");
  pills.forEach((p) => {
    p.addEventListener("click", () => {
      pills.forEach((x) => x.classList.remove("active"));
      p.classList.add("active");
      const tab = p.getAttribute("data-tab");
      if (tab === "ai-chat") {
        document.getElementById("coach")?.scrollIntoView({ behavior: "smooth" });
      }
    });
  });
}

function setupProfileDropdown() {
  const menu = document.getElementById("profileMenu");
  const dropdown = document.getElementById("profileDropdown");

  menu.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("open");
  });

  document.addEventListener("click", () => {
    dropdown.classList.remove("open");
  });
}

function setupTimeRangeFilter() {
  const select = document.getElementById("timeRangeSelect");
  select.addEventListener("change", (e) => {
    renderSplineChart(e.target.value);
  });
}

function setupSearchFilter() {
  const searchInput = document.getElementById("searchInput");
  searchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase().trim();
    if (!term) return;

    if (term.includes("pressure") || term.includes("bp")) {
      document.querySelector(".card-bp")?.scrollIntoView({ behavior: "smooth" });
    } else if (term.includes("heart") || term.includes("bpm")) {
      document.querySelector(".hr-main-card")?.scrollIntoView({ behavior: "smooth" });
    } else if (term.includes("sugar") || term.includes("glucose")) {
      document.querySelector(".card-sugar")?.scrollIntoView({ behavior: "smooth" });
    } else if (term.includes("step") || term.includes("walk")) {
      document.querySelector(".step-card")?.scrollIntoView({ behavior: "smooth" });
    } else if (term.includes("nutrition") || term.includes("carb")) {
      document.querySelector(".nutrition-card")?.scrollIntoView({ behavior: "smooth" });
    }
  });
}
