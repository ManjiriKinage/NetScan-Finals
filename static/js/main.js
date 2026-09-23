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
let lastScanResults = null;  // Store results for export
let riskChart = null;  // Chart.js instance

function appendLog(text) {
  const time = new Date().toLocaleTimeString();
  log.textContent += `[${time}] ${text}\n`;
  log.scrollTop = log.scrollHeight;
  lastUpdated.textContent = new Date().toLocaleTimeString();
}

// ──────────────────────────────────────────────
// RISK CHART (item 2.2) — Chart.js Doughnut
// ──────────────────────────────────────────────

function initRiskChart() {
  const ctx = document.getElementById('riskChart');
  if (!ctx) return;

  riskChart = new Chart(ctx.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Critical', 'High', 'Medium', 'Low'],
      datasets: [{
        data: [0, 0, 0, 0],
        backgroundColor: [
          'rgba(251, 113, 133, 0.9)',   // rose-400
          'rgba(251, 146, 60, 0.9)',    // orange-400
          'rgba(252, 211, 77, 0.9)',    // amber-300
          'rgba(100, 116, 139, 0.7)'   // slate-500
        ],
        borderColor: [
          '#fb7185', '#fb923c', '#fcd34d', '#64748b'
        ],
        borderWidth: 2,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '60%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            font: { size: 11 },
            padding: 12
          }
        }
      },
      animation: {
        animateRotate: true,
        duration: 800
      }
    }
  });
}

function updateRiskChart(critical, high, medium, low) {
  if (!riskChart) return;
  riskChart.data.datasets[0].data = [critical, high, medium, low];
  riskChart.update('active');
}

// Initialize chart on load
document.addEventListener('DOMContentLoaded', initRiskChart);


// ──────────────────────────────────────────────
// DEVICE DETAIL MODAL (item 2.3)
// ──────────────────────────────────────────────

function openDeviceModal(dev) {
  const modal = document.getElementById('deviceModal');
  const title = document.getElementById('modalTitle');
  const content = document.getElementById('modalContent');
  if (!modal) return;

  title.textContent = `🖥️ ${dev.host} — ${dev.risk || 'Info'} Risk`;

  // OS info
  let osHtml = '';
  if (dev.os && dev.os.name) {
    osHtml = `
      <div class="modal-section">
        <h4>💻 Operating System</h4>
        <div class="modal-service-row">
          <span>${dev.os.name}</span>
          <span class="text-slate-400">Accuracy: ${dev.os.accuracy}%</span>
        </div>
      </div>`;
  }

  // Services
  let servicesHtml = '<div class="modal-section"><h4>🔌 Services</h4>';
  if (dev.services && dev.services.length > 0) {
    dev.services.forEach(svc => {
      servicesHtml += `
        <div class="modal-service-row">
          <span><strong>Port ${svc.port}</strong></span>
          <span>${svc.service || 'Unknown'} ${svc.version || ''}</span>
        </div>`;
    });
  } else {
    servicesHtml += '<p class="text-slate-400 text-sm">No services detected</p>';
  }
  servicesHtml += '</div>';

  // Vulnerabilities
  let vulnsHtml = '<div class="modal-section"><h4>⚠️ Vulnerabilities</h4>';
  if (dev.vulnerabilities && dev.vulnerabilities.length > 0) {
    dev.vulnerabilities.forEach(v => {
      vulnsHtml += `<div class="modal-vuln-item">${v}</div>`;
    });
  } else {
    vulnsHtml += '<p class="text-green-400 text-sm">✅ No vulnerabilities detected</p>';
  }
  vulnsHtml += '</div>';

  // Risk score
  let scoreHtml = `
    <div class="modal-section">
      <h4>📊 Risk Summary</h4>
      <div class="modal-service-row">
        <span>Severity Score</span>
        <span class="font-bold ${dev.severity_score >= 9 ? 'text-rose-400' : dev.severity_score >= 7 ? 'text-orange-400' : dev.severity_score >= 4 ? 'text-amber-300' : 'text-green-400'}">${dev.severity_score || 0}</span>
      </div>
      <div class="modal-service-row">
        <span>Risk Level</span>
        <span class="font-bold">${dev.risk || 'Low'}</span>
      </div>
    </div>`;

  content.innerHTML = osHtml + servicesHtml + vulnsHtml + scoreHtml;
  modal.style.display = 'flex';
}

// Close modal handlers
document.addEventListener('DOMContentLoaded', () => {
  const modalClose = document.getElementById('modalClose');
  const deviceModal = document.getElementById('deviceModal');
  if (modalClose) modalClose.onclick = () => deviceModal.style.display = 'none';
  if (deviceModal) deviceModal.onclick = (e) => { if (e.target === deviceModal) deviceModal.style.display = 'none'; };
});


// ──────────────────────────────────────────────
// RENDER RESULTS (updated for clickable rows — item 2.3)
// ──────────────────────────────────────────────

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
      : '<ul class="text-sm text-rose-200">' + dev.vulnerabilities.slice(0, 3).map(v => `<li>• ${v}</li>`).join('') + (dev.vulnerabilities.length > 3 ? `<li class="text-slate-400">+ ${dev.vulnerabilities.length - 3} more...</li>` : '') + '</ul>';

    // OS badge
    const osBadge = dev.os && dev.os.name
      ? `<span class="text-xs px-2 py-0.5 rounded bg-indigo-800 text-indigo-200 ml-2">${dev.os.name}</span>`
      : '';

    const el = document.createElement('div');
    // use border-black to match your theme
    el.className = 'p-3 bg-slate-900/30 rounded border border-black device-row';
    el.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="font-medium text-slate-100">${dev.host}${osBadge}</div>
        <span class="text-xs px-2 py-0.5 rounded bg-slate-700 text-white">
          ${dev.risk || "Info"}
        </span>
      </div>
      <div class="mt-2">${vulnHtml}</div>
      <div class="text-xs text-slate-500 mt-1">Click for details →</div>
    `;
    el.addEventListener('click', () => openDeviceModal(dev));
    resultsContainer.appendChild(el);
  });
}


// ──────────────────────────────────────────────
// EXPORT CSV/JSON (item 2.4)
// ──────────────────────────────────────────────

function exportCSV() {
  if (!lastScanResults || lastScanResults.length === 0) {
    alert('No scan results to export');
    return;
  }

  let csv = 'Host,Risk,Severity Score,OS,Services Count,Vulnerabilities Count,Vulnerabilities\n';
  lastScanResults.forEach(dev => {
    const os = (dev.os && dev.os.name) || 'Unknown';
    const vulns = (dev.vulnerabilities || []).join(' | ').replace(/"/g, '""');
    csv += `"${dev.host}","${dev.risk || 'Low'}",${dev.severity_score || 0},"${os}",${(dev.services || []).length},${(dev.vulnerabilities || []).length},"${vulns}"\n`;
  });

  downloadFile(csv, 'netscan_results.csv', 'text/csv');
}

function exportJSON() {
  if (!lastScanResults || lastScanResults.length === 0) {
    alert('No scan results to export');
    return;
  }

  const json = JSON.stringify(lastScanResults, null, 2);
  downloadFile(json, 'netscan_results.json', 'application/json');
}

function downloadFile(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Make export functions globally available
window.exportCSV = exportCSV;
window.exportJSON = exportJSON;


// ──────────────────────────────────────────────
// SCAN DIFF (item 3.3)
// ──────────────────────────────────────────────

async function showScanDiff() {
  if (!currentJob && !lastCompletedJob) {
    alert('No completed scan to compare');
    return;
  }

  const jobId = lastCompletedJob || currentJob;
  const diffModal = document.getElementById('diffModal');
  const diffContent = document.getElementById('diffContent');
  if (!diffModal) return;

  diffContent.innerHTML = '<p class="text-slate-400 text-sm">Loading diff...</p>';
  diffModal.style.display = 'flex';

  try {
    const res = await fetch(`/scan-diff/${jobId}`);
    const data = await res.json();

    if (data.error && !data.diff) {
      diffContent.innerHTML = `<p class="text-slate-400 text-sm">${data.error}</p>`;
      return;
    }

    const diff = data.diff;
    let html = '';

    html += `<div class="modal-section"><h4>🆕 New Vulnerabilities (${diff.new.length})</h4>`;
    if (diff.new.length > 0) {
      diff.new.forEach(v => { html += `<div class="diff-new">+ ${v}</div>`; });
    } else {
      html += '<p class="text-green-400 text-sm">No new vulnerabilities</p>';
    }
    html += '</div>';

    html += `<div class="modal-section"><h4>✅ Resolved Vulnerabilities (${diff.resolved.length})</h4>`;
    if (diff.resolved.length > 0) {
      diff.resolved.forEach(v => { html += `<div class="diff-resolved">- ${v}</div>`; });
    } else {
      html += '<p class="text-slate-400 text-sm">No resolved vulnerabilities</p>';
    }
    html += '</div>';

    html += `<div class="modal-section"><h4>📊 Summary</h4>
      <div class="modal-service-row"><span>Unchanged</span><span>${diff.unchanged_count}</span></div>
    </div>`;

    diffContent.innerHTML = html;
  } catch (e) {
    diffContent.innerHTML = `<p class="text-rose-400 text-sm">Error loading diff: ${e}</p>`;
  }
}

window.showScanDiff = showScanDiff;

let lastCompletedJob = null;

// Close diff modal
document.addEventListener('DOMContentLoaded', () => {
  const diffClose = document.getElementById('diffClose');
  const diffModal = document.getElementById('diffModal');
  if (diffClose) diffClose.onclick = () => diffModal.style.display = 'none';
  if (diffModal) diffModal.onclick = (e) => { if (e.target === diffModal) diffModal.style.display = 'none'; };
});


// ──────────────────────────────────────────────
// SCAN HISTORY (item 2.1)
// ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const historyBtn = document.getElementById('historyBtn');
  const historyModal = document.getElementById('historyModal');
  const historyClose = document.getElementById('historyClose');
  const historyContent = document.getElementById('historyContent');

  if (historyBtn) {
    historyBtn.onclick = async () => {
      historyModal.style.display = 'flex';
      historyContent.innerHTML = '<p class="text-slate-400 text-sm">Loading...</p>';

      try {
        const res = await fetch('/scan-history');
        const data = await res.json();

        if (!data || data.length === 0) {
          historyContent.innerHTML = '<p class="text-slate-400 text-sm">No scan history yet. Complete a scan first.</p>';
          return;
        }

        let html = '';
        data.forEach(scan => {
          const date = scan.started_at ? new Date(scan.started_at * 1000).toLocaleString() : 'Unknown';
          const statusColor = scan.status === 'done' ? 'text-green-400' : scan.status === 'error' ? 'text-rose-400' : 'text-slate-400';
          html += `
            <div class="history-row">
              <div>
                <div class="text-sm font-medium text-slate-200">${scan.subnet}</div>
                <div class="text-xs text-slate-400">${date} · ${scan.profile || 'standard'}</div>
              </div>
              <div class="text-right">
                <div class="${statusColor} text-sm font-medium">${scan.status}</div>
                <div class="text-xs text-slate-400">${scan.total_devices} devices · ${scan.critical_devices} critical</div>
              </div>
              ${scan.pdf ? `<a href="${scan.pdf}" class="ml-2 text-xs text-emerald-400 hover:underline">📥 PDF</a>` : ''}
            </div>`;
        });
        historyContent.innerHTML = html;
      } catch (e) {
        historyContent.innerHTML = `<p class="text-rose-400 text-sm">Error: ${e}</p>`;
      }
    };
  }

  if (historyClose) historyClose.onclick = () => historyModal.style.display = 'none';
  if (historyModal) historyModal.onclick = (e) => { if (e.target === historyModal) historyModal.style.display = 'none'; };
});


// ──────────────────────────────────────────────
// SCHEDULED SCANS (item 3.1)
// ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const scheduleBtn = document.getElementById('scheduleBtn');

  if (scheduleBtn) {
    scheduleBtn.onclick = async () => {
      const subnet = document.getElementById('subnet').value.trim();
      const delay = parseInt(document.getElementById('scheduleDelay').value) || 5;
      const profile = document.querySelector('input[name="scanProfile"]:checked')?.value || 'standard';

      if (!subnet) {
        appendLog('Please provide subnet for scheduled scan');
        return;
      }

      try {
        const res = await fetch('/schedule-scan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ subnet, delay_minutes: delay, profile })
        });

        const data = await res.json();
        if (res.ok) {
          appendLog(`⏰ Scan scheduled: ${subnet} in ${delay} minutes (ID: ${data.schedule_id})`);
          refreshScheduledList();
        } else {
          appendLog(`⚠️ Schedule failed: ${data.error}`);
        }
      } catch (e) {
        appendLog('Schedule failed: ' + e);
      }
    };
  }

  refreshScheduledList();
});

async function refreshScheduledList() {
  const list = document.getElementById('scheduledList');
  if (!list) return;

  try {
    const res = await fetch('/scheduled-scans');
    const data = await res.json();

    if (!data || data.length === 0) {
      list.innerHTML = '<span class="text-slate-500">No scheduled scans</span>';
      return;
    }

    list.innerHTML = data.map(s => {
      const time = new Date(s.run_at * 1000).toLocaleTimeString();
      const color = s.status === 'pending' ? 'text-amber-300' : s.status === 'running' ? 'text-green-400' : 'text-slate-500';
      return `<div class="flex justify-between items-center"><span>${s.subnet}</span><span class="${color}">${s.status} · ${time}</span></div>`;
    }).join('');
  } catch (e) {
    // Silently ignore on first load
  }
}


// ──────────────────────────────────────────────
// THEME TOGGLE (item 2.5)
// ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('themeToggle');
  const moonIcon = document.getElementById('themeIconMoon');
  const sunIcon = document.getElementById('themeIconSun');

  // Restore saved theme
  if (localStorage.getItem('netscan-theme') === 'light') {
    document.body.classList.add('light-mode');
    if (moonIcon) moonIcon.classList.add('hidden');
    if (sunIcon) sunIcon.classList.remove('hidden');
  }

  if (toggle) {
    toggle.onclick = () => {
      document.body.classList.toggle('light-mode');
      const isLight = document.body.classList.contains('light-mode');
      localStorage.setItem('netscan-theme', isLight ? 'light' : 'dark');

      if (moonIcon && sunIcon) {
        moonIcon.classList.toggle('hidden', isLight);
        sunIcon.classList.toggle('hidden', !isLight);
      }
    };
  }
});


// ──────────────────────────────────────────────
// START / CANCEL SCAN (updated for profiles — item 3.2)
// ──────────────────────────────────────────────

async function startScan() {

  // If already scanning → Cancel
  if (isScanning && currentJob) {
    cancelScan();
    return;
  }

  const subnet = document.getElementById('subnet').value.trim();
  const profile = document.querySelector('input[name="scanProfile"]:checked')?.value || 'standard';
  const osDetect = document.getElementById('osDetect')?.checked || false;

  if (!subnet) {
    appendLog('Please provide subnet');
    return;
  }

  appendLog(`Starting ${profile} scan for ${subnet}...`);

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
      body: JSON.stringify({ subnet, profile, os_detect: osDetect })
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

  appendLog("Cancelling scan... waiting for the partial AI summary...");

  try {

    await fetch(`/cancel/${currentJob}`, {
      method: "POST"
    });

    // Keep polling until the current host exits and the partial report is ready.
    scanBtn.innerHTML = "Cancelling...";
    scanBtn.disabled = true;

    const mail = document.getElementById("mailStatus");
    if (mail) {
      mail.textContent = "Cancelling...";
      mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-orange-500 text-white";
    }

    // Keep polling alive so the frontend receives the partial AI summary and PDF.

  } catch (e) {
    appendLog("Cancel failed: " + e);
    resetUI();
  }
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
      // Render AI summary as markdown if marked is available
      if (typeof marked !== 'undefined') {
        aiBox.innerHTML = marked.parse(data.ai_summary);
      } else {
        aiBox.textContent = data.ai_summary;
      }
    }

    // --- QUICK STATS UPDATE (safe checks) ---
    const results = data.results || [];
    lastScanResults = results;  // Store for export
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

    // Update Chart.js doughnut (item 2.2)
    updateRiskChart(critical, high, medium, low);

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

  // Show export buttons (item 2.4)
  const csvBtn = document.getElementById('exportCsvBtn');
  const jsonBtn = document.getElementById('exportJsonBtn');
  if (csvBtn) csvBtn.classList.remove('hidden');
  if (jsonBtn) jsonBtn.classList.remove('hidden');
}


if (data.status === 'done' || data.status === 'cancelled') {

  appendLog('Job finished: ' + data.status);

  if (pollInterval) clearInterval(pollInterval);

  lastCompletedJob = jobId;
  isScanning = false;
  currentJob = null;

  // Show diff button (item 3.3)
  const diffBtn = document.getElementById('diffBtn');
  if (diffBtn) diffBtn.classList.remove('hidden');

  // Auto-attach PDF to NetBot (item 6.4)
  if (data.pdf && !netbotPdfPath) {
    netbotPdfPath = data.pdf;
    const netMsg = document.getElementById("netbot-messages");
    if (netMsg) {
      const div = document.createElement("div");
      div.className = "netbot-bot";
      div.innerHTML = "📄 <strong>Latest scan report auto-attached.</strong> You can now ask me to analyze it!";
      netMsg.appendChild(div);
    }
  }

  // Reset button (re-enable in case cancel disabled it)
  scanBtn.innerHTML = "Start Scan";
  scanBtn.disabled = false;
  scanBtn.classList.remove("bg-rose-600");
  scanBtn.classList.add("from-rose-500","via-orange-400","to-amber-300");

  const mail = document.getElementById("mailStatus");
  if (mail) {
    if (data.status === 'cancelled') {
      mail.textContent = "Cancelled (Partial)";
      mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-orange-500 text-white";
    } else {
      mail.textContent = "Completed";
      mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-green-500 text-white";
    }
  }

  // Refresh scheduled scans list
  refreshScheduledList();
} 
  } catch (e) {
    appendLog('Status poll failed: ' + e);
    clearInterval(pollInterval);
    scanBtn.disabled = false;
  }
}

scanBtn.addEventListener('click', startScan);

// ──────────────────────────────────────────────
// NETBOT UI (Safe Init) — with typing indicator, markdown, chips, export
// ──────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {

  const netBtn = document.getElementById("netbot-btn");
  const netPanel = document.getElementById("netbot-panel");
  const netClose = document.getElementById("netbot-close");

  const netSend = document.getElementById("netbot-send");
  const netInput = document.getElementById("netbot-text");
  const netMsg = document.getElementById("netbot-messages");
  const netFile = document.getElementById("netbot-file");
  const netExport = document.getElementById("netbot-export");

  // If NetBot not present on page → skip safely
  if (!netBtn || !netPanel) return;

  netBtn.onclick = () => {
    netPanel.style.display = "flex";
  };

  netClose.onclick = () => {
    netPanel.style.display = "none";
  };

  // ── Typing Indicator (item 6.1) ──
  function showTyping() {
    const indicator = document.createElement("div");
    indicator.className = "typing-indicator";
    indicator.id = "netbot-typing";
    indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    netMsg.appendChild(indicator);
    netMsg.scrollTop = netMsg.scrollHeight;
  }

  function hideTyping() {
    const indicator = document.getElementById("netbot-typing");
    if (indicator) indicator.remove();
  }

  // ── Add Message (updated for markdown — item 6.2) ──
  function addMsg(text, cls) {
    const div = document.createElement("div");
    div.className = cls;

    if (cls === "netbot-bot" && typeof marked !== 'undefined') {
      // Render markdown for bot messages
      div.innerHTML = marked.parse(text);
    } else {
      // User messages: preserve formatting, use typing effect
      div.style.whiteSpace = "pre-wrap";
      div.style.wordBreak = "break-word";

      let i = 0;
      function type() {
        if (i < text.length) {
          div.textContent += text.charAt(i++);
          setTimeout(type, 6);
        }
      }
      type();
    }

    netMsg.appendChild(div);
    netMsg.scrollTop = netMsg.scrollHeight;
  }

  // ── Suggested Prompt Chips (item 6.3) ──
  const chips = document.querySelectorAll('.netbot-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const msg = chip.getAttribute('data-msg');
      if (msg) {
        netInput.value = msg;
        sendNetBot();
      }
    });
  });

  // ── Chat Export (item 6.5) ──
  if (netExport) {
    netExport.onclick = () => {
      const messages = netMsg.querySelectorAll('.netbot-user, .netbot-bot');
      let chatText = "NetBot Chat Export\n" + "=".repeat(40) + "\n\n";

      messages.forEach(msg => {
        const role = msg.classList.contains('netbot-user') ? 'You' : 'NetBot';
        chatText += `[${role}]: ${msg.textContent.trim()}\n\n`;
      });

      downloadFile(chatText, 'netbot_chat.txt', 'text/plain');
    };
  }

  // ── Send Message ──
  async function sendNetBot() {

  const msg = netInput.value.trim();
  if (!msg) return;

  addMsg(msg, "netbot-user");
  netInput.value = "";

  // Show typing indicator (item 6.1)
  showTyping();

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
        hideTyping();
        addMsg("⚠️ PDF upload failed.", "netbot-bot");
        return;
      }

      const up = await upload.json();

      netbotPdfPath = up.path;
      addMsg("📄 Uploaded: " + file.name, "netbot-user");
      netFile.value = "";
    }

    // Send message AFTER upload
    // Include subnet from the input field so netbot can use it for scans
    const subnetInput = document.getElementById('subnet');
    const subnetValue = subnetInput ? subnetInput.value.trim() : '';
    const res = await fetch("/netbot/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: msg,
        session: NETBOT_SESSION,
        pdf_path: netbotPdfPath,
        subnet: subnetValue,
        job_id: currentJob
      })
    });

    hideTyping();

    if (!res.ok) {
      addMsg("⚠️ NetBot server error.", "netbot-bot");
      return;
    }

    const data = await res.json();

    addMsg(data.reply, "netbot-bot");

    // If the reply contains a Job ID, start polling in the main scan UI
    if (data.reply && data.reply.includes("Job ID:")) {
      const match = data.reply.match(/Job ID:\s*(\S+)/);
      if (match) {
        const jobId = match[1];
        currentJob = jobId;
        isScanning = true;

        // Update scan button
        scanBtn.innerHTML = "Cancel Scan";
        scanBtn.classList.remove("from-rose-500","via-orange-400","to-amber-300");
        scanBtn.classList.add("bg-rose-600");

        // Update mail status
        const mail = document.getElementById("mailStatus");
        if (mail) {
          mail.textContent = "Scanning...";
          mail.className = "ml-2 inline-block px-2 py-0.5 rounded bg-amber-500 text-black";
        }

        appendLog("Scan started via NetBot. Job: " + jobId);

        // Start polling
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(() => pollStatus(jobId), 1000);
      }
    }

    // If the reply indicates scan was cancelled, update the UI
    // Don't call resetUI() — the polling loop will handle the final state
    // once the backend finishes generating the partial report
    if (data.reply && (data.reply.includes("cancelled") || data.reply.includes("Scan cancelled"))) {
      appendLog("Scan cancelled via NetBot.");
      scanBtn.innerHTML = "Cancelling...";
      scanBtn.disabled = true;
    }

  } catch (err) {

    hideTyping();
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
