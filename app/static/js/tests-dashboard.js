document.addEventListener('DOMContentLoaded', () => {
  populateFiles();
});

// Minimal JSON viewer used by the Tests UI
function createJSONViewer(obj) {
  try {
    const container = document.createElement('div');
    container.className = 'json-viewer-container';
    const pre = document.createElement('pre');
    pre.style.whiteSpace = 'pre-wrap';
    pre.style.wordBreak = 'break-word';
    pre.textContent = JSON.stringify(obj, null, 2);
    container.appendChild(pre);
    return container.outerHTML;
  } catch (e) {
    return `<pre>${String(obj)}</pre>`;
  }
}

async function populateFiles() {
  try {
    const res = await fetch('/ui/tests/list');
    const data = await res.json();
    if (!data.success) return;
    const sel = document.getElementById('tests-file-select');
    // preserve first option (ALL)
    while (sel.options.length > 1) sel.remove(1);
    data.files.forEach(f => {
      const opt = document.createElement('option');
      opt.value = f.path;
      opt.textContent = f.name;
      sel.appendChild(opt);
    });
  } catch {}
}

async function runAllTests(btn) {
  const summary = document.getElementById('tests-summary');
  const area = document.getElementById('tests-results');
  const sel = document.getElementById('tests-file-select');
  btn.disabled = true;
  const old = btn.textContent;
  btn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Running...';
  summary.innerHTML = '<span class="text-muted">Executing tests, please wait...</span>';
  area.innerHTML = '';
  try {
    const body = sel && sel.value && sel.value !== 'ALL' ? { file: sel.value } : {};
    const res = await fetch('/ui/tests/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Failed to run tests');
    // Show returned HTML tables
    summary.innerHTML = '';
    area.innerHTML = data.html || '<div class="text-muted">No results</div>';
  } catch (e) {
    summary.innerHTML = `<span class="text-danger">${e.message}</span>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = old;
  }
}