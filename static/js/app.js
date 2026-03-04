// ── Drag & Drop ──
const dropZone = document.getElementById('dropZone');
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
});

function onFileSelected(input) {
    if (input.files[0]) setFile(input.files[0]);
}

function setFile(file) {
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf','docx','txt'].includes(ext)) {
        showError('Only PDF, DOCX, and TXT files are supported.');
        return;
    }
    const dt = new DataTransfer();
    dt.items.add(file);
    document.getElementById('fileInput').files = dt.files;
    document.getElementById('fileChipName').textContent = '📎 ' + file.name;
    document.getElementById('fileChip').classList.remove('hidden');
    document.getElementById('textInput').value = '';
}

function removeFile(e) {
    e.stopPropagation();
    document.getElementById('fileInput').value = '';
    document.getElementById('fileChip').classList.add('hidden');
}

// ── SCAN ──
async function startScan() {
    const btn = document.getElementById('scanBtn');
    const file = document.getElementById('fileInput');
    const text = document.getElementById('textInput').value.trim();

    if (!file.files[0] && !text) {
        showError('Please upload a file or paste text to scan.');
        return;
    }

    // hide everything
    hide('errorState');
    hide('resultsSection');
    show('loadingState');
    btn.disabled = true;

    const formData = new FormData();
    if (file.files[0]) formData.append('file', file.files[0]);
    else formData.append('text', text);

    try {
        const res = await fetch('/scan', { method: 'POST', body: formData });
        const data = await res.json();
        hide('loadingState');
        btn.disabled = false;

        if (data.error) { showError(data.error); return; }
        renderResults(data);
    } catch (e) {
        hide('loadingState');
        btn.disabled = false;
        showError('Network error: ' + e.message);
    }
}

// ── RENDER RESULTS ──
function renderResults(data) {
    // File name
    document.getElementById('resultFilename').textContent = data.filename || 'Document';

    // Verdict hero
    const hero = document.getElementById('verdictHero');
    hero.className = 'verdict-hero ' + data.verdict.color;
    document.getElementById('verdictEmoji').textContent = data.verdict.icon;
    document.getElementById('verdictLabel').textContent = data.verdict.label;

    // Animated score ring
    animateRing(data.overall_score);

    // Stats
    document.getElementById('statTotal').textContent = data.total_words.toLocaleString();
    document.getElementById('statFlagged').textContent = data.flagged_words.toLocaleString();
    document.getElementById('statClean').textContent = data.clean_words.toLocaleString();
    document.getElementById('statPhrases').textContent = data.repeated_phrases.length;

    // Highlighted doc
    document.getElementById('highlightedDoc').innerHTML = data.highlighted_html || '<em>No content</em>';

    // Flagged words table
    renderWordsTable(data.flagged_word_details || []);

    // Sentence analysis
    renderSentences(data.sentence_analysis || []);

    // Phrases
    renderPhrases(data.repeated_phrases || []);

    show('resultsSection');
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function animateRing(score) {
    const ring = document.getElementById('scoreRing');
    const numEl = document.getElementById('scoreNum');
    const circumference = 314;
    const offset = circumference - (score / 100) * circumference;

    numEl.textContent = '0';
    ring.style.strokeDashoffset = circumference;

    setTimeout(() => {
        ring.style.transition = 'stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1)';
        ring.style.strokeDashoffset = offset;
    }, 150);

    // Count up number
    let current = 0;
    const step = score / 60;
    const timer = setInterval(() => {
        current += step;
        if (current >= score) { current = score; clearInterval(timer); }
        numEl.textContent = current.toFixed(1);
    }, 25);
}

function renderWordsTable(words) {
    const tbody = document.getElementById('flaggedWordsBody');
    if (!words.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="no-result" style="padding:20px;text-align:center">No flagged words detected.</td></tr>`;
        return;
    }
    tbody.innerHTML = words.map((w, i) => `
        <tr>
            <td style="color:var(--muted);font-size:13px">${i + 1}</td>
            <td><span class="word-cell" style="color:${w.level==='high'?'#fca5a5':'#fde68a'}">${esc(w.word)}</span></td>
            <td><span class="badge-${w.level}">${w.level === 'high' ? '🔴 HIGH' : '🟡 MEDIUM'}</span></td>
            <td><span class="count-pill">×${w.count}</span></td>
            <td><span class="status-flag" style="color:${w.level==='high'?'#f87171':'#fbbf24'}">
                ${w.level === 'high' ? '⚠️ Phrase Repeated' : '🔁 Word Repeated'}
            </span></td>
        </tr>
    `).join('');
}

function renderSentences(sentences) {
    const el = document.getElementById('sentenceList');
    if (!sentences.length) {
        el.innerHTML = '<p class="no-result">No suspicious sentences detected.</p>';
        return;
    }
    el.innerHTML = sentences.map(s => `
        <div class="sent-row">
            <div class="sent-pct-badge ${s.level}">
                ${s.flagged_pct}%
                <span>flagged</span>
            </div>
            <div>
                <div class="sent-text">"${esc(s.sentence)}"</div>
                <div class="sent-meta">${s.flagged_words} of ${s.total_words} content words flagged</div>
            </div>
        </div>
    `).join('');
}

function renderPhrases(phrases) {
    const el = document.getElementById('phrasesList');
    if (!phrases.length) {
        el.innerHTML = '<p class="no-result">No repeated phrases found.</p>';
        return;
    }
    el.innerHTML = phrases.map(p => `
        <div class="phrase-pill">
            ${esc(p.phrase)}
            <span class="phrase-count">×${p.count}</span>
        </div>
    `).join('');
}

// ── RESET ──
function resetAll() {
    document.getElementById('fileInput').value = '';
    document.getElementById('textInput').value = '';
    document.getElementById('fileChip').classList.add('hidden');
    hide('resultsSection');
    hide('errorState');
    hide('loadingState');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── HELPERS ──
function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }
function showError(msg) {
    document.getElementById('errorMsg').textContent = msg;
    show('errorState');
    hide('loadingState');
}
function esc(s) {
    return String(s)
        .replace(/&/g,'&amp;')
        .replace(/</g,'&lt;')
        .replace(/>/g,'&gt;');
}
