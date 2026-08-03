// ===== PDF Generator UI — Section Data & Logic (UI Only) =====

const DEFAULT_SECTIONS = [
    { id: 1, name: 'Project Overview', short: 'Overview', desc: 'Project name, description, domain, stack, problem, workflow, deployment, elevator pitch.' },
    { id: 2, name: 'Tech Stack & Dependencies', short: 'Tech Stack', desc: 'Libraries, frameworks, versions, purposes, alternatives, architectural layers.' },
    { id: 3, name: 'Architecture & Module Map', short: 'Architecture', desc: 'Folder structure, module purposes, entry points, data flow, system diagrams.' },
    { id: 4, name: 'Environment & Secrets', short: 'Env Config', desc: 'Environment variables, API keys, config settings, dev vs production setup.' },
    { id: 5, name: 'Core Functions & Classes', short: 'Core Code', desc: 'Important functions/classes, file locations, purpose, inputs, outputs.' },
    { id: 6, name: 'Technology Deep Dives', short: 'Deep Dives', desc: 'Major technologies explained, how they work, why they fit, related concepts.' },
    { id: 7, name: 'Design Decisions', short: 'Decisions', desc: 'Engineering decisions, rationale, trade-offs, patterns, architectural principles.' },
    { id: 8, name: 'Failure Log & Learnings', short: 'Failures', desc: 'Problems encountered, attempted solutions, root causes, lessons learned.' },
    { id: 9, name: 'APIs & Interfaces', short: 'APIs', desc: 'REST endpoints, HTTP methods, request/response formats, error handling.' },
    { id: 10, name: 'Data Models & Storage', short: 'Data Layer', desc: 'Database models, schema, storage choices, indexing, persistence mechanisms.' },
    { id: 11, name: 'Testing Strategy', short: 'Testing', desc: 'Test coverage, frameworks, unit/integration plans, mocking, testing theory.' },
    { id: 12, name: 'Scalability & Production', short: 'Scale', desc: 'Bottlenecks, scaling analysis, code smells, security, monitoring gaps.' },
    { id: 13, name: 'Deployment & Infra', short: 'Deploy', desc: 'Hosting, CI/CD, infrastructure, environment separation, DevOps.' },
    { id: 14, name: 'Interview Question Bank', short: 'Questions', desc: 'Advanced questions based on the project, detailed answers, discussion points.' },
];
let SECTIONS = [...DEFAULT_SECTIONS];

const NODE_ICONS = {
    1: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    2: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    3: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    4: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    5: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    6: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    7: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    8: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    9: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
    10: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    11: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    12: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    13: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/></svg>',
    14: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
};

// Per-section state
let sectionStates = {};
let activeSection = null;

// Track which sections have been explicitly given a per-section API key override.
// When a common key is applied, sections in this set are NOT overwritten.
let sectionKeyOverrides = new Set();

// Track the current common key value so we can detect overrides properly
let currentCommonApiKey = '';
let currentCommonProvider = '';

function initSectionStates() {
    sectionStates = {};
    // Reset per-section overrides when switching projects or reinitializing
    sectionKeyOverrides = new Set();
    currentCommonApiKey = '';
    currentCommonProvider = '';
    SECTIONS.forEach(s => {
        sectionStates[s.id] = {
            provider: 'gemini', apiKey: '', detailLevel: (s.id === 6 || s.id === 14) ? 2 : 1,
            skip: false, placeholder: false, locked: false,
            customInstructions: '', strategy: '1_pass',
            status: 'idle', // idle | generating | completed
        };
    });
}
initSectionStates();

// ===== Initialize for Selected Project =====
async function initGeneratorForProject(projectName) {
    document.getElementById('genHubProject').textContent = projectName || 'Project';
    SECTIONS = [...DEFAULT_SECTIONS];
    initSectionStates(); // Reset states for new project
    activeSection = null;
    closePanel();

    const genAllBtn = document.getElementById('genAllBtnLeft') || document.getElementById('genHubBtn');
    if (genAllBtn) genAllBtn.disabled = false;

    if (projectName) {
        try {
            const defsRes = await fetch(`/api/project/${projectName}/custom_section_defs`);
            const genRes = await fetch(`/api/project/${projectName}/generated`);
            const defs = defsRes.ok ? await defsRes.json() : [];
            const gen = genRes.ok ? await genRes.json() : [];

            const customMap = new Map();
            defs.forEach(d => customMap.set(d.section_id, { id: d.section_id, name: d.name, short: d.name.split(' ')[0] || 'Custom', desc: d.description, isCustom: true }));
            gen.forEach(g => {
                if (g.section_id >= 100 && !customMap.has(g.section_id)) {
                    customMap.set(g.section_id, { id: g.section_id, name: g.name, short: g.name.split(' ')[0] || 'Custom', desc: 'Custom documentation section', isCustom: true });
                }
            });

            const sortedCustoms = Array.from(customMap.values()).sort((a, b) => a.id - b.id);
            SECTIONS.push(...sortedCustoms);
            initSectionStates();

            const completedIds = gen.map(g => g.section_id);
            SECTIONS.forEach(sec => {
                if (completedIds.includes(sec.id) && sectionStates[sec.id]) {
                    sectionStates[sec.id].status = 'completed';
                }
            });
        } catch (e) {
            console.error('Failed to load custom sections for radial generator:', e);
        }
    }
    renderNodes();
    updateProgressRing();
}
window.initGeneratorForProject = initGeneratorForProject;

// ===== Render Radial Nodes =====
function renderNodes() {
    const container = document.getElementById('genNodesContainer');
    container.innerHTML = '';

    const total = SECTIONS.length;
    const radius = 230; // px from center
    const cx = 290, cy = 290; // center of 580px container

    SECTIONS.forEach((sec, i) => {
        const angle = (i / total) * 2 * Math.PI - Math.PI / 2;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);

        // Connection line
        const line = document.createElement('div');
        line.className = 'gen-connection' + (sec.id >= 100 ? ' custom-connection' : '');
        const dx = x - cx, dy = y - cy;
        const len = Math.sqrt(dx * dx + dy * dy) - 36;
        const deg = Math.atan2(dy, dx) * 180 / Math.PI;
        line.style.cssText = `width:${len}px;transform:rotate(${deg}deg);`;
        container.appendChild(line);

        // Node
        const state = sectionStates[sec.id] || { status: 'idle', skip: false, locked: false };
        const node = document.createElement('div');
        node.className = 'gen-node' + (sec.id >= 100 ? ' custom-node' : '');
        node.id = `genNode_${sec.id}`;
        if (activeSection === sec.id) node.classList.add('active');
        if (state.locked) node.classList.add('locked');
        if (state.skip) node.classList.add('skipped');
        if (state.status === 'generating') node.classList.add('generating');
        if (state.status === 'completed') node.classList.add('completed');

        node.style.left = x + 'px';
        node.style.top = y + 'px';

        // Status badge
        let statusBadge = '';
        if (state.locked) statusBadge = '<div class="gen-node-status locked-icon"><svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>';
        else if (state.status === 'completed') statusBadge = '<div class="gen-node-status done-icon"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg></div>';
        else if (state.skip) statusBadge = '<div class="gen-node-status skip-icon"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></div>';

        const iconHtml = NODE_ICONS[sec.id] || '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>';
        node.innerHTML = `
            <span class="gen-node-num">${sec.id}</span>
            <span class="gen-node-icon">${iconHtml}</span>
            ${statusBadge}
        `;

        // Label position: outside the circle
        const labelAngleDeg = (i / total) * 360 - 90;
        const label = document.createElement('div');
        label.className = 'gen-node-label';
        label.textContent = sec.short;

        // Position label based on which side of the circle
        const labelDist = 50;
        if (labelAngleDeg > -45 && labelAngleDeg < 45) { label.style.cssText = `top:-20px;left:50%;transform:translateX(-50%);`; }
        else if (labelAngleDeg >= 45 && labelAngleDeg < 135) { label.style.cssText = `right:-8px;top:50%;transform:translate(100%,-50%);`; }
        else if (labelAngleDeg >= 135 || labelAngleDeg < -135) { label.style.cssText = `bottom:-20px;left:50%;transform:translateX(-50%);`; }
        else { label.style.cssText = `left:-8px;top:50%;transform:translate(-100%,-50%);`; }

        node.appendChild(label);
        node.addEventListener('click', () => selectSection(sec.id));
        container.appendChild(node);
    });
}

// ===== Select Section / Open Panel =====
function selectSection(id) {
    activeSection = id;
    window.activeSection = id;
    renderNodes();
    openPanel(id);
}

function syncPanelKeyDisplay(state) {
    const genSelect = document.getElementById('genSavedKeySelect');
    const genApiKeyEl = document.getElementById('genApiKey');
    const genProviderEl = document.getElementById('genProvider');

    if (state.provider && genProviderEl) {
        genProviderEl.value = state.provider;
    }

    if (state.apiKey && typeof state.apiKey === 'string' && state.apiKey.startsWith('saved_')) {
        if (genSelect) genSelect.value = state.apiKey;
        const idx = parseInt(state.apiKey.replace('saved_', ''), 10);
        if (typeof savedApiKeys !== 'undefined' && savedApiKeys[idx] && genApiKeyEl) {
            genApiKeyEl.value = savedApiKeys[idx].key;
        } else if (genApiKeyEl) {
            genApiKeyEl.value = state.apiKey;
        }
    } else {
        if (genSelect) genSelect.value = '';
        if (genApiKeyEl) genApiKeyEl.value = state.apiKey || '';
    }
}

function openPanel(id) {
    const panel = document.getElementById('genPanel');
    const sec = SECTIONS.find(s => s.id === id);
    const state = sectionStates[id];
    if (!sec || !state) return;

    document.getElementById('genPanelTitle').textContent = `${sec.id}. ${sec.name}`;
    document.getElementById('genPanelSubtitle').textContent = sec.desc;

    // Provider, API Key, and Saved Select display synchronization
    syncPanelKeyDisplay(state);
    // Strategy
    const genStrategyEl = document.getElementById('genStrategy');
    if (genStrategyEl) genStrategyEl.value = state.strategy || '1_pass';
    // Detail Level
    setDetailLevel(state.detailLevel, false);
    // Toggles
    setToggle('genSkipToggle', state.skip);
    setToggle('genPlaceholderToggle', state.placeholder);

    // Custom Instructions
    document.getElementById('genCustomInstructions').value = state.customInstructions;
    // Lock button
    const lockBtn = document.getElementById('genLockBtn');
    lockBtn.classList.toggle('locked', state.locked);
    lockBtn.innerHTML = state.locked
        ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg> Unlock'
        : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg> Lock';

    const customActions = document.getElementById('genCustomActions');
    const pasteArea = document.getElementById('genPasteArea');
    if (customActions) customActions.style.display = (id >= 100) ? 'flex' : 'none';
    if (pasteArea) pasteArea.style.display = 'none';

    panel.classList.add('open');
}

function closePanel() {
    document.getElementById('genPanel').classList.remove('open');
    activeSection = null;
    window.activeSection = null;
    renderNodes();
}

// ===== Panel Control Helpers =====
function setDetailLevel(level, save) {
    const positions = [0, 50, 100];
    document.getElementById('genSliderFill').style.width = positions[level] + '%';
    document.getElementById('genSliderThumb').style.left = positions[level] + '%';
    document.querySelectorAll('.gen-slider-labels span').forEach((el, i) => {
        el.classList.toggle('active', i === level);
    });
    if (save !== false && activeSection) {
        sectionStates[activeSection].detailLevel = level;
    }
}

function setToggle(id, val) {
    const el = document.getElementById(id);
    el.classList.toggle('on', val);
}

function toggleSwitch(id, stateKey) {
    if (!activeSection) return;
    const state = sectionStates[activeSection];
    state[stateKey] = !state[stateKey];
    setToggle(id, state[stateKey]);
    renderNodes();
}

function updateProgressRing() {
    const completed = Object.values(sectionStates).filter(s => s.status === 'completed').length;
    const total = SECTIONS.length;
    const pct = total > 0 ? completed / total : 0;
    const circumference = 2 * Math.PI * 86;
    const offset = circumference * (1 - pct);
    const ring = document.getElementById('genRingFill');
    if (ring) {
        ring.style.strokeDasharray = circumference;
        ring.style.strokeDashoffset = offset;
    }
    const label = document.getElementById('genHubProgress');
    if (label) label.textContent = `${completed} / ${total} sections`;
}

// ===== Event Bindings (called after DOM ready) =====
function initGeneratorEvents() {
    // Close panel
    const genPanelClose = document.getElementById('genPanelClose');
    if (genPanelClose) genPanelClose.addEventListener('click', closePanel);

    // Provider change (per-section override)
    document.getElementById('genProvider').addEventListener('change', e => {
        if (activeSection) {
            sectionStates[activeSection].provider = e.target.value;
            // Mark this section as having a per-section override
            sectionKeyOverrides.add(activeSection);
        }
    });

    // Strategy change
    const genStrategyEl = document.getElementById('genStrategy');
    if (genStrategyEl) {
        genStrategyEl.addEventListener('change', e => {
            if (activeSection) sectionStates[activeSection].strategy = e.target.value;
        });
    }

    // Common Strategy change
    const commonStrategyEl = document.getElementById('commonStrategy');
    if (commonStrategyEl) {
        commonStrategyEl.addEventListener('change', e => {
            const strat = e.target.value;
            Object.values(sectionStates).forEach(s => s.strategy = strat);
            if (activeSection && document.getElementById('genStrategy')) {
                document.getElementById('genStrategy').value = strat;
            }
        });
    }

    // API Key change (per-section override)
    document.getElementById('genApiKey').addEventListener('input', e => {
        if (activeSection) {
            sectionStates[activeSection].apiKey = e.target.value;
            const commonInput = document.getElementById('commonApiKey');
            if (commonInput && e.target.value === commonInput.value) {
                sectionKeyOverrides.delete(activeSection);
            } else {
                sectionKeyOverrides.add(activeSection);
            }
        }
    });

    // Detail Level clicks
    document.querySelectorAll('.gen-slider-labels span').forEach((el, i) => {
        el.addEventListener('click', () => setDetailLevel(i, true));
    });
    // Slider track click
    document.getElementById('genSliderTrack').addEventListener('click', e => {
        const rect = e.currentTarget.getBoundingClientRect();
        const pct = (e.clientX - rect.left) / rect.width;
        const level = pct < 0.33 ? 0 : pct < 0.66 ? 1 : 2;
        setDetailLevel(level, true);
    });

    // Toggles
    document.getElementById('genSkipToggle').addEventListener('click', () => toggleSwitch('genSkipToggle', 'skip'));
    document.getElementById('genPlaceholderToggle').addEventListener('click', () => toggleSwitch('genPlaceholderToggle', 'placeholder'));



    // Custom instructions
    document.getElementById('genCustomInstructions').addEventListener('input', e => {
        if (activeSection) sectionStates[activeSection].customInstructions = e.target.value;
    });

    // Lock button
    document.getElementById('genLockBtn').addEventListener('click', () => {
        if (!activeSection) return;
        sectionStates[activeSection].locked = !sectionStates[activeSection].locked;
        openPanel(activeSection);
        renderNodes();
    });

    async function executeGeneration(secId) {
        const state = sectionStates[secId];
        if (state.locked || state.skip || state.placeholder) return;

        const projectName = document.getElementById('genHubProject').textContent;
        if (!projectName || projectName === 'Project') {
            showToast('No project selected.', 'warning');
            throw new Error('No project selected.');
        }

        if (!state.provider || !state.apiKey) {
            showToast(`Please provide an API key and select a provider for Section ${secId}.`, 'warning');
            throw new Error('Missing API key or provider.');
        }

        state.status = 'generating';
        renderNodes();
        updateProgressRing();

        logToTerminal(`Starting extraction for Section ${secId}`);
        if (secId !== 6) {
            logToTerminal(`Strategy: ${state.strategy || '1_pass'}`);
        }
        logToTerminal(`Connecting to ${state.provider} via LLM Gateway...`);

        try {
            if (secId === 6) {
                // --- SECTION 6: CHUNKED PER-FRAMEWORK GENERATION ---
                logToTerminal(`Phase 0: Discovering frameworks...`);

                const discRes = await fetch(`/api/project/${projectName}/generate_s6`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: state.provider,
                        api_key: state.apiKey,
                        phase: 'discovery',
                        detail_level: state.detailLevel,
                        custom_instructions: state.customInstructions
                    })
                });

                const discData = await discRes.json();
                if (!discRes.ok) throw new Error(discData.error || 'Failed during discovery');

                const frameworks = discData.frameworks || [];
                const completed = discData.completed || [];

                logToTerminal(`Discovered ${frameworks.length} frameworks to analyze.`);
                if (completed.length > 0) {
                    logToTerminal(`Already completed: ${completed.join(', ')}`);
                }

                for (let i = 0; i < frameworks.length; i++) {
                    const fw = frameworks[i];
                    if (completed.includes(fw.name)) continue;

                    logToTerminal(`Phase 1: Generating deep dive for ${fw.name} (${i + 1}/${frameworks.length})...`);

                    const diveRes = await fetch(`/api/project/${projectName}/generate_s6`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            provider: state.provider,
                            api_key: state.apiKey,
                            phase: 'deep_dive',
                            framework_index: i,
                            detail_level: state.detailLevel,
                            custom_instructions: state.customInstructions
                        })
                    });

                    const diveData = await diveRes.json();
                    if (!diveRes.ok) {
                        logToTerminal(`Generation paused or failed at ${fw.name}.`);
                        throw new Error(diveData.error || `Failed on framework ${fw.name}`);
                    }

                    if (diveData.skipped) {
                        logToTerminal(`[Skipped] ${fw.name} already completed.`);
                    } else {
                        logToTerminal(`[Saved] Deep dive for ${fw.name} completed.`);
                    }
                }

                logToTerminal(`Success! All frameworks for Section 6 analyzed and saved.`);
                state.status = 'completed';

            } else if (secId >= 100) {
                // --- CUSTOM SECTION GENERATION ---
                const secObj = SECTIONS.find(s => s.id === secId);
                const res = await fetch(`/api/project/${projectName}/generate_custom`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        section_id: secId,
                        section_title: secObj ? secObj.name : `Custom ${secId}`,
                        section_description: secObj ? secObj.desc : '',
                        provider: state.provider,
                        api_key: state.apiKey,
                        strategy: state.strategy || '1_pass',
                        detail_level: state.detailLevel,
                        custom_instructions: state.customInstructions
                    })
                });
                logToTerminal(`Received response from backend for custom section.`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to generate custom section');
                logToTerminal(`Success! Custom Section "${data.section_title}" saved to project DB.`);
                state.status = 'completed';
            } else {
                // --- STANDARD GENERATION FOR OTHER SECTIONS ---
                const res = await fetch(`/api/project/${projectName}/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        section_id: secId,
                        provider: state.provider,
                        api_key: state.apiKey,
                        strategy: state.strategy || '1_pass',
                        detail_level: state.detailLevel,
                        custom_instructions: state.customInstructions
                    })
                });

                logToTerminal(`Received response from backend.`);
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed to generate');

                if (data.passes && Array.isArray(data.passes)) {
                    data.passes.forEach(p => {
                        logToTerminal(`  Pass ${p.pass}: ${p.info}`);
                        if (p.requested_files && p.requested_files.length > 0) {
                            logToTerminal(`  Requested files: ${p.requested_files.join(', ')}`);
                        }
                        if (p.reasoning) {
                            logToTerminal(`  Reasoning: ${p.reasoning}`);
                        }
                    });
                }

                logToTerminal(`Success! Section ${secId} saved to project DB.`);
                state.status = 'completed';
            }
        } catch (err) {
            console.error(err);
            logToTerminal(`ERROR: ${err.message}`);
            state.status = 'idle';
            renderNodes();
            updateProgressRing();
            throw err;
        }

        renderNodes();
        updateProgressRing();
        if (activeSection === secId) openPanel(secId);
    }

    // Regenerate button
    const genRegenerateBtn = document.getElementById('genRegenerateBtn');
    if (genRegenerateBtn) {
        genRegenerateBtn.addEventListener('click', async () => {
            if (!activeSection) return;
            const btn = genRegenerateBtn;
            btn.disabled = true;
            try { await executeGeneration(activeSection); }
            catch (e) { /* error already logged */ }
            finally { btn.disabled = false; }
        });
    }

    // Generate All
    const genAllBtn = document.getElementById('genAllBtnLeft') || document.getElementById('genHubBtn');
    if (genAllBtn) {
        genAllBtn.addEventListener('click', async () => {
            if (!confirm('Warning: This will sequentially regenerate all unlocked sections. Continue?')) return;
            const btn = genAllBtn;
            btn.disabled = true;
            try {
                for (const sec of SECTIONS) {
                    const state = sectionStates[sec.id];
                    if (!state.locked && !state.skip && !state.placeholder) {
                        await executeGeneration(sec.id);
                    }
                }
                logToTerminal('Generate All completed successfully.');
            } catch (e) {
                logToTerminal('Generate All aborted due to an error.');
            } finally {
                btn.disabled = false;
            }
        });
    }

    // Generate This Section Only
    const genSectionBtn = document.getElementById('genGenerateSectionBtn');
    if (genSectionBtn) {
        genSectionBtn.addEventListener('click', async () => {
            if (!activeSection) return;
            const btn = genSectionBtn;
            btn.disabled = true;
            try { await executeGeneration(activeSection); }
            catch (e) { /* error already logged */ }
            finally { btn.disabled = false; }
        });
    }
}

// Init when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGeneratorEvents);
} else {
    initGeneratorEvents();
}

// ===== API Keys Logic =====
let savedApiKeys = [];

async function loadApiKeys() {
    try {
        const res = await fetch('/api/config/llm_keys');
        if (res.ok) {
            savedApiKeys = await res.json();
            renderApiKeys();
            updateKeyDropdowns();
        }
    } catch (e) {
        console.error('Failed to load API keys:', e);
    }
}

async function addApiKey(name, provider, key) {
    try {
        const res = await fetch('/api/config/llm_keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, provider, key })
        });
        if (res.ok) {
            await loadApiKeys();
        } else {
            showToast('Failed to save API key', 'error');
        }
    } catch (e) {
        showToast('Error saving API key', 'error');
    }
}

function renderApiKeys() {
    const list = document.getElementById('savedKeysList');
    if (!list) return;
    if (savedApiKeys.length === 0) {
        list.innerHTML = '<div style="font-size: 13px; color: var(--text-dim); padding: 8px;">No saved keys.</div>';
        return;
    }
    list.innerHTML = savedApiKeys.map((k, i) => `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: rgba(255,255,255,0.03); border: 1px solid var(--dark-border2); border-radius: var(--radius-sm);">
            <div style="display: flex; flex-direction: column; gap: 2px;">
                <span style="font-size: 13px; font-weight: 600; color: #fff;">${escapeHtml(k.name)}</span>
                <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">${escapeHtml(k.provider)}</span>
            </div>
            <button class="project-delete-btn" title="Delete Key" onclick="deleteApiKey(${i})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
        </div>
    `).join('');
}

window.deleteApiKey = async function (index) {
    try {
        const res = await fetch(`/api/config/llm_keys/${index}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            await loadApiKeys();
        } else {
            showToast('Failed to delete API key', 'error');
        }
    } catch (e) {
        showToast('Error deleting API key', 'error');
    }
};

function updateKeyDropdowns() {
    const commonSelect = document.getElementById('commonSavedKeySelect');
    const genSelect = document.getElementById('genSavedKeySelect');

    const optionsHTML = '<option value="">-- Select Saved Key --</option>' +
        savedApiKeys.map((k, i) => `<option value="saved_${i}">${escapeHtml(k.name)} (${escapeHtml(k.provider)})</option>`).join('');

    if (commonSelect) {
        commonSelect.innerHTML = optionsHTML;
        if (currentCommonApiKey) commonSelect.value = currentCommonApiKey;
    }
    if (genSelect) {
        genSelect.innerHTML = optionsHTML;
        if (activeSection && sectionStates[activeSection]) {
            syncPanelKeyDisplay(sectionStates[activeSection]);
        }
    }
}

function initApiKeysEvents() {
    const addBtn = document.getElementById('addSavedKeyBtn');
    if (addBtn) {
        addBtn.addEventListener('click', async () => {
            const name = document.getElementById('newKeyName').value.trim();
            const provider = document.getElementById('newKeyProvider').value;
            const key = document.getElementById('newKeyValue').value.trim();
            if (!name || !key) {
                showToast('Please provide a name and API key.', 'warning'); return;
            }
            addBtn.disabled = true;
            await addApiKey(name, provider, key);
            document.getElementById('newKeyName').value = '';
            document.getElementById('newKeyValue').value = '';
            addBtn.disabled = false;
        });
    }

    const commonSelect = document.getElementById('commonSavedKeySelect');
    if (commonSelect) {
        commonSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            if (val.startsWith("saved_")) {
                const idx = parseInt(val.replace("saved_", ""));
                const k = savedApiKeys[idx];
                // Show masked key for display, but store saved_N reference for API calls
                document.getElementById('commonApiKey').value = k.key;

                // Update tracked common key
                currentCommonApiKey = val;
                currentCommonProvider = k.provider;

                // Sync to sections that DON'T have a per-section override
                SECTIONS.forEach(sec => {
                    if (!sectionKeyOverrides.has(sec.id)) {
                        sectionStates[sec.id].apiKey = val;
                        sectionStates[sec.id].provider = k.provider;
                    }
                });
                // Update the per-section panel display only if the active section is NOT overridden
                if (activeSection && !sectionKeyOverrides.has(activeSection)) {
                    syncPanelKeyDisplay(sectionStates[activeSection]);
                }
            }
        });
    }

    const commonKeyInput = document.getElementById('commonApiKey');
    if (commonKeyInput) {
        commonKeyInput.addEventListener('input', (e) => {
            const val = e.target.value;
            // Update tracked common key
            currentCommonApiKey = val;

            // Only sync to sections that DON'T have a per-section override
            SECTIONS.forEach(sec => {
                if (!sectionKeyOverrides.has(sec.id)) {
                    sectionStates[sec.id].apiKey = val;
                }
            });
            if (activeSection && !sectionKeyOverrides.has(activeSection)) {
                syncPanelKeyDisplay(sectionStates[activeSection]);
            }
        });
    }

    const genSelect = document.getElementById('genSavedKeySelect');
    if (genSelect) {
        genSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            if (val.startsWith("saved_")) {
                const idx = parseInt(val.replace("saved_", ""));
                const k = savedApiKeys[idx];
                // Show masked key for display, but store saved_N reference for API calls
                document.getElementById('genApiKey').value = k.key;
                document.getElementById('genProvider').value = k.provider;
                if (activeSection) {
                    sectionStates[activeSection].apiKey = val;
                    sectionStates[activeSection].provider = k.provider;
                    if (val === currentCommonApiKey) {
                        sectionKeyOverrides.delete(activeSection);
                    } else {
                        sectionKeyOverrides.add(activeSection);
                    }
                }
            } else {
                if (activeSection) {
                    sectionStates[activeSection].apiKey = '';
                    document.getElementById('genApiKey').value = '';
                }
            }
        });
    }
    loadApiKeys();
}

function escapeHtml(str) { if (!str) return ''; const d = document.createElement('div'); d.textContent = String(str); return d.innerHTML; }

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApiKeysEvents);
} else {
    initApiKeysEvents();
}

window.logToTerminal = function (msg) {
    const term = document.getElementById('genTerminal');
    const content = document.getElementById('genTerminalContent');
    if (term && content) {
        term.style.display = 'flex';
        const line = document.createElement('div');
        line.className = 'gen-terminal-line';
        const now = new Date();
        const timeStr = now.getHours().toString().padStart(2, '0') + ':' +
            now.getMinutes().toString().padStart(2, '0') + ':' +
            now.getSeconds().toString().padStart(2, '0');
        line.innerHTML = `<span class="gen-terminal-time">[${timeStr}]</span> ${escapeHtml(msg)}`;
        content.appendChild(line);
        content.scrollTop = content.scrollHeight;
    }
};

window.syncGeneratedStatus = function (completedIds) {
    SECTIONS.forEach(sec => {
        if (completedIds.includes(sec.id)) {
            sectionStates[sec.id].status = 'completed';
        } else {
            sectionStates[sec.id].status = 'idle';
        }
    });
    renderNodes();
    updateProgressRing();
};

// ===== Draggable Terminal =====
(function initDraggableTerminal() {
    function setup() {
        const terminal = document.getElementById('genTerminal');
        const header = document.getElementById('genTerminalHeader');
        const clearBtn = document.getElementById('genTerminalClear');
        const closeBtn = document.getElementById('genTerminalCloseBtn');
        if (!terminal || !header) return;

        let isDragging = false;
        let offsetX = 0, offsetY = 0;

        header.addEventListener('mousedown', (e) => {
            // Don't drag if clicking a button inside the header
            if (e.target.closest('button')) return;
            isDragging = true;
            const rect = terminal.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            // Switch from bottom/right to top/left positioning
            terminal.style.left = rect.left + 'px';
            terminal.style.top = rect.top + 'px';
            terminal.style.right = 'auto';
            terminal.style.bottom = 'auto';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            let newX = e.clientX - offsetX;
            let newY = e.clientY - offsetY;
            // Clamp to viewport
            const w = terminal.offsetWidth;
            const h = terminal.offsetHeight;
            newX = Math.max(0, Math.min(newX, window.innerWidth - w));
            newY = Math.max(0, Math.min(newY, window.innerHeight - h));
            terminal.style.left = newX + 'px';
            terminal.style.top = newY + 'px';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
        });

        // Clear button
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                const content = document.getElementById('genTerminalContent');
                if (content) content.innerHTML = '';
            });
        }

        // Close button
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                terminal.style.display = 'none';
                // Reset position to default bottom-right
                terminal.style.left = '';
                terminal.style.top = '';
                terminal.style.right = '20px';
                terminal.style.bottom = '20px';
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
