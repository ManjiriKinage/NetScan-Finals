// static/js/main.js
const scanBtn = document.getElementById('scanBtn');
const cancelBtn = document.getElementById('cancelBtn');
const log = document.getElementById('log');
const pdfLink = document.getElementById('pdfLink');
const progressBar = document.getElementById('progressBar');
const resultsContainer = document.getElementById('resultsContainer');
const deviceCount = document.getElementById('deviceCount');
const lastUpdated = document.getElementById('lastUpdated');
const NETBOT_SESSION = "netbot_" + Math.random().toString(36).slice(2);
// Quick stats elements (may not exist yet; we check before updating)
const statDevices = document.getElementById('statDevices');
const statVulns = document.getElementById('statVulns');
const statReports = document.getElementById('statReports');

let pollInterval = null;
let currentJob = null;
let isScanning = false;
let netbotPdfPath = null;

function appendLog(text) {
  const time = new Date().toLocaleTimeString();
  log.textContent += `[${time}] ${text}\n`;
  log.scrollTop = log.scrollHeight;
  lastUpdated.textContent = new Date().toLocaleTimeString();
}

function renderResults(results) {
  resultsContainer.innerHTML = '';
  if (!results || results.length === 0) {
    resultsContainer.innerHTML = '<div class="text-sm text-slate-400 italic">No devices found.</div>';
    if (deviceCount) deviceCount.textContent = '0';
    return;
  }
  if (deviceCount) deviceCount.textContent = results.length;
  results.forEach(dev => {
    const vulnHtml = dev.vulnerabilities.length === 0
      ? '<div class="text-sm text-green-300">No major vulnerabilities</div>'
      : '<ul class="text-sm text-rose-200">' + dev.vulnerabilities.map(v => `<li>• ${v}</li>`).join('') + '</ul>';

    const el = document.createElement('div');
    // use border-black to match your theme
    el.className = 'p-3 bg-slate-900/30 rounded border border-black';
    el.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="font-medium text-slate-100">${dev.host}</div>
        <span class="text-xs px-2 py-0.5 rounded bg-slate-700 text-white">
          ${dev.risk || "Info"}
        </span>
      </div>
      <div class="mt-2">${vulnHtml}</div>
    `;
    resultsContainer.appendChild(el);
  });
}

async function startScan() {

  // If already scanning → Cancel
  if (isScanning && currentJob) {
    cancelScan();
    return;
  }

  const subnet = document.getElementById('subnet').value.trim();

  if (!subnet) {
    appendLog('Please provide subnet');
    return;
  }

  appendLog(`Starting scan for ${subnet}...`);

  isScanning = true;
  scanBtn.innerHTML = "Cancel Scan";
  scanBtn.classList.remove("from-rose-500","via-orange-400","to-amber-300");
  scanBtn.classList.add("bg-rose-600");

  // Status → Scanning
  const mail = document.getElementById("mailStatus");
  if (mail) {
    mail.textContent = "Scanning...";
    mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-amber-500 text-black";
  }

  try {

    const res = await fetch('/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subnet })
    });

    const data = await res.json();

    currentJob = data.job_id;

    appendLog('Job started: ' + currentJob);

    pollInterval = setInterval(() => pollStatus(currentJob), 1000);

  } catch (e) {

    appendLog('Start failed: ' + e);
    resetUI();
  }
}

async function cancelScan() {

  if (!currentJob) return;

  appendLog("Cancelling scan...");

  try {

    await fetch(`/cancel/${currentJob}`, {
      method: "POST"
    });

    appendLog("Scan cancelled. Partial report generated.");

  } catch (e) {
    appendLog("Cancel failed: " + e);
  }

  resetUI();
}

function resetUI() {

  if (pollInterval) clearInterval(pollInterval);

  isScanning = false;
  currentJob = null;

  // Reset button
  scanBtn.innerHTML = "Start Scan";
  scanBtn.classList.remove("bg-rose-600");
  scanBtn.classList.add("from-rose-500","via-orange-400","to-amber-300");

  // Status → Idle
  const mail = document.getElementById("mailStatus");

  if (mail) {
    mail.textContent = "Idle";
    mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-slate-500 text-white";
  }

  // Reset progress
  if (progressBar) progressBar.style.width = "0%";
}

async function sendToNetBot(msg) {

  const res = await fetch("/netbot/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session: NETBOT_SESSION,
      message: msg,
      pdf_path: netbotPdfPath
    })
  });

  const data = await res.json();

  return data.reply;
}

async function pollStatus(jobId) {
  try {
    const res = await fetch(`/status/${jobId}`);
    if (res.status === 404) {
      appendLog('Job not found: ' + jobId);
      clearInterval(pollInterval);
      scanBtn.disabled = false;
      return;
    }

    const data = await res.json();

    // re-render logs
    log.textContent = '';
    (data.logs || []).forEach(l => appendLog(l));

    // update progress bar
    const p = data.progress || 0;
    if (progressBar) progressBar.style.width = `${p}%`;

    
    // update results
    renderResults(data.results || []);
    // AI Summary
    const aiBox = document.getElementById("aiSummary");
    if (aiBox && data.ai_summary) {
      aiBox.textContent = data.ai_summary;
    }

    // --- QUICK STATS UPDATE (safe checks) ---
    const results = data.results || [];
    const devices = results.length;
    let vulnCount = 0;
    let critical = 0, high = 0, medium = 0, low = 0;

    results.forEach(dev => {
      vulnCount += (dev.vulnerabilities || []).length;

      switch (dev.risk) {
        case "Critical": critical++; break;
        case "High": high++; break;
        case "Medium": medium++; break;
        default: low++;
      }
    });

    const riskBox = document.getElementById("riskBox");

    if (riskBox) {
      riskBox.innerHTML = `
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div class="text-rose-400 font-semibold">Critical: ${critical}</div>
          <div class="text-orange-400 font-semibold">High: ${high}</div>
          <div class="text-amber-300 font-semibold">Medium: ${medium}</div>
          <div class="text-slate-400 font-semibold">Low: ${low}</div>
        </div>
      `;
    }

    if (statDevices) statDevices.textContent = devices;
    if (statVulns) statVulns.textContent = vulnCount;
    if (statReports) statReports.textContent = data.pdf ? '1' : '0';
    // Email status badge
    const mail = document.getElementById("mailStatus");

    if (mail && data.logs) {

      if (data.logs.some(l => l.includes("Report emailed successfully"))) {
        mail.textContent = "Email Sent";
        mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-green-500 text-white";
      }

      if (data.logs.some(l => l.includes("Email failed"))) {
        mail.textContent = "Email Failed";
        mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-rose-500 text-white";
      }
    }
    // pdf link
    if (data.pdf) {
  pdfLink.innerHTML = `
    <button
      onclick="window.location.href='${data.pdf}'"
      class="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium
             bg-emerald-500 hover:bg-emerald-600 text-white shadow border border-black">
      <!-- icon -->
      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
        <path d="M3 14a1 1 0 011-1h3v-8a1 1 0 112 0v8h3a1 1 0 011 1v2H3v-2z" />
        <path d="M7 11l3 3 3-3H7z" />
      </svg>
      Download Report
    </button>
  `;
}


if (data.status === 'done' || data.status === 'cancelled') {

  appendLog('Job finished: ' + data.status);

  if (pollInterval) clearInterval(pollInterval);

  isScanning = false;
  currentJob = null;

  // Reset only button + status (NOT pdf)
  scanBtn.innerHTML = "Start Scan";
  scanBtn.classList.remove("bg-rose-600");
  scanBtn.classList.add("from-rose-500","via-orange-400","to-amber-300");

  const mail = document.getElementById("mailStatus");
  if (mail) {
    mail.textContent = "Completed";
    mail.className =
      "ml-2 inline-block px-2 py-0.5 rounded bg-green-500 text-white";
  }
} 
  } catch (e) {
    appendLog('Status poll failed: ' + e);
    clearInterval(pollInterval);
    scanBtn.disabled = false;
  }
}

scanBtn.addEventListener('click', startScan);

// NETBOT UI (Safe Init)
document.addEventListener("DOMContentLoaded", () => {

  const netBtn = document.getElementById("netbot-btn");
  const netPanel = document.getElementById("netbot-panel");
  const netClose = document.getElementById("netbot-close");

  const netSend = document.getElementById("netbot-send");
  const netInput = document.getElementById("netbot-text");
  const netMsg = document.getElementById("netbot-messages");
  const netFile = document.getElementById("netbot-file");

  // If NetBot not present on page → skip safely
  if (!netBtn || !netPanel) return;

  netBtn.onclick = () => {
    netPanel.style.display = "flex";
  };

  netClose.onclick = () => {
    netPanel.style.display = "none";
  };

  function addMsg(text, cls) {

  const div = document.createElement("div");
  div.className = cls;

  // Preserve formatting
  div.style.whiteSpace = "pre-wrap";
  div.style.wordBreak = "break-word";

  let i = 0;

  function type() {
    if (i < text.length) {
      div.textContent += text.charAt(i++);
      setTimeout(type, 6);
    }
  }

  netMsg.appendChild(div);
  type();

  netMsg.scrollTop = netMsg.scrollHeight;
}

  async function sendNetBot() {

  const msg = netInput.value.trim();
  if (!msg) return;

  addMsg(msg, "netbot-user");
  netInput.value = "";

  try {

    // Upload PDF only once
    if (netFile.files.length > 0 && !netbotPdfPath) {

      const file = netFile.files[0];

      const buffer = await file.arrayBuffer();
      const blob = new Blob([buffer], { type: file.type });

      const form = new FormData();
      form.append("file", blob, file.name);

      const upload = await fetch("/netbot/upload", {
        method: "POST",
        body: form
      });

      if (!upload.ok) {
        addMsg("⚠️ PDF upload failed.", "netbot-bot");
        return;
      }

      const up = await upload.json();

      netbotPdfPath = up.path;
      addMsg("📄 Uploaded: " + file.name, "netbot-user");
      netFile.value = "";
    }

    // Send message AFTER upload
    const res = await fetch("/netbot/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: msg,
        context: [],
        pdf_path: netbotPdfPath
      })
    });

    if (!res.ok) {
      addMsg("⚠️ NetBot server error.", "netbot-bot");
      return;
    }

    const data = await res.json();

    addMsg(data.reply, "netbot-bot");

  } catch (err) {

    console.error(err);
    addMsg("⚠️ Network error.", "netbot-bot");
  }
}

  if (netSend) netSend.onclick = sendNetBot;

  if (netInput) {
    netInput.addEventListener("keydown", e => {
      if (e.key === "Enter") sendNetBot();
    });
  }

});
