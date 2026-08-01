const API = '';
let currentProject = null;
let pollInterval = null;

// ===== Toast Notification System =====
const TOAST_ICONS = {
    success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    info: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
};
window.showToast = function (message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span class="toast-icon">${TOAST_ICONS[type] || TOAST_ICONS.info}</span><span class="toast-message">${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    toast.addEventListener('click', () => dismissToast(toast));
    setTimeout(() => dismissToast(toast), duration);
};
function dismissToast(toast) {
    if (toast.classList.contains('toast-exit')) return;
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
}

// ===== Theme Toggle =====
function initTheme() {
    const saved = localStorage.getItem('builtbyme-theme') || 'dark';
    applyTheme(saved);
}
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const sunIcon = document.getElementById('themeIconSun');
    const moonIcon = document.getElementById('themeIconMoon');
    if (sunIcon && moonIcon) {
        // Show sun icon in dark mode (to switch to light), moon in light mode (to switch to dark)
        sunIcon.style.display = theme === 'dark' ? 'block' : 'none';
        moonIcon.style.display = theme === 'light' ? 'block' : 'none';
    }
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('builtbyme-theme', next);
    applyTheme(next);
    showToast(`Switched to ${next} mode`, 'info', 2000);
}
initTheme();

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
menuBtn.addEventListener('click', e => { e.stopPropagation(); menuDropdown.classList.toggle('show'); if (menuDropdown.classList.contains('show')) { loadProjectsList(); const si = document.getElementById('projectSearchInput'); if (si) { si.value = ''; } } });
document.addEventListener('click', () => menuDropdown.classList.remove('show'));
menuDropdown.addEventListener('click', e => e.stopPropagation());
addProjectBtn.addEventListener('click', () => { menuDropdown.classList.remove('show'); openModal(); });
modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
startExtractionBtn.addEventListener('click', startExtraction);

// Theme toggle
const themeToggleBtn = $('themeToggle');
if (themeToggleBtn) themeToggleBtn.addEventListener('click', toggleTheme);

// Project search
const projectSearchInput = $('projectSearchInput');
if (projectSearchInput) {
    projectSearchInput.addEventListener('input', e => {
        const query = e.target.value.toLowerCase();
        const items = projectsList.querySelectorAll('.menu-item:not(.disabled)');
        items.forEach(item => {
            const name = item.textContent.toLowerCase();
            item.style.display = name.includes(query) ? '' : 'none';
        });
    });
    projectSearchInput.addEventListener('click', e => e.stopPropagation());
}

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
        const r = await fetch(`${API}/api/config/pat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pat }) });
        const d = await r.json();
        st.style.display = 'flex'; st.className = 'config-status success'; st.textContent = d.message || 'Saved successfully';
        setTimeout(() => st.style.display = 'none', 3000);
    } catch (e) { st.style.display = 'flex'; st.className = 'config-status error'; st.textContent = 'Failed to save'; }
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
        const resp = await fetch(`${API}/api/extract`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ repo_url: repoUrl, token: token || null, ignore_patterns: ignorePatterns }) });
        const data = await resp.json();
        if (!resp.ok) { showError(data.error || 'Failed to start extraction'); startExtractionBtn.disabled = false; return; }
        pollExtractionStatus(data.project_name);
    } catch (err) { showError('Network error: ' + err.message); startExtractionBtn.disabled = false; }
}

function pollExtractionStatus(projectName) {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(async () => {
        try {
            const resp = await fetch(`${API}/api/extract/status/${projectName}`);
            const data = await resp.json();
            if (['extracting', 'fetching_info', 'fetching_commits', 'fetching_tree'].includes(data.status)) {
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
        } catch (err) { console.error('Poll error:', err); }
    }, 1000);
}

function updateProgress(text, pct, file) {
    $('progressBar').style.width = pct + '%';
    $('progressText').textContent = text;
    $('progressFile').textContent = file;
}
function showError(msg) { errorArea.style.display = 'block'; $('errorText').textContent = msg; showToast(msg, 'error'); }

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
        if (resp.ok) { if (currentProject === name) { currentProject = null; emptyState.style.display = 'flex'; projectView.style.display = 'none'; } loadProjectsList(); showToast(`Project '${name}' deleted`, 'success'); }
        else showToast('Failed to delete project', 'error');
    } catch (e) { showToast('Error deleting project', 'error'); }
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
        if (data.info?.topics) { try { JSON.parse(data.info.topics).forEach(t => meta.push(`<span class="sidebar-meta-tag">${icons.hash} ${t}</span>`)); } catch { } }
        $('projectMeta').innerHTML = meta.join('');

        // Initialize the radial generator view for this project
        if (typeof initGeneratorForProject === 'function') {
            initGeneratorForProject(name);
        }

        await loadGeneratedSections();
    } catch (err) { console.error(err); }
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
            ${meta.imports.map(im => `<span class="cv-metadata-chip import">${escapeHtml(typeof im === 'string' ? im : im.module || JSON.stringify(im))}</span>`).join('')}</div></div>`;
    }
    const blocks = file.blocks || [];
    if (blocks.length > 0) {
        h += `<div class="cv-metadata-section"><h4>${icons.code} Code Chunks (${blocks.length})</h4><div class="cv-blocks-list">`;
        blocks.forEach(b => {
            let mData = null;
            if (b.block_type === 'function') mData = (meta.functions || []).find(f => (f.name || f) === b.name);
            if (b.block_type === 'class') mData = (meta.classes || []).find(c => (c.name || c) === b.name);
            if (b.block_type === 'method') { const pc = (meta.classes || []).find(c => (c.name || c) === b.parent_name); if (pc && pc.methods) mData = pc.methods.find(m => (m.name || m) === b.name); }
            let header = b.name ? escapeHtml(b.name) : (b.block_type === 'module_level' ? 'Module Level Code' : escapeHtml(b.block_type));
            if (mData && mData.params) header += escapeHtml(mData.params);
            const typeIcon = b.block_type === 'function' ? icons.fn : b.block_type === 'class' ? icons.box : b.block_type === 'method' ? icons.wrench : icons.file;
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
        const date = c.date ? new Date(c.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
        const lines = (c.message || '').split('\n'), title = lines[0], body = lines.slice(1).join('\n').trim();
        return `<div class="cv-commit-item">
            <span class="cv-commit-sha">${escapeHtml(c.sha || '')}</span>
            <div class="cv-commit-body">
                <div class="cv-commit-msg">${escapeHtml(title)}</div>
                ${body ? `<div class="cv-commit-msg" style="font-weight:400;color:var(--gray-500);font-size:13px;margin-top:4px;">${escapeHtml(body)}</div>` : ''}
                <div class="cv-commit-info"><span class="cv-commit-author">${escapeHtml(c.author || '')}</span>${date ? ` \u00b7 ${date}` : ''}</div>
            </div></div>`;
    }).join('');
}

function formatSize(bytes) {
    if (!bytes) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
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

// ===== PDF Theme Selection =====
let selectedPdfTheme = 'sunrise';
document.querySelectorAll('.theme-swatch').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.theme-swatch').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedPdfTheme = btn.dataset.theme || 'sunrise';
    });
});

if ($('generatePdfBtn')) {
    $('generatePdfBtn').addEventListener('click', async () => {
        if (!currentProject) return;
        const btn = $('generatePdfBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Generating...';
        btn.disabled = true;
        try {
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
                    placeholder_sections: placeholderSections,
                    theme: selectedPdfTheme
                })
            });
            if (!res.ok) throw new Error('Failed to generate PDF');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentProject}_revision.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showToast('PDF generated and downloaded!', 'success');
        } catch (e) {
            console.error(e);
            showToast('Failed to generate PDF: ' + e.message, 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}


// ===== Export Markdown =====
if ($('exportMarkdownBtn')) {
    $('exportMarkdownBtn').addEventListener('click', async () => {
        if (!currentProject) return;
        const btn = $('exportMarkdownBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Exporting...';
        btn.disabled = true;
        try {
            const skipSections = [];
            const placeholderSections = [];
            if (typeof sectionStates !== 'undefined') {
                Object.entries(sectionStates).forEach(([id, state]) => {
                    const sectionId = parseInt(id);
                    if (state.skip) skipSections.push(sectionId);
                    if (state.placeholder) placeholderSections.push(sectionId);
                });
            }
            const res = await fetch(`/api/project/${currentProject}/markdown`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ skip_sections: skipSections, placeholder_sections: placeholderSections })
            });
            if (!res.ok) throw new Error('Failed to export Markdown');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentProject}_docs.md`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showToast('Markdown exported successfully!', 'success');
        } catch (e) {
            console.error(e);
            showToast('Failed to export Markdown: ' + e.message, 'error');
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

window.selectGeneratedSection = function (id) {
    activeGeneratedSectionId = id;
    const sec = currentGeneratedSections.find(s => s.section_id === id);
    if (!sec) return;

    renderGeneratedSectionsList();

    $('generatedViewerTitle').textContent = `${id}. ${sec.name}`;
    $('generatedViewerContent').textContent = typeof sec.content === 'object' ? JSON.stringify(sec.content, null, 2) : sec.content;
    $('deleteGeneratedBtn').style.display = 'block';

    // Render formatted preview
    renderSectionPreview(id, sec.content);
    // Show preview tab by default
    switchGeneratedView('preview');

    // Attach delete handler
    const delBtn = $('deleteGeneratedBtn');
    const newDelBtn = delBtn.cloneNode(true);
    delBtn.parentNode.replaceChild(newDelBtn, delBtn);

    newDelBtn.addEventListener('click', async () => {
        if (!confirm(`Are you sure you want to delete ${sec.name}?`)) return;
        try {
            const res = await fetch(`/api/project/${currentProject}/generated/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error('Failed to delete');
            await loadGeneratedSections();
            showToast(`${sec.name} deleted`, 'success');
        } catch (e) {
            showToast(e.message, 'error');
        }
    });
};

// ===== Preview / Raw Tab Toggle =====
function switchGeneratedView(view) {
    const preview = $('generatedPreviewContent');
    const raw = $('generatedViewerContent');
    const tabPreview = $('tabPreview');
    const tabRaw = $('tabRaw');
    if (!preview || !raw) return;
    if (view === 'preview') {
        preview.style.display = 'flex';
        raw.style.display = 'none';
        if (tabPreview) tabPreview.classList.add('active');
        if (tabRaw) tabRaw.classList.remove('active');
    } else {
        preview.style.display = 'none';
        raw.style.display = 'block';
        if (tabPreview) tabPreview.classList.remove('active');
        if (tabRaw) tabRaw.classList.add('active');
    }
}
if ($('tabPreview')) $('tabPreview').addEventListener('click', () => switchGeneratedView('preview'));
if ($('tabRaw')) $('tabRaw').addEventListener('click', () => switchGeneratedView('raw'));

// ===== Section Preview Renderer =====
function renderSectionPreview(sectionId, content) {
    const container = $('generatedPreviewContent');
    if (!container) return;
    if (!content || (typeof content === 'object' && Object.keys(content).length === 0)) {
        container.innerHTML = '<div class="preview-empty">No content to preview</div>';
        return;
    }
    const data = typeof content === 'string' ? (() => { try { return JSON.parse(content); } catch { return null; } })() : content;
    if (!data || typeof data !== 'object') {
        container.innerHTML = `<div class="preview-card"><div class="preview-field-val">${escapeHtml(String(content))}</div></div>`;
        return;
    }

    // Section 6 has special structure: { deep_dives: [...FrameworkDeepDive] }
    if (sectionId === 6 && data.deep_dives && Array.isArray(data.deep_dives)) {
        container.innerHTML = renderSection6Preview(data.deep_dives);
        return;
    }

    let html = '';
    for (const [key, value] of Object.entries(data)) {
        const title = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        if (Array.isArray(value)) {
            html += renderArrayCard(title, value);
        } else if (typeof value === 'object' && value !== null) {
            html += `<div class="preview-card"><div class="preview-card-title">${escapeHtml(title)}</div>`;
            for (const [k, v] of Object.entries(value)) {
                html += renderField(k, v);
            }
            html += '</div>';
        } else {
            html += `<div class="preview-card"><div class="preview-card-title">${escapeHtml(title)}</div>`;
            html += renderField(key, value);
            html += '</div>';
        }
    }
    container.innerHTML = html || '<div class="preview-empty">No content to preview</div>';
}

function renderSection6Preview(deepDives) {
    let html = '';
    deepDives.forEach((fw, idx) => {
        const fwName = fw.framework_name || fw.name || `Framework ${idx + 1}`;
        const category = fw.category || '';
        html += `<div class="preview-card" style="border-left-color: ${['#f97316', '#3b82f6', '#22c55e', '#a855f7', '#ef4444', '#eab308'][idx % 6]};">`;
        html += `<div class="preview-card-title" style="font-size:15px;margin-bottom:14px;">
            ${escapeHtml(fwName)}
            ${category ? `<span class="preview-badge preview-badge-purple">${escapeHtml(category)}</span>` : ''}
        </div>`;

        // Basics
        if (fw.basics && fw.basics.length > 0) {
            html += `<div style="margin-bottom:16px;"><div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:var(--green-500);margin-bottom:8px;display:flex;align-items:center;"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg> Basics <span class="preview-badge preview-badge-green" style="margin-left:6px;">${fw.basics.length}</span></div>`;
            fw.basics.forEach(concept => {
                html += renderConceptCard(concept, 'rgba(34,197,94,0.08)', 'var(--green-500)');
            });
            html += '</div>';
        }

        // Directly Used Concepts
        if (fw.directly_used_concepts && fw.directly_used_concepts.length > 0) {
            html += `<div style="margin-bottom:16px;"><div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:var(--orange-400);margin-bottom:8px;display:flex;align-items:center;"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Directly Used <span class="preview-badge preview-badge-orange" style="margin-left:6px;">${fw.directly_used_concepts.length}</span></div>`;
            fw.directly_used_concepts.forEach(concept => {
                html += renderConceptCard(concept, 'rgba(249,115,22,0.08)', 'var(--orange-400)');
            });
            html += '</div>';
        }

        // Indirect Concepts
        if (fw.indirect_concepts && fw.indirect_concepts.length > 0) {
            html += `<div><div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:var(--blue-500);margin-bottom:8px;display:flex;align-items:center;"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg> Indirect / Interview Knowledge <span class="preview-badge preview-badge-blue" style="margin-left:6px;">${fw.indirect_concepts.length}</span></div>`;
            fw.indirect_concepts.forEach(concept => {
                html += renderConceptCard(concept, 'rgba(59,130,246,0.08)', 'var(--blue-500)');
            });
            html += '</div>';
        }

        html += '</div>';
    });
    return html || '<div class="preview-empty">No deep dives to preview</div>';
}

function renderConceptCard(concept, bgColor, accentColor) {
    const title = concept.title || concept.name || 'Concept';
    const explanation = concept.explanation || '';
    const codeSnippet = concept.code_snippet || '';
    let html = `<div style="background:${bgColor};border-radius:var(--radius-sm);padding:12px 14px;margin-bottom:8px;border-left:3px solid ${accentColor};">`;
    html += `<div style="font-weight:700;font-size:13px;color:${accentColor};margin-bottom:6px;">${escapeHtml(title)}</div>`;
    if (explanation) {
        html += `<div style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:${codeSnippet ? '8' : '0'}px;">${escapeHtml(explanation)}</div>`;
    }
    if (codeSnippet) {
        html += `<pre style="background:#0d0d10;color:#d4d4d4;padding:10px 14px;border-radius:var(--radius-sm);font-family:var(--font-mono);font-size:11px;line-height:1.5;overflow-x:auto;white-space:pre-wrap;margin-top:4px;max-height:200px;overflow-y:auto;">${escapeHtml(codeSnippet)}</pre>`;
    }
    html += '</div>';
    return html;
}

function renderArrayCard(title, value) {
    let html = `<div class="preview-card"><div class="preview-card-title">${escapeHtml(title)} <span class="preview-badge preview-badge-blue">${value.length} items</span></div>`;
    if (value.length === 0) {
        html += '<div class="preview-field-val" style="font-style:italic;color:var(--text-dim);">Empty</div>';
    } else if (typeof value[0] === 'object' && value[0] !== null) {
        value.forEach((item, i) => {
            html += `<div style="border-top:1px solid var(--dark-border);padding-top:10px;margin-top:10px;">`;
            const itemName = item.name || item.title || item.question || item.framework_name || item.framework || item.technology || `Item ${i + 1}`;
            html += `<div style="font-weight:700;color:var(--orange-400);font-size:13px;margin-bottom:6px;">${escapeHtml(itemName)}</div>`;
            for (const [k, v] of Object.entries(item)) {
                if (['name', 'title', 'framework_name'].includes(k)) continue;
                html += renderField(k, v);
            }
            html += '</div>';
        });
    } else {
        html += '<ul class="preview-list">';
        value.forEach(item => { html += `<li>${escapeHtml(String(item))}</li>`; });
        html += '</ul>';
    }
    html += '</div>';
    return html;
}

function renderField(key, value) {
    const fieldTitle = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const isCodeField = /code_snippet|code_example|snippet|source_code/i.test(key);

    if (isCodeField && typeof value === 'string' && value.trim()) {
        return `<div class="preview-field" style="flex-direction:column;gap:6px;">
            <div class="preview-field-key">${escapeHtml(fieldTitle)}</div>
            <pre style="background:#0d0d10;color:#d4d4d4;padding:10px 14px;border-radius:var(--radius-sm);font-family:var(--font-mono);font-size:11px;line-height:1.5;overflow-x:auto;white-space:pre-wrap;max-height:200px;overflow-y:auto;margin:0;">${escapeHtml(value)}</pre>
        </div>`;
    }

    if (Array.isArray(value)) {
        if (value.length === 0) return '';
        if (typeof value[0] === 'object') {
            let nested = `<div class="preview-field" style="flex-direction:column;gap:6px;"><div class="preview-field-key">${escapeHtml(fieldTitle)} <span class="preview-badge preview-badge-blue">${value.length}</span></div>`;
            value.forEach((item, i) => {
                const subName = item.name || item.title || `${i + 1}`;
                nested += `<div style="padding:8px;background:rgba(255,255,255,0.02);border-radius:var(--radius-sm);border:1px solid var(--dark-border);margin-top:4px;">`;
                nested += `<div style="font-weight:600;font-size:12px;color:var(--orange-400);margin-bottom:4px;">${escapeHtml(subName)}</div>`;
                for (const [sk, sv] of Object.entries(item)) {
                    if (['name', 'title'].includes(sk)) continue;
                    nested += renderField(sk, sv);
                }
                nested += '</div>';
            });
            nested += '</div>';
            return nested;
        }
        return `<div class="preview-field"><div class="preview-field-key">${escapeHtml(fieldTitle)}</div><div class="preview-field-val">${value.map(x => escapeHtml(String(x))).join(', ')}</div></div>`;
    }

    return `<div class="preview-field"><div class="preview-field-key">${escapeHtml(fieldTitle)}</div><div class="preview-field-val">${formatPreviewValue(value)}</div></div>`;
}

function formatPreviewValue(v) {
    if (Array.isArray(v)) {
        if (v.length === 0) return '<span style="color:var(--text-dim);font-style:italic;">None</span>';
        return v.map(item => typeof item === 'object' ? escapeHtml(JSON.stringify(item)) : escapeHtml(String(item))).join(', ');
    }
    if (typeof v === 'boolean') return v ? '<span class="preview-badge preview-badge-green">Yes</span>' : '<span class="preview-badge preview-badge-red">No</span>';
    if (v === null || v === undefined) return '<span style="color:var(--text-dim);font-style:italic;">N/A</span>';
    return escapeHtml(String(v));
}

// ===== Keyboard Shortcuts =====
document.addEventListener('keydown', (e) => {
    // Don't trigger shortcuts when typing in inputs/textareas
    const tag = document.activeElement?.tagName?.toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') {
        if (e.key === 'Escape') { document.activeElement.blur(); }
        return;
    }
    // Escape — close any open modal/overlay
    if (e.key === 'Escape') {
        e.preventDefault();
        if ($('customSectionCreateModal')?.style.display !== 'none' && $('customSectionCreateModal')?.style.display) { $('customSectionCreateModal').style.display = 'none'; return; }
        if ($('userGuideOverlay')?.style.display !== 'none' && $('userGuideOverlay')?.style.display) { $('userGuideOverlay').style.display = 'none'; document.body.style.overflow = ''; return; }
        if ($('generatedOverlay')?.style.display !== 'none' && $('generatedOverlay')?.style.display) { $('generatedOverlay').style.display = 'none'; document.body.style.overflow = ''; return; }
        if ($('contentViewer')?.style.display !== 'none' && $('contentViewer')?.style.display) { closeContentViewer(); return; }
        if ($('configOverlay')?.style.display !== 'none' && $('configOverlay')?.style.display) { closeConfig(); return; }
        if ($('modalOverlay')?.style.display !== 'none' && $('modalOverlay')?.style.display) { closeModal(); return; }
        if (menuDropdown?.classList.contains('show')) { menuDropdown.classList.remove('show'); return; }
        return;
    }
    if (!e.ctrlKey && !e.metaKey) return;
    switch (e.key.toLowerCase()) {
        case 'n': e.preventDefault(); menuDropdown.classList.remove('show'); openModal(); break;
        case 'k': e.preventDefault(); menuDropdown.classList.add('show'); loadProjectsList(); setTimeout(() => { const si = $('projectSearchInput'); if (si) si.focus(); }, 100); break;
        case ',': e.preventDefault(); menuDropdown.classList.remove('show'); openConfig(); break;
        case 'g': e.preventDefault(); if (currentProject && $('generatePdfBtn')) $('generatePdfBtn').click(); break;
        case 'm': e.preventDefault(); if (currentProject && $('exportMarkdownBtn')) $('exportMarkdownBtn').click(); break;
    }
});

// ===== Custom Sections Feature (Configuration Modal & Radial Integration) =====
(function initCustomSections() {
    const modal = $('customSectionCreateModal');
    const closeBtn = $('customModalClose');
    const menuBtn = $('customSectionsBtn');
    const submitBtn = $('customModalSubmitBtn');
    const titleInput = $('customModalTitle');
    const descInput = $('customModalDesc');

    if (menuBtn && modal) {
        menuBtn.addEventListener('click', () => {
            if (!currentProject) {
                showToast('Please select a project first.', 'warning');
                return;
            }
            if (menuDropdown) menuDropdown.classList.remove('show');
            modal.style.display = 'flex';
            if (titleInput) { titleInput.value = ''; titleInput.focus(); }
            if (descInput) { descInput.value = ''; }
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    if (submitBtn) {
        submitBtn.addEventListener('click', async () => {
            if (!currentProject) return;
            const title = titleInput?.value.trim();
            const desc = descInput?.value.trim();
            if (!title) {
                showToast('Please enter a custom section title.', 'warning');
                if (titleInput) titleInput.focus();
                return;
            }
            if (!desc) {
                showToast('Please provide instructions/description for this section.', 'warning');
                if (descInput) descInput.focus();
                return;
            }

            submitBtn.disabled = true;
            try {
                const res = await fetch(`/api/project/${currentProject}/custom_section_def`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ section_title: title, section_description: desc })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to create custom section definition.');

                showToast(`Custom Section "${title}" added to Radial Generator!`, 'success');
                modal.style.display = 'none';

                if (window.initGeneratorForProject) {
                    await window.initGeneratorForProject(currentProject);
                }
            } catch (e) {
                showToast(e.message, 'error');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    // === Radial Generator Panel: Custom Action Buttons ===
    const copyPromptBtn = $('genCopyPromptBtn');
    const showPasteBtn = $('genShowPasteBtn');
    const deleteCustomBtn = $('genDeleteCustomBtn');
    const submitPasteBtn = $('genSubmitPasteBtn');
    const pasteInput = $('genPasteInput');
    const pasteArea = $('genPasteArea');

    if (copyPromptBtn) {
        copyPromptBtn.addEventListener('click', async () => {
            if (!currentProject || !window.activeSection) return;
            const secTitleEl = $('genPanelTitle');
            const secDescEl = $('genPanelSubtitle');
            const title = secTitleEl ? secTitleEl.textContent.replace(/^\d+\.\s*/, '').trim() : `Custom Section`;
            const desc = secDescEl ? secDescEl.textContent.trim() : '';

            copyPromptBtn.disabled = true;
            try {
                const res = await fetch(`/api/project/${currentProject}/custom_prompt`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ section_title: title, section_description: desc })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to generate prompt');

                await navigator.clipboard.writeText(data.prompt);
                showToast('Prompt copied to clipboard! Paste into ChatGPT, Claude, etc.', 'success');
            } catch (e) {
                showToast(e.message, 'error');
            } finally {
                copyPromptBtn.disabled = false;
            }
        });
    }

    if (showPasteBtn && pasteArea) {
        showPasteBtn.addEventListener('click', () => {
            if (pasteArea.style.display === 'none' || !pasteArea.style.display) {
                pasteArea.style.display = 'flex';
                if (pasteInput) { pasteInput.value = ''; pasteInput.focus(); }
            } else {
                pasteArea.style.display = 'none';
            }
        });
    }

    if (submitPasteBtn && pasteInput) {
        submitPasteBtn.addEventListener('click', async () => {
            if (!currentProject || !window.activeSection) return;
            const content = pasteInput.value.trim();
            if (!content) {
                showToast('Please paste the AI response JSON.', 'warning');
                pasteInput.focus();
                return;
            }

            const secTitleEl = $('genPanelTitle');
            const title = secTitleEl ? secTitleEl.textContent.replace(/^\d+\.\s*/, '').trim() : `Custom ${window.activeSection}`;

            submitPasteBtn.disabled = true;
            try {
                const res = await fetch(`/api/project/${currentProject}/add_custom_manual`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ section_title: title, content: content, section_id: window.activeSection })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to save section');

                showToast(`Section saved successfully!`, 'success');
                if (pasteArea) pasteArea.style.display = 'none';
                if (window.initGeneratorForProject) {
                    await window.initGeneratorForProject(currentProject);
                }
            } catch (e) {
                showToast(e.message, 'error');
            } finally {
                submitPasteBtn.disabled = false;
            }
        });
    }

    if (deleteCustomBtn) {
        deleteCustomBtn.addEventListener('click', async () => {
            if (!currentProject || !window.activeSection) return;
            if (!confirm('Are you sure you want to completely remove this custom section?')) return;

            deleteCustomBtn.disabled = true;
            try {
                const delDefRes = await fetch(`/api/project/${currentProject}/custom_section_def/${window.activeSection}`, { method: 'DELETE' });
                await fetch(`/api/project/${currentProject}/generated/${window.activeSection}`, { method: 'DELETE' }).catch(()=>{});

                if (!delDefRes.ok && delDefRes.status !== 404) throw new Error('Failed to delete section');
                showToast('Custom section deleted.', 'success');
                
                if (window.initGeneratorForProject) {
                    await window.initGeneratorForProject(currentProject);
                }
            } catch (e) {
                showToast(e.message, 'error');
            } finally {
                deleteCustomBtn.disabled = false;
            }
        });
    }
})();

