// static/js/main.js
const scanBtn = document.getElementById('scanBtn');
const cancelBtn = document.getElementById('cancelBtn');
const log = document.getElementById('log');
const pdfLink = document.getElementById('pdfLink');
const progressBar = document.getElementById('progressBar');
const resultsContainer = document.getElementById('resultsContainer');
const deviceCount = document.getElementById('deviceCount');
const lastUpdated = document.getElementById('lastUpdated');

// Quick stats elements (may not exist yet; we check before updating)
const statDevices = document.getElementById('statDevices');
const statVulns = document.getElementById('statVulns');
const statReports = document.getElementById('statReports');

let pollInterval = null;
let currentJob = null;

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
    el.innerHTML = `<div class="flex items-center justify-between"><div class="font-medium text-slate-100">${dev.host}</div></div>
                    <div class="mt-2">${vulnHtml}</div>`;
    resultsContainer.appendChild(el);
  });
}

async function startScan() {
  const subnet = document.getElementById('subnet').value.trim();
  if (!subnet) {
    appendLog('Please provide subnet');
    return;
  }
  appendLog(`Starting scan for ${subnet}...`);
  scanBtn.disabled = true;

  try {
    const res = await fetch('/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subnet })
    });

    if (!res.ok) {
      const j = await res.json();
      appendLog('Server error starting job: ' + (j.error || 'unknown'));
      scanBtn.disabled = false;
      return;
    }

    const data = await res.json();
    currentJob = data.job_id;
    appendLog('Job started: ' + currentJob);

    pollInterval = setInterval(() => pollStatus(currentJob), 1000);
  } catch (e) {
    appendLog('Start request failed: ' + e);
    scanBtn.disabled = false;
  }
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

    // --- QUICK STATS UPDATE (safe checks) ---
    const results = data.results || [];
    const devices = results.length;
    let vulnCount = 0;
    results.forEach(dev => { vulnCount += (dev.vulnerabilities || []).length; });

    if (statDevices) statDevices.textContent = devices;
    if (statVulns) statVulns.textContent = vulnCount;
    if (statReports) statReports.textContent = data.pdf ? '1' : '0';

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


    if (data.status === 'done' || data.status === 'error') {
      appendLog('Job finished with status: ' + data.status + (data.error ? (' - ' + data.error) : ''));
      clearInterval(pollInterval);
      scanBtn.disabled = false;
      currentJob = null;
    }
  } catch (e) {
    appendLog('Status poll failed: ' + e);
    clearInterval(pollInterval);
    scanBtn.disabled = false;
  }
}

scanBtn.addEventListener('click', startScan);
cancelBtn && cancelBtn.addEventListener('click', () => {
  if (pollInterval) clearInterval(pollInterval);
  appendLog('Scan cancelled (client-side).');
  scanBtn.disabled = false;
});
