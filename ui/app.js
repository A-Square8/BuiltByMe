const API = '';
let currentProject = null;
let pollInterval = null;

// SVG icon helpers
const icons = {
    file: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    trash: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    code: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    star: '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    fork: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/><path d="M6 9a9 9 0 0 0 9 9"/></svg>',
    fileText: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    gitCommit: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><line x1="1.05" y1="12" x2="7" y2="12"/><line x1="17.01" y1="12" x2="22.96" y2="12"/></svg>',
    hash: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>',
    pkg: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    fn: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
    box: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    wrench: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    chevDown: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
    folder: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    chevLeft: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
};

const $ = id => document.getElementById(id);

const menuBtn = $('menuBtn'), menuDropdown = $('menuDropdown'), addProjectBtn = $('addProjectBtn');
const modalOverlay = $('modalOverlay'), modalClose = $('modalClose'), startExtractionBtn = $('startExtraction');
const projectsList = $('projectsList'), emptyState = $('emptyState'), projectView = $('projectView');
const progressArea = $('progressArea'), errorArea = $('errorArea');
const configBtn = $('configBtn'), configOverlay = $('configOverlay'), configClose = $('configClose');

// Menu
menuBtn.addEventListener('click', e => { e.stopPropagation(); menuDropdown.classList.toggle('show'); if (menuDropdown.classList.contains('show')) loadProjectsList(); });
document.addEventListener('click', () => menuDropdown.classList.remove('show'));
menuDropdown.addEventListener('click', e => e.stopPropagation());
addProjectBtn.addEventListener('click', () => { menuDropdown.classList.remove('show'); openModal(); });
modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
startExtractionBtn.addEventListener('click', startExtraction);

// Config
configBtn.addEventListener('click', () => { menuDropdown.classList.remove('show'); openConfig(); });
configClose.addEventListener('click', closeConfig);
configOverlay.addEventListener('click', e => { if (e.target === configOverlay) closeConfig(); });

// User Guide
const guideBtn = $('guideBtn'), userGuideOverlay = $('userGuideOverlay'), closeGuideBtn = $('closeGuideBtn');
if (guideBtn && userGuideOverlay) {
    guideBtn.addEventListener('click', () => { menuDropdown.classList.remove('show'); userGuideOverlay.style.display = 'flex'; document.body.style.overflow = 'hidden'; });
    closeGuideBtn.addEventListener('click', () => { userGuideOverlay.style.display = 'none'; document.body.style.overflow = ''; });
    userGuideOverlay.addEventListener('click', e => { if (e.target === userGuideOverlay) { userGuideOverlay.style.display = 'none'; document.body.style.overflow = ''; } });
}

$('savePatBtn').addEventListener('click', savePat);
$('clearPatBtn').addEventListener('click', clearPat);
$('togglePatVisibility').addEventListener('click', () => {
    const inp = $('configPat');
    inp.type = inp.type === 'password' ? 'text' : 'password';
});

function openModal() {
    modalOverlay.style.display = 'flex';
    $('repoUrl').value = '';
    $('accessToken').value = '';
    progressArea.style.display = 'none';
    errorArea.style.display = 'none';
    startExtractionBtn.disabled = false;
}
function closeModal() { modalOverlay.style.display = 'none'; if (pollInterval) { clearInterval(pollInterval); pollInterval = null; } }

async function openConfig() {
    configOverlay.style.display = 'flex';
    $('configStatus').style.display = 'none';
    try {
        const r = await fetch(`${API}/api/config/pat`);
        const d = await r.json();
        $('configPat').value = d.pat || '';
    } catch { $('configPat').value = ''; }
}
function closeConfig() { configOverlay.style.display = 'none'; }

async function savePat() {
    const pat = $('configPat').value.trim();
    const st = $('configStatus');
    try {
        const r = await fetch(`${API}/api/config/pat`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({pat}) });
        const d = await r.json();
        st.style.display = 'flex'; st.className = 'config-status success'; st.textContent = d.message || 'Saved successfully';
        setTimeout(() => st.style.display = 'none', 3000);
    } catch(e) { st.style.display = 'flex'; st.className = 'config-status error'; st.textContent = 'Failed to save'; }
}
async function clearPat() {
    $('configPat').value = '';
    await savePat();
}

async function startExtraction() {
    const repoUrl = $('repoUrl').value.trim();
    const token = $('accessToken').value.trim();
    const ignorePatterns = $('ignorePatterns') ? $('ignorePatterns').value.trim() : '';
    if (!repoUrl) { showError('Please enter a GitHub repository URL'); return; }
    if (!repoUrl.includes('github.com/')) { showError('Please enter a valid GitHub URL'); return; }
    startExtractionBtn.disabled = true;
    errorArea.style.display = 'none';
    progressArea.style.display = 'block';
    updateProgress('Starting extraction...', 0, '');
    try {
        const resp = await fetch(`${API}/api/extract`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ repo_url: repoUrl, token: token || null, ignore_patterns: ignorePatterns }) });
        const data = await resp.json();
        if (!resp.ok) { showError(data.error || 'Failed to start extraction'); startExtractionBtn.disabled = false; return; }
        pollExtractionStatus(data.project_name);
    } catch(err) { showError('Network error: ' + err.message); startExtractionBtn.disabled = false; }
}

function pollExtractionStatus(projectName) {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(async () => {
        try {
            const resp = await fetch(`${API}/api/extract/status/${projectName}`);
            const data = await resp.json();
            if (['extracting','fetching_info','fetching_commits','fetching_tree'].includes(data.status)) {
                const pct = data.total > 0 ? Math.round((data.processed / data.total) * 100) : 0;
                const txt = data.status === 'extracting' ? `Processing files... ${data.processed}/${data.total} (${pct}%)` : data.status.replace(/_/g, ' ') + '...';
                updateProgress(txt, pct, data.current_file || '');
            } else if (data.status === 'completed') {
                clearInterval(pollInterval); pollInterval = null;
                updateProgress('Extraction complete!', 100, '');
                setTimeout(() => { closeModal(); loadProject(projectName); }, 1000);
            } else if (data.status === 'failed') {
                clearInterval(pollInterval); pollInterval = null;
                showError('Extraction failed: ' + (data.errors?.[0] || 'Unknown error'));
                startExtractionBtn.disabled = false;
            }
        } catch(err) { console.error('Poll error:', err); }
    }, 1000);
}

function updateProgress(text, pct, file) {
    $('progressBar').style.width = pct + '%';
    $('progressText').textContent = text;
    $('progressFile').textContent = file;
}
function showError(msg) { errorArea.style.display = 'block'; $('errorText').textContent = msg; }

async function loadProjectsList() {
    try {
        const resp = await fetch(`${API}/api/projects`);
        const projects = await resp.json();
        if (projects.length === 0) { projectsList.innerHTML = '<div class="menu-item disabled">No projects yet</div>'; return; }
        projectsList.innerHTML = projects.map(p => `
            <div class="menu-item ${currentProject === p.name ? 'active' : ''}" onclick="selectProject('${p.name}')" style="display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:8px;">
                    ${icons.folder}
                    <span>${p.name}</span>
                    <span style="font-size:10px;color:var(--gray-400);font-weight:500;">${p.extraction_status || ''}</span>
                </div>
                <button onclick="deleteProject(event,'${p.name}')" class="project-delete-btn" title="Delete">${icons.trash}</button>
            </div>
        `).join('');
    } catch { projectsList.innerHTML = '<div class="menu-item disabled">Error loading</div>'; }
}

function selectProject(name) { menuDropdown.classList.remove('show'); loadProject(name); }

async function deleteProject(event, name) {
    event.stopPropagation();
    if (!confirm(`Delete project '${name}'?`)) return;
    try {
        const resp = await fetch(`${API}/api/project/${name}/delete`, { method: 'DELETE' });
        if (resp.ok) { if (currentProject === name) { currentProject = null; emptyState.style.display = 'flex'; projectView.style.display = 'none'; } loadProjectsList(); }
        else alert('Failed to delete');
    } catch(e) { alert('Error deleting'); }
}

async function loadProject(name) {
    currentProject = name;
    try {
        const resp = await fetch(`${API}/api/project/${name}`);
        if (!resp.ok) throw new Error('Not found');
        const data = await resp.json();
        emptyState.style.display = 'none'; projectView.style.display = 'flex';
        $('projectTitle').textContent = data.info?.full_name || name;
        $('projectDesc').textContent = data.info?.description || '';
        const meta = [];
        if (data.info?.language) meta.push(`<span class="sidebar-meta-tag">${icons.code} ${data.info.language}</span>`);
        if (data.info?.stars) meta.push(`<span class="sidebar-meta-tag">${icons.star} ${data.info.stars}</span>`);
        if (data.info?.forks) meta.push(`<span class="sidebar-meta-tag">${icons.fork} ${data.info.forks}</span>`);
        if (data.files) meta.push(`<span class="sidebar-meta-tag">${icons.fileText} ${data.files.length} files</span>`);
        if (data.commits) meta.push(`<span class="sidebar-meta-tag">${icons.gitCommit} ${data.commits.length} commits</span>`);
        if (data.info?.topics) { try { JSON.parse(data.info.topics).forEach(t => meta.push(`<span class="sidebar-meta-tag">${icons.hash} ${t}</span>`)); } catch{} }
        $('projectMeta').innerHTML = meta.join('');
        
        // Initialize the radial generator view for this project
        if (typeof initGeneratorForProject === 'function') {
            initGeneratorForProject(name);
        }
        
        await loadGeneratedSections();
    } catch(err) { console.error(err); }
}

loadProjectsList();

// ===== Content Viewer =====
const contentViewer = $('contentViewer'), cvClose = $('cvClose'), viewContentBtn = $('viewContentBtn');
const fileSearch = $('fileSearch'), tabFiles = $('tabFiles'), tabCommits = $('tabCommits');
let cvProjectData = null, cvAllFiles = [];

viewContentBtn.addEventListener('click', () => { if (currentProject) openContentViewer(currentProject); });
cvClose.addEventListener('click', closeContentViewer);
tabFiles.addEventListener('click', () => switchTab('files'));
tabCommits.addEventListener('click', () => switchTab('commits'));
fileSearch.addEventListener('input', e => { const q = e.target.value.toLowerCase(); renderFileList(cvAllFiles.filter(f => f.path.toLowerCase().includes(q))); });

function openContentViewer(projectName) {
    contentViewer.style.display = 'flex'; document.body.style.overflow = 'hidden';
    $('cvTitle').textContent = projectName;
    $('cvSubtitle').textContent = 'Loading...';
    $('fileList').innerHTML = '<div class="cv-loading"><div class="cv-spinner"></div> Loading files...</div>';
    $('fileContent').innerHTML = `<div class="cv-empty-content">${icons.chevLeft}<p>Select a file</p></div>`;
    $('commitsList').innerHTML = '<div class="cv-loading"><div class="cv-spinner"></div> Loading commits...</div>';
    switchTab('files'); fileSearch.value = '';
    fetch(`${API}/api/project/${projectName}`).then(r => r.json()).then(data => {
        cvProjectData = data; cvAllFiles = data.files || [];
        const fc = cvAllFiles.length, cc = (data.commits || []).length;
        $('cvSubtitle').textContent = `${fc} files \u00b7 ${cc} commits`;
        tabFiles.innerHTML = `${icons.folder} Files (${fc})`;
        tabCommits.innerHTML = `${icons.gitCommit} Commits (${cc})`;
        renderFileList(cvAllFiles); renderCommitsList(data.commits || []);
    }).catch(err => { $('cvSubtitle').textContent = 'Error loading'; console.error(err); });
}

function closeContentViewer() { contentViewer.style.display = 'none'; document.body.style.overflow = ''; cvProjectData = null; cvAllFiles = []; }

function switchTab(tab) {
    document.querySelectorAll('.cv-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.cv-panel').forEach(p => p.classList.remove('active'));
    if (tab === 'files') { tabFiles.classList.add('active'); $('panelFiles').classList.add('active'); }
    else { tabCommits.classList.add('active'); $('panelCommits').classList.add('active'); }
}

function getFileIcon(lang) { return icons.file; }

function renderFileList(files) {
    const fl = $('fileList');
    if (!files.length) { fl.innerHTML = '<div class="cv-loading">No files found</div>'; return; }
    fl.innerHTML = files.map((f, i) => `
        <div class="cv-file-item" onclick="showFileContent(${i})" data-index="${i}" id="fileItem_${i}">
            <span class="cv-file-icon">${getFileIcon(f.language)}</span>
            <span class="cv-file-name" title="${escapeHtml(f.path)}">${escapeHtml(f.path)}</span>
            ${f.language ? `<span class="cv-file-lang">${escapeHtml(f.language)}</span>` : ''}
        </div>
    `).join('');
}

function showFileContent(index) {
    const file = cvAllFiles[index]; if (!file) return;
    document.querySelectorAll('.cv-file-item').forEach(el => el.classList.remove('active'));
    const ael = $(`fileItem_${index}`); if (ael) ael.classList.add('active');
    const ca = $('fileContent');
    let h = '<div class="cv-file-detail">';
    h += `<div class="cv-file-detail-header"><h3>${escapeHtml(file.path)}</h3><div class="cv-file-detail-meta">
        ${file.language ? `<span>${icons.code} ${escapeHtml(file.language)}</span>` : ''}
        <span>${icons.pkg} ${formatSize(file.size)}</span></div></div>`;
    const meta = file.metadata || {};
    if (meta.imports && meta.imports.length > 0) {
        h += `<div class="cv-metadata-section"><h4>${icons.pkg} Imports (${meta.imports.length})</h4><div class="cv-metadata-chips">
            ${meta.imports.map(im => `<span class="cv-metadata-chip import">${escapeHtml(typeof im==='string'?im:im.module||JSON.stringify(im))}</span>`).join('')}</div></div>`;
    }
    const blocks = file.blocks || [];
    if (blocks.length > 0) {
        h += `<div class="cv-metadata-section"><h4>${icons.code} Code Chunks (${blocks.length})</h4><div class="cv-blocks-list">`;
        blocks.forEach(b => {
            let mData = null;
            if (b.block_type === 'function') mData = (meta.functions||[]).find(f => (f.name||f) === b.name);
            if (b.block_type === 'class') mData = (meta.classes||[]).find(c => (c.name||c) === b.name);
            if (b.block_type === 'method') { const pc = (meta.classes||[]).find(c => (c.name||c) === b.parent_name); if (pc && pc.methods) mData = pc.methods.find(m => (m.name||m) === b.name); }
            let header = b.name ? escapeHtml(b.name) : (b.block_type === 'module_level' ? 'Module Level Code' : escapeHtml(b.block_type));
            if (mData && mData.params) header += escapeHtml(mData.params);
            const typeIcon = b.block_type==='function'?icons.fn:b.block_type==='class'?icons.box:b.block_type==='method'?icons.wrench:icons.file;
            h += `<div class="cv-detail-card ${b.block_type}">
                <div class="cv-detail-header" onclick="this.parentElement.classList.toggle('expanded')">
                    <strong style="display:flex;align-items:center;gap:6px;">${typeIcon} ${header}</strong>
                    ${mData && mData.return_type ? ` <span style="color:var(--gray-400);margin-left:6px;font-size:12px;">\u2192 ${escapeHtml(mData.return_type)}</span>` : ''}
                    <span style="margin-left:auto;font-size:11px;color:var(--gray-400);display:flex;align-items:center;gap:4px;">L${b.start_line}-${b.end_line} ${icons.chevDown}</span>
                </div>
                <div class="cv-detail-body">
                    ${mData && mData.docstring ? `<div class="cv-docstring"><em>"${escapeHtml(mData.docstring)}"</em></div>` : ''}
                    ${mData && mData.decorators && mData.decorators.length ? `<div style="margin-top:4px;font-size:12px;"><strong>Decorators:</strong> ${mData.decorators.map(d => `<code style="background:var(--gray-100);padding:2px 6px;border-radius:4px;font-family:var(--font-mono);">${escapeHtml(d)}</code>`).join(' ')}</div>` : ''}
                    ${mData && mData.calls && mData.calls.length ? `<div style="margin-top:4px;font-size:12px;"><strong>Calls:</strong> ${mData.calls.map(c => `<span class="cv-metadata-chip" style="background:var(--orange-50);color:var(--orange-700);">${escapeHtml(c)}</span>`).join('')}</div>` : ''}
                    <div class="cv-code-wrapper" style="margin-top:8px;"><pre class="cv-code-block">${escapeHtml(b.content || '')}</pre></div>
                </div></div>`;
        });
        h += '</div></div>';
    } else if (file.content) {
        h += `<div class="cv-code-wrapper"><pre class="cv-code-block">${escapeHtml(file.content)}</pre></div>`;
    } else { h += '<div class="cv-loading">No content stored</div>'; }
    h += '</div>';
    ca.innerHTML = h; ca.scrollTop = 0;
}

function renderCommitsList(commits) {
    const list = $('commitsList');
    if (!commits.length) { list.innerHTML = '<div class="cv-loading">No commits found</div>'; return; }
    list.innerHTML = commits.map(c => {
        const date = c.date ? new Date(c.date).toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) : '';
        const lines = (c.message||'').split('\n'), title = lines[0], body = lines.slice(1).join('\n').trim();
        return `<div class="cv-commit-item">
            <span class="cv-commit-sha">${escapeHtml(c.sha||'')}</span>
            <div class="cv-commit-body">
                <div class="cv-commit-msg">${escapeHtml(title)}</div>
                ${body ? `<div class="cv-commit-msg" style="font-weight:400;color:var(--gray-500);font-size:13px;margin-top:4px;">${escapeHtml(body)}</div>` : ''}
                <div class="cv-commit-info"><span class="cv-commit-author">${escapeHtml(c.author||'')}</span>${date ? ` \u00b7 ${date}` : ''}</div>
            </div></div>`;
    }).join('');
}

function formatSize(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
    return (bytes/(1024*1024)).toFixed(1) + ' MB';
}
function escapeHtml(str) { if (!str) return ''; const d = document.createElement('div'); d.textContent = String(str); return d.innerHTML; }

// ===== Generated Content Logic =====
let currentGeneratedSections = [];
let activeGeneratedSectionId = null;

if ($('viewGeneratedBtn')) {
    $('viewGeneratedBtn').addEventListener('click', async () => {
        if (!currentProject) return;
        $('generatedOverlay').style.display = 'flex';
        document.body.style.overflow = 'hidden';
        await loadGeneratedSections();
    });
}

if ($('generatePdfBtn')) {
    $('generatePdfBtn').addEventListener('click', async () => {
        if (!currentProject) return;
        const btn = $('generatePdfBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Generating...';
        btn.disabled = true;
        try {
            // Collect skip/placeholder states from generator UI
            const skipSections = [];
            const placeholderSections = [];
            if (typeof sectionStates !== 'undefined') {
                Object.entries(sectionStates).forEach(([id, state]) => {
                    const sectionId = parseInt(id);
                    if (state.skip) skipSections.push(sectionId);
                    if (state.placeholder) placeholderSections.push(sectionId);
                });
            }
            
            const res = await fetch(`/api/project/${currentProject}/pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    skip_sections: skipSections,
                    placeholder_sections: placeholderSections
                })
            });
            if (!res.ok) throw new Error('Failed to generate PDF');
            
            // Trigger file download
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentProject}_revision.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            console.error(e);
            alert('Failed to generate PDF: ' + e.message);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

if ($('closeGeneratedBtn')) {
    $('closeGeneratedBtn').addEventListener('click', () => {
        $('generatedOverlay').style.display = 'none';
        document.body.style.overflow = '';
    });
}

async function loadGeneratedSections() {
    if (!currentProject) return;
    try {
        const res = await fetch(`/api/project/${currentProject}/generated`);
        if (!res.ok) throw new Error('Failed to load generated sections');
        currentGeneratedSections = await res.json();
        renderGeneratedSectionsList();
        
        // Reset viewer
        activeGeneratedSectionId = null;
        $('generatedViewerTitle').textContent = 'Select a section';
        $('generatedViewerContent').textContent = '';
        $('deleteGeneratedBtn').style.display = 'none';
        
        if (window.syncGeneratedStatus) {
            window.syncGeneratedStatus(currentGeneratedSections.map(s => s.section_id));
        }
        
    } catch (e) {
        console.error(e);
        $('generatedList').innerHTML = `<div style="color:#ef4444; font-size:12px;">Error: ${e.message}</div>`;
    }
}

function renderGeneratedSectionsList() {
    const list = $('generatedList');
    if (!list) return;
    
    if (currentGeneratedSections.length === 0) {
        list.innerHTML = '<div style="color:var(--text-muted); font-size:12px; padding: 10px;">No sections generated yet.</div>';
        return;
    }
    
    list.innerHTML = currentGeneratedSections.map(sec => `
        <div class="cv-file-item ${activeGeneratedSectionId === sec.section_id ? 'active' : ''}" onclick="selectGeneratedSection(${sec.section_id})">
            <span class="cv-file-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg>
            </span>
            <div style="display:flex; flex-direction:column; overflow:hidden; flex:1;">
                <span class="cv-file-name" style="font-size:13px; font-family:var(--font-sans);">${escapeHtml(sec.name)}</span>
                <span style="font-size:10px; color:var(--text-muted);">${new Date(sec.generated_at).toLocaleString()}</span>
            </div>
        </div>
    `).join('');
}

window.selectGeneratedSection = function(id) {
    activeGeneratedSectionId = id;
    const sec = currentGeneratedSections.find(s => s.section_id === id);
    if (!sec) return;
    
    renderGeneratedSectionsList(); // to update active state
    
    $('generatedViewerTitle').textContent = `${id}. ${sec.name}`;
    $('generatedViewerContent').textContent = typeof sec.content === 'object' ? JSON.stringify(sec.content, null, 2) : sec.content;
    $('deleteGeneratedBtn').style.display = 'block';
    
    // Attach delete handler (remove old listeners by replacing clone)
    const delBtn = $('deleteGeneratedBtn');
    const newDelBtn = delBtn.cloneNode(true);
    delBtn.parentNode.replaceChild(newDelBtn, delBtn);
    
    newDelBtn.addEventListener('click', async () => {
        if (!confirm(`Are you sure you want to delete ${sec.name}?`)) return;
        try {
            const res = await fetch(`/api/project/${currentProject}/generated/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error('Failed to delete');
            await loadGeneratedSections();
        } catch(e) {
            alert(e.message);
        }
    });
};
