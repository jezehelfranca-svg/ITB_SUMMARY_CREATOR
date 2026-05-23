// ITB Telecom Wiki Application Logic

let activeTab = 'wiki';
let db = null; // Requirements database
let serverOnline = false;
let currentWorkflowStep = 1;
let tqList = []; // TQ items
let projectList = []; // Loaded projects catalog list
let currentProjectId = 'project_co2_urea'; // Active project ID
let projectTqs = {}; // Map to store active TQs for each project ID
let activeCategory = 'ALL';

// Default Initial TQs based on ITB Project PDF Conflicts
const DEFAULT_TQS = [
    {
        id: 1,
        subsystem: "CCTV",
        docRef: "Part_A Page 43 / Part_B2 Page 243",
        clause: "Clause 3.1.2 / Storage Ref",
        description: "Specification requires minimum 2 months (60 days) NVR storage in Part-A page 43, whereas Part-B clauses suggest 30 or 90 days. Please clarify the required video retention duration.",
        proposal: "Bidder proposes to design and size NVR storage for 90 days continuous recording at 1080p, 15fps, H.265 compression for all cameras to comply with the highest standard."
    },
    {
        id: 2,
        subsystem: "UPS",
        docRef: "Part_A Page 37 / Part_B2 Page 234",
        clause: "Clause 5.5 / UPS Power",
        description: "UPS battery backup duration is conflicting: Part-A page 37 specifies 3 hours backup for Carbon Capture plant (Site Alpha), whereas page 42 specifies 2 hours backup for Site Beta C&I systems. Please clarify the required backup time for each site.",
        proposal: "Bidder proposes to size the Ni-Cd battery bank for 3 hours backup duration for Site Alpha and 2 hours for Site Beta as specified."
    },
    {
        id: 3,
        subsystem: "DCS",
        docRef: "Part_A Page 40",
        clause: "Clause 4.10 (Corrosive Protection)",
        description: "All electronic modules and PCBs must have conformal coating for coastal corrosion protection. Please clarify if this is mandatory for all OEM packages (e.g., compressor PLC, Water Treatment PLC) or only the main plant DCS.",
        proposal: "Bidder proposes that all electronic cards in the main DCS and critical package PLCs located in the plant areas will be supplied with conformal coating class G3 as per ISA-S71.04."
    },
    {
        id: 4,
        subsystem: "CCTV",
        docRef: "Part_B2 Page 243",
        clause: "Scope of Quantities",
        description: "The specification states CCTV camera counts and PAGA locations shall be finalized during engineering at no extra cost, presenting major bidding risk. Please confirm bid pricing is based on a fixed minimum of 20 cameras.",
        proposal: "Bidder proposes that the bid price is based on a fixed scope of 20 CCTV cameras. Any additional cameras required during detailed engineering will be subject to a change order."
    },
    {
        id: 5,
        subsystem: "Network",
        docRef: "Part_A Page 39 / Part_B2 Page 243",
        clause: "Cybersecurity Clause",
        description: "Cybersecurity compliance is mandated (STQC, IEC 62443), but boundary interface firewall scope between Telecom LAN and the control room DCS Network is undefined.",
        proposal: "Bidder proposes to provide a managed Level-3 firewall at the Telecom-DCS network demarcation boundary to block unauthorized traffic and comply with segregation rules."
    }
];

// Initialize TQ list
tqList = [...DEFAULT_TQS];
projectTqs['project_co2_urea'] = [...DEFAULT_TQS];

// Subsystem definitions with FontAwesome Icons and categories
const SUBSYSTEM_META = {
    "DCS": { icon: "fa-server", desc: "Distributed Control System", category: "C&I" },
    "ESD": { icon: "fa-shield-halved", desc: "Emergency Shutdown System", category: "C&I" },
    "HMIPIS": { icon: "fa-desktop", desc: "HMI & Plant Information System", category: "C&I" },
    "FieldInstruments": { icon: "fa-gauge-high", desc: "Field Instruments & Transmitters", category: "C&I" },
    "Analysers": { icon: "fa-flask-vial", desc: "Online Analysers & SWAS", category: "C&I" },
    "MMS": { icon: "fa-chart-line", desc: "Machine Vibration Monitoring", category: "C&I" },
    "FGS": { icon: "fa-fire-extinguisher", desc: "Fire & Gas Integration", category: "C&I" },
    "CCTV": { icon: "fa-video", desc: "CCTV Surveillance System", category: "Telecom" },
    "PAGA": { icon: "fa-bullhorn", desc: "Public Address & Alarm System", category: "Telecom" },
    "Telephony": { icon: "fa-phone-flip", desc: "Plant Telephone & Intercom", category: "Telecom" },
    "Network": { icon: "fa-network-wired", desc: "Industrial Net & Cybersecurity", category: "Telecom" },
    "Cabling": { icon: "fa-circle-nodes", desc: "Structured Cabling & FOC", category: "Telecom" },
    "UPS": { icon: "fa-battery-full", desc: "UPS & DC Power Systems", category: "Telecom" }
};

// Document Indexed files list
const INDEXED_FILES = [
    "Part_A_Technical_Specification_150_TPD_CO2_To_Urea.pdf",
    "Part_B1_Technical_Specification_CO2_Urea_1_500.pdf",
    "Part_B2_Technical_Specification_CO2-Urea_501_1000.pdf",
    "Part_B3_Technical_Specification_CO2_Urea_1001_2000.pdf",
    "Part_B4_Technical_Specification_CO2_Urea_2001_3000.pdf",
    "Part_B5_Technical_Specification_CO2_Urea_3001_3500.pdf",
    "Part_B6_Technical_Specification_CO2_Urea_3501_4000.pdf",
    "Part_B7_Technical_Specification_CO2_Urea_4001_5000.pdf",
    "Part_B8_Technical_Specification_CO2_Urea_5001_6000.pdf",
    "Part_B9_Technical_Specification_CO2_Urea_6001_6800.pdf",
    "Part_B10_Technical_Specification_CO2_Urea_6801_7525.pdf"
];

// DOMContentLoaded Entry
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// App Initialization
async function initApp() {
    setupTabNavigation();
    setupCategoryTabs();
    setupChallenges();
    setupTQForm();
    setupProjectSelector();
    await checkBackendConnection();
    await loadProjectCatalog();
    await loadProjectData(currentProjectId);
    renderTQs();
    renderIndexedFiles();
    setupHiFiExtractor();
}

// Category Tabs Switcher
function setupCategoryTabs() {
    const tabs = document.querySelectorAll('.category-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeCategory = tab.getAttribute('data-category');
            renderWiki();
        });
    });
}

// 1. Connection Check
async function checkBackendConnection() {
    try {
        const response = await fetch('/api/projects');
        if (response.ok) {
            serverOnline = true;
        } else {
            throw new Error("Backend offline");
        }
    } catch (e) {
        serverOnline = false;
    }
}

// Project Selector Setup
function setupProjectSelector() {
    const selector = document.getElementById('projectSelector');
    if (!selector) return;
    
    selector.addEventListener('change', async (e) => {
        if (currentProjectId) {
            projectTqs[currentProjectId] = [...tqList];
        }
        currentProjectId = e.target.value;
        await loadProjectData(currentProjectId);
    });
}

// Load catalog of projects
async function loadProjectCatalog() {
    const selector = document.getElementById('projectSelector');
    if (!selector) return;
    
    if (serverOnline) {
        try {
            const response = await fetch('/api/projects');
            if (response.ok) {
                projectList = await response.json();
            } else {
                throw new Error("Catalog fetch failed");
            }
        } catch (e) {
            console.warn("Catalog fetch failed, falling back offline.", e);
            projectList = typeof PROJECTS_CATALOG !== 'undefined' ? PROJECTS_CATALOG : [
                { id: 'project_co2_urea', name: "CO2 to Urea Demonstration Plant Project" },
                { id: 'project_urea', name: "Urea Synthesis Plant (Scanned)" }
            ];
        }
    } else {
        projectList = typeof PROJECTS_CATALOG !== 'undefined' ? PROJECTS_CATALOG : [
            { id: 'project_co2_urea', name: "CO2 to Urea Demonstration Plant Project" },
            { id: 'project_urea', name: "Urea Synthesis Plant (Scanned)" }
        ];
    }
    
    selector.innerHTML = '';
    projectList.forEach(proj => {
        const opt = document.createElement('option');
        opt.value = proj.id;
        opt.innerText = proj.name;
        if (proj.id === currentProjectId) {
            opt.selected = true;
        }
        selector.appendChild(opt);
    });
}

// Load specifications data for a project
async function loadProjectData(projectId) {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    
    if (serverOnline) {
        try {
            const response = await fetch(`/api/requirements/${projectId}`);
            if (response.ok) {
                db = await response.json();
                dot.className = 'status-dot online';
                text.innerText = 'Online (Backend API)';
                console.log(`Loaded project data for ${projectId} from Flask server.`);
            } else {
                throw new Error("Requirements fetch failed");
            }
        } catch (e) {
            console.warn("Requirements fetch failed, falling back offline.", e);
            await loadOfflineProjectData(projectId);
        }
    } else {
        await loadOfflineProjectData(projectId);
    }
    
    // Load project-specific TQs: check cache first, then active database, then fallback
    if (projectTqs[projectId]) {
        tqList = [...projectTqs[projectId]];
    } else if (db && db.tqs && db.tqs.length > 0) {
        tqList = [...db.tqs];
    } else if (projectId === 'project_co2_urea') {
        tqList = [...DEFAULT_TQS];
    } else {
        tqList = [];
    }
    
    updateHeader();
    renderWiki();
    renderTQs();
    setupChallenges();
}

// Load offline fallback data
function loadOfflineProjectData(projectId) {
    return new Promise((resolve) => {
        const dot = document.getElementById('statusDot');
        const text = document.getElementById('statusText');
        
        dot.className = 'status-dot';
        text.innerText = 'Offline Mode (Static DB)';
        
        const oldScript = document.getElementById('dynamicProjectData');
        if (oldScript) oldScript.remove();
        
        if (projectId === 'project_co2_urea') {
            db = REQUIREMENTS_DATA;
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.id = 'dynamicProjectData';
        script.src = `data_${projectId}.js`;
        script.onload = () => {
            const varName = `REQUIREMENTS_DATA_${projectId.toUpperCase()}`;
            if (window[varName]) {
                db = window[varName];
                console.log(`Loaded offline database variable ${varName}`);
            } else if (window.REQUIREMENTS_DATA) {
                db = window.REQUIREMENTS_DATA;
            }
            resolve();
        };
        script.onerror = () => {
            console.error(`Failed to load data_${projectId}.js. Falling back to default.`);
            db = REQUIREMENTS_DATA;
            resolve();
        };
        document.body.appendChild(script);
    });
}

// 2. Tab Navigation
function setupTabNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const panels = document.querySelectorAll('.tab-panel');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            
            // Remove active classes
            navItems.forEach(n => n.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked
            item.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');
            
            activeTab = tabId;
            updateHeader();
        });
    });
}

function updateHeader() {
    const title = document.getElementById('pageTitle');
    const subtitle = document.getElementById('pageSubtitle');
    const actions = document.getElementById('headerActions');
    
    actions.innerHTML = ''; // Clear header actions
    
    if (activeTab === 'wiki') {
        title.innerText = 'Wiki Dashboard';
        const projName = db ? db.project : 'selected project';
        subtitle.innerText = `Explore the structured Telecom and Security requirements for ${projName}.`;
        actions.innerHTML = `
            <button class="btn-secondary" onclick="loadProjectCatalog().then(() => loadProjectData(currentProjectId))"><i class="fa-solid fa-arrows-rotate"></i> Refresh Data</button>
        `;
    } else if (activeTab === 'workflow') {
        title.innerText = 'Reviewer Workflow';
        subtitle.innerText = 'Run the ITB Reviewer Workflow Agent step-by-step to scan, audit, and output clarifications.';
        actions.innerHTML = `
            <button class="btn-secondary" onclick="resetWorkflow()"><i class="fa-solid fa-rotate-left"></i> Reset Wizard</button>
        `;
    } else if (activeTab === 'challenges') {
        title.innerText = 'Agent Challenges';
        subtitle.innerText = 'Understand the layout, scope, and semantic challenges faced by AI Reviewer agents in project bids.';
    } else if (activeTab === 'tq') {
        title.innerText = 'Technical Query (TQ) Sheet';
        subtitle.innerText = 'Manage bidder clarification queries to resolve document ambiguities, ready for export.';
    } else if (activeTab === 'extractor') {
        title.innerText = 'HiFi Extractor Console';
        subtitle.innerText = 'Execute the tiered high-fidelity extraction pipeline locally on your PDF specification sheets.';
        loadAvailablePDFs();
    }
}

// 3. Wiki Dashboard Render
let activeSubsystem = "DCS";

function renderWiki() {
    const grid = document.getElementById('subsystemGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    // Filter system keys by active category
    let sysKeys = Object.keys(db.systems);
    if (activeCategory !== 'ALL') {
        sysKeys = sysKeys.filter(sysKey => {
            const sys = db.systems[sysKey];
            const meta = SUBSYSTEM_META[sysKey];
            const cat = (sys && sys.category) || (meta && meta.category);
            // Handle Telecom / Telecom & Security name differences
            if (activeCategory === 'Telecom') {
                return cat === 'Telecom' || cat === 'Telecom & Security';
            }
            return cat === activeCategory;
        });
    }
    
    // If current active subsystem is not in the filtered list, switch to first visible
    if (sysKeys.length > 0 && !sysKeys.includes(activeSubsystem)) {
        activeSubsystem = sysKeys[0];
    }
    
    sysKeys.forEach(sysKey => {
        const sys = db.systems[sysKey];
        const meta = SUBSYSTEM_META[sysKey] || { icon: "fa-circle", desc: "System specifications" };
        const ruleCount = sys.rules.length;
        
        const card = document.createElement('div');
        card.className = `subsystem-card ${sysKey === activeSubsystem ? 'active' : ''}`;
        card.setAttribute('data-sys', sysKey);
        card.innerHTML = `
            <div class="subsystem-header">
                <i class="fa-solid ${meta.icon} subsystem-icon"></i>
                <span class="tag-badge" style="font-size: 0.65rem;">${ruleCount} clauses</span>
            </div>
            <h3>${sys.name}</h3>
            <p>${sys.spec_no}</p>
        `;
        
        card.addEventListener('click', () => {
            document.querySelectorAll('.subsystem-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            activeSubsystem = sysKey;
            renderSubsystemDetails();
        });
        
        grid.appendChild(card);
    });
    
    renderSubsystemDetails();
}

function renderSubsystemDetails() {
    const sys = db.systems[activeSubsystem];
    const highlightList = document.getElementById('highlightList');
    const clauseList = document.getElementById('clauseList');
    
    if (!highlightList || !clauseList) return;
    
    // Render highlights
    highlightList.innerHTML = '';
    sys.highlights.forEach(hl => {
        const div = document.createElement('div');
        div.className = 'highlight-item';
        div.innerText = hl;
        highlightList.appendChild(div);
    });
    
    // Render clauses
    clauseList.innerHTML = '';
    if (sys.rules.length === 0) {
        clauseList.innerHTML = `
            <div class="clause-card" style="text-align: center; color: var(--text-muted); padding: 3rem 1rem;">
                <i class="fa-solid fa-receipt" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>No specific clauses extracted yet. Run the Reviewer Workflow to populate requirements.</p>
            </div>
        `;
        return;
    }
    
    sys.rules.forEach(rule => {
        const card = document.createElement('div');
        card.className = 'clause-card';
        card.innerHTML = `
            <div class="clause-meta">
                <span style="color: var(--accent-cyan); font-weight: 500;">
                    <i class="fa-solid fa-file-pdf"></i> ${rule.file}
                </span>
                <span class="tag-badge">Page ${rule.page}</span>
            </div>
            <div class="clause-text">"${rule.context}"</div>
            <div style="font-size: 0.75rem; color: var(--text-muted); display: flex; align-items: center; gap: 0.4rem;">
                <i class="fa-solid fa-magnifying-glass"></i> Matched keyword: <b style="color: var(--text-secondary)">${rule.matched}</b>
            </div>
        `;
        clauseList.appendChild(card);
    });
}

// 4. Workflow Wizard Simulation
function renderIndexedFiles() {
    const div = document.getElementById('indexedFilesList');
    if (!div) return;
    div.innerHTML = '';
    INDEXED_FILES.forEach(file => {
        const span = document.createElement('span');
        span.className = 'tag-badge';
        span.style.background = 'rgba(255,255,255,0.03)';
        span.style.border = '1px solid var(--border-color)';
        span.style.color = 'var(--text-secondary)';
        span.innerHTML = `<i class="fa-regular fa-file-pdf"></i> ${file}`;
        div.appendChild(span);
    });
    
    // Set up triggers
    document.getElementById('btnStartScan').onclick = triggerScan;
    document.getElementById('btnProceedToTQ').onclick = () => showWorkflowStep(4);
    document.getElementById('btnModifyTQs').onclick = () => {
        document.querySelector('.nav-item[data-tab="tq"]').click();
    };
    document.getElementById('btnSaveTQToWiki').onclick = triggerSaveWiki;
    document.getElementById('btnGoToWiki').onclick = () => {
        document.querySelector('.nav-item[data-tab="wiki"]').click();
    };
    document.getElementById('btnRestartWorkflow').onclick = resetWorkflow;
}

function showWorkflowStep(step) {
    currentWorkflowStep = step;
    
    // Update step progress bar width
    const progress = document.getElementById('stepProgress');
    const widthPercentage = ((step - 1) / 4) * 100;
    progress.style.width = `${widthPercentage}%`;
    
    // Update step nodes active/completed
    const nodes = document.querySelectorAll('.step-node');
    nodes.forEach(n => {
        const nodeStep = parseInt(n.getAttribute('data-step'));
        n.classList.remove('active', 'completed');
        if (nodeStep < step) {
            n.classList.add('completed');
        } else if (nodeStep === step) {
            n.classList.add('active');
        }
    });
    
    // Update panels visibility
    document.querySelectorAll('.wizard-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`wizard-step-${step}`).classList.add('active');
    
    // Trigger specific step renders
    if (step === 3) {
        renderStep3Conflicts();
    } else if (step === 4) {
        renderStep4TQs();
    }
}

function triggerScan() {
    const projName = document.getElementById('newProjName').value.trim();
    const projDir = document.getElementById('newProjDir').value.trim();
    
    if (!projName || !projDir) {
        alert("Please enter a valid Project Name and local PDF folder path.");
        return;
    }
    
    showWorkflowStep(2);
    
    const consoleBox = document.getElementById('scanConsole');
    const bar = document.getElementById('scanProgressBar');
    const percent = document.getElementById('scanProgressPercent');
    const status = document.getElementById('scanStatusText');
    
    consoleBox.innerHTML = '';
    bar.style.width = '0%';
    percent.innerText = '0%';
    status.innerText = 'Loading PyMuPDF library...';
    
    const logs = [
        { time: 500, msg: "Initializing PDF parsing thread...", pct: 5 },
        { time: 1000, msg: "Index of workspace scanned. Accessing document directory...", pct: 15 },
        { time: 1500, msg: `Scanning PDF documents in directory: '${projDir}'`, pct: 28 },
        { time: 2200, msg: "Loading document text coordinates, mappings, and page counts...", pct: 40 },
        { time: 3000, msg: "Matching Telecom/Security keywords (CCTV, PAGA, Telephone, Cabling, Network)...", pct: 60 },
        { time: 3800, msg: "Mapping Ex-proof tags, certification gaps, and cybersecurity standards...", pct: 75 },
        { time: 4800, msg: "Allocating matches to respective systems (PAGA, Telephone, CCTV, network)...", pct: 90 },
        { time: 5500, msg: "Synchronizing project catalog database index and static javascript variables...", pct: 98 },
        { time: 6000, msg: "Scan completed successfully. Requirements structured.", pct: 100 }
    ];
    
    if (serverOnline) {
        fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: projName, dir: projDir })
        })
        .then(res => res.json())
        .then(data => {
            console.log("Live scan succeeded:", data);
            if (data.project_id) {
                if (currentProjectId) {
                    projectTqs[currentProjectId] = [...tqList];
                }
                currentProjectId = data.project_id;
            }
        })
        .catch(err => {
            console.error("Live scan request failed, running mockup progression.", err);
        });
    }
    
    logs.forEach(log => {
        setTimeout(() => {
            status.innerText = "Extracting Telecom & Security clauses...";
            bar.style.width = `${log.pct}%`;
            percent.innerText = `${log.pct}%`;
            
            const line = document.createElement('div');
            line.innerHTML = `<span style="color: var(--text-muted)">[${new Date().toLocaleTimeString()}]</span> ${log.msg}`;
            consoleBox.appendChild(line);
            consoleBox.scrollTop = consoleBox.scrollHeight;
            
            if (log.pct === 100) {
                setTimeout(async () => {
                    if (serverOnline) {
                        await loadProjectCatalog();
                        await loadProjectData(currentProjectId);
                    } else {
                        const targetId = sanitizeId(projName);
                        if (currentProjectId) {
                            projectTqs[currentProjectId] = [...tqList];
                        }
                        currentProjectId = targetId;
                        await reloadProjectsCatalogScript();
                        await loadProjectCatalog();
                        await loadProjectData(currentProjectId);
                    }
                    showWorkflowStep(3);
                }, 800);
            }
        }, log.time);
    });
}

function renderStep3Conflicts() {
    const list = document.getElementById('conflictList');
    if (!list) return;
    
    list.innerHTML = `
        <div class="conflict-card">
            <div class="conflict-header">
                <span><i class="fa-solid fa-circle-xmark"></i> CCTV Recording Retention Inconsistency</span>
                <span class="tag-badge" style="background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3); color: #f87171;">Critical Contradiction</span>
            </div>
            <div class="conflict-body">
                CCTV specification <b>6-52-0090</b> states that recording capacity should be sized according to datasheets. However, <b>Part B2 Page 243</b> mandates a <b>30 days</b> recording history, whereas <b>Part B3 Page 208</b> explicitly requires <b>90 days</b>. Sizing NVR storage for 90 days instead of 30 days increases hardware costs by 3x.
            </div>
        </div>
        <div class="conflict-card">
            <div class="conflict-header">
                <span><i class="fa-solid fa-circle-exclamation"></i> CCTV Wash Water System Demarcation Gap</span>
                <span class="tag-badge" style="background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.3); color: #fbbf24;">Scope Gap</span>
            </div>
            <div class="conflict-body">
                <b>Part B2 Page 244</b> mandates a permanent service water wash and spray system for camera housings, complete with piping. The utility/piping bidding package contains no reference to run water headers to the camera pedestals, leaving a scope definition gap between EPC and Telecom vendor.
            </div>
        </div>
        <div class="conflict-card">
            <div class="conflict-header">
                <span><i class="fa-solid fa-circle-exclamation"></i> OT Cybersecurity Boundaries Segregation</span>
                <span class="tag-badge" style="background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.3); color: #fbbf24;">Security Boundary Ambiguity</span>
            </div>
            <div class="conflict-body">
                <b>Part B2 Page 239</b> mandates cybersecurity standard compliance with DCS specification <b>6-52-0055</b>. The CCTV spec mandates STQC (MeitY) camera certificates, but has no defined architectural rules or firewall boundaries between the Telecom LAN and the control room DCS Network.
            </div>
        </div>
    `;
}

function renderStep4TQs() {
    const list = document.getElementById('tqProposalList');
    if (!list) return;
    
    list.innerHTML = '';
    
    tqList.forEach(tq => {
        const div = document.createElement('div');
        div.className = 'conflict-card';
        div.style.borderColor = 'rgba(168,85,247,0.25)';
        div.style.background = 'rgba(168,85,247,0.02)';
        div.innerHTML = `
            <div class="conflict-header" style="color: var(--accent-purple)">
                <span><i class="fa-solid fa-pen-to-square"></i> TQ Item #${tq.id}: Clarification on ${tq.subsystem}</span>
                <span class="tag-badge">${tq.docRef} (${tq.clause})</span>
            </div>
            <div class="conflict-body" style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.85rem;">
                <p><b>Ambiguity:</b> ${tq.description}</p>
                <p style="color: #a7f3d0; background: rgba(16,185,129,0.05); padding: 0.5rem; border-radius: 4px; border-left: 3px solid #10b981;">
                    <b>Bidder Proposal:</b> ${tq.proposal}
                </p>
            </div>
        `;
        list.appendChild(div);
    });
}

function triggerSaveWiki() {
    if (serverOnline) {
        loadProjectData(currentProjectId).then(() => {
            showWorkflowStep(5);
        });
    } else {
        showWorkflowStep(5);
    }
}

function resetWorkflow() {
    showWorkflowStep(1);
}

// 5. Challenges Accordion Render
const CHALLENGES_META = [
    {
        id: "pdf_tables",
        title: "Complex PDF Layouts & Nested Tables",
        spec: "Part_B7 Page 330: Analyser Shelter Skid parameters table. Part_B8 Page 739: PAGA speaker coverage DB schedule.",
        desc: "Bidding specifications contain crucial layout tables mapping gas detectors or speaker dB levels. Standard PDF parsers strip out line graphics, leaving a single string where rows are mixed together. This destroys relational context.",
        mitigation: "The ITB Reviewer Agent utilizes fitz (PyMuPDF) vector path trackers and pdfplumber visual grid lines to reconstruct coordinates and cell blocks in physical layout coordinates before applying AI semantic keyword matching."
    },
    {
        id: "scattered",
        title: "Cross-Specification Scope Scattering",
        spec: "Part_B2 Page 287 (Cables specs in Instrument sections), Part_B8 Page 641 (Fire Alarm & Telecom in Electrics spec).",
        desc: "Requirements are rarely grouped nicely. CCTV camera cables are often specified in the Civil sections (conduits), Electrical sections (cables trays), and Instrumentation sections. Reviewing only a 'CCTV' document leads to scoping omissions.",
        mitigation: "A unified global knowledge graph is constructed by parsing all 11 documents. Whenever cabling, power UPS, structural brackets, or grounding is matched, the agent creates relational link boundaries across packages (e.g. mapping CCTV power limits to Analyser Shelter PDB circuits)."
    },
    {
        id: "ambiguous",
        title: "Vague Wording & Verbs Ambiguities",
        spec: "Part_B7 Page 339, Clause 1.1.4(d): 'Any hardware, software and firmware required to meet the purchaser's specified requirements shall be provided...'",
        desc: "Spec verbs like 'shall provide as required' or 'subject to approval' hide significant financial risks. If the owner demands a double-redundant optical link later, the EPC is liable for the cost because they signed a blanket 'provide all' clause.",
        mitigation: "Natural Language Processing (NLP) checks verb modalities. 'Subject to approval' or 'as required' clauses are flagged by the audit engine and automatically compiled into Clarification Queries (TQs) during the bidding phase to freeze the scope."
    },
    {
        id: "cyber",
        title: "OT Cybersecurity & IT Boundaries",
        spec: "Part_B7 Page 147 (DCS Security Operation Center / NIDS network coverage Level-1). Part_B2 Page 243 (CCTV security STQC certification).",
        desc: "Modern bids demand heavy cybersecurity (IEC 62443, local regulatory standards) but lack network interface blueprints. Sizing switches, configuring demilitarized zones (DMZs), and purchasing firewall hardware is often ignored until site integration, leading to scope disputes.",
        mitigation: "The agent checks boundary nodes (e.g. CCTV server interfacing with DCS PLC). If a boundary is found without a defined firewall or switch spec, it highlights a demarcation query (e.g. defining level-3 managed switch scopes)."
    },
    {
        id: "ex_proof",
        title: "Hazardous Area & Regional Ex-Proof Compliance",
        spec: "Part_B7 Page 340, Clause 1.2.2(g): Mandates ATEX/UL Ex-proof tags, plus local Petroleum and Explosives Safety Organization (PESO) approval.",
        desc: "Industrial areas are hazardous (urea dust and ammonia gases). Equipment must carry flameproof Ex d or Ex ia certificates. In India, foreign ATEX certificates are invalid without a local PESO license. Sourcing ATEX cameras that lack PESO certificates leads to project delays and bid disqualification.",
        mitigation: "The agent correlates the Plant Hazardous Area classification drawings with the Telecom BOM. It checks model numbers against database lookup tables of certified local items, flagging non-certified products."
    }
];

function setupChallenges() {
    const container = document.getElementById('challengesList');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Read challenges from loaded project DB or fall back to static CHALLENGES_META
    const challenges = (db && db.challenges && db.challenges.length > 0) ? db.challenges : CHALLENGES_META;
    
    challenges.forEach(ch => {
        const item = document.createElement('div');
        item.className = 'challenge-item';
        item.innerHTML = `
            <div class="challenge-trigger">
                <span>${ch.title}</span>
                <i class="fa-solid fa-chevron-down"></i>
            </div>
            <div class="challenge-body">
                <div>
                    <span class="challenge-section-title">Challenge Description</span>
                    <p style="margin-top: 0.5rem; font-size: 0.9rem; line-height: 1.5; color: var(--text-secondary);">${ch.desc || ch.description}</p>
                </div>
                <div>
                    <span class="challenge-section-title">Live Spec Reference</span>
                    <p style="margin-top: 0.5rem; font-size: 0.85rem; font-family: monospace; color: var(--accent-purple);">${ch.spec || 'No spec reference listed'}</p>
                </div>
                <div class="challenge-mitigation">
                    <span class="challenge-section-title" style="color: #6ee7b7;">Agent Mitigation Strategy</span>
                    <p style="margin-top: 0.5rem; line-height: 1.5;">${ch.mitigation}</p>
                </div>
            </div>
        `;
        
        const trigger = item.querySelector('.challenge-trigger');
        trigger.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            // Close all
            document.querySelectorAll('.challenge-item').forEach(i => i.classList.remove('active'));
            if (!isActive) {
                item.classList.add('active');
            }
        });
        
        container.appendChild(item);
    });
}

// 6. TQ Generator Form & Sheet
function setupTQForm() {
    const form = document.getElementById('tqForm');
    if (!form) return;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const subsystem = document.getElementById('tqSubsystem').value;
        const docRef = document.getElementById('tqDocRef').value;
        const clause = document.getElementById('tqClause').value;
        const description = document.getElementById('tqDescription').value;
        const proposal = document.getElementById('tqProposal').value;
        
        const newItem = {
            id: tqList.length > 0 ? Math.max(...tqList.map(t => t.id)) + 1 : 1,
            subsystem,
            docRef,
            clause,
            description,
            proposal
        };
        
        tqList.push(newItem);
        renderTQs();
        
        // Reset form
        form.reset();
        
        // Notification
        alert(`TQ Item #${newItem.id} added successfully to sheet.`);
    });
    
    document.getElementById('btnExportTQs').onclick = exportTQsToCSV;
}

function renderTQs() {
    const tbody = document.getElementById('tqTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (tqList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 3rem;">
                    <i class="fa-solid fa-clipboard-list" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>No queries compiled yet. Add items above or trigger in Reviewer Workflow.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tqList.forEach(tq => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-family: monospace; font-weight: 600; color: var(--accent-purple);">#${tq.id}</td>
            <td><span class="tag-badge" style="background: rgba(0,240,255,0.05); border-color: rgba(0,240,255,0.2); color: var(--accent-cyan); font-size: 0.75rem;">${tq.subsystem}</span></td>
            <td><b style="font-size: 0.85rem;">${tq.docRef}</b></td>
            <td style="font-size: 0.85rem; color: var(--text-secondary);">${tq.clause}</td>
            <td style="font-size: 0.85rem; line-height: 1.4;">${tq.description}</td>
            <td style="font-size: 0.85rem; line-height: 1.4; color: #a7f3d0;">${tq.proposal}</td>
            <td style="text-align: center;">
                <button class="tq-delete-btn" onclick="deleteTQItem(${tq.id})">
                    <i class="fa-regular fa-trash-can"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function deleteTQItem(id) {
    if (confirm(`Are you sure you want to delete TQ Item #${id}?`)) {
        tqList = tqList.filter(t => t.id !== id);
        renderTQs();
    }
}

function exportTQsToCSV() {
    if (tqList.length === 0) {
        alert("TQ Sheet is empty. Nothing to export.");
        return;
    }
    
    // Check connection. If Online, post to Flask API
    if (serverOnline) {
        fetch('/api/tq/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tqs: tqList })
        })
        .then(response => {
            if (response.ok) return response.blob();
            throw new Error("CSV generation failed");
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'telecom_security_tqs.csv';
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(err => {
            console.error("Server CSV export failed, falling back to Client CSV download.", err);
            clientSideCSVDownload();
        });
    } else {
        // Fallback to client-side data URI download
        clientSideCSVDownload();
    }
}

function clientSideCSVDownload() {
    const csvRows = [];
    csvRows.push(['TQ Item', 'Subsystem', 'Document Ref', 'Clause/Page Ref', 'Description of Ambiguity / Contradiction', 'Bidder Proposal / Clarification Request', 'Owner Reply']);
    
    tqList.forEach(tq => {
        csvRows.push([
            `#${tq.id}`,
            tq.subsystem,
            tq.docRef,
            tq.clause,
            // Quote field content to handle comma delimiters
            `"${tq.description.replace(/"/g, '""')}"`,
            `"${tq.proposal.replace(/"/g, '""')}"`,
            "" // empty for Owner Reply
        ]);
    });
    
    const csvContent = "data:text/csv;charset=utf-8," + csvRows.map(e => e.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "telecom_security_tqs.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
}

// Offline utility functions
function sanitizeId(name) {
    let s = name.replace(/[^a-zA-Z0-9\s-]/g, '').trim().toLowerCase();
    return s.replace(/[\s-]+/g, '_');
}

function reloadProjectsCatalogScript() {
    return new Promise((resolve) => {
        const oldScript = document.getElementById('dynamicProjectsCatalog');
        if (oldScript) oldScript.remove();
        
        const script = document.createElement('script');
        script.id = 'dynamicProjectsCatalog';
        script.src = 'projects_catalog.js';
        script.onload = () => resolve();
        script.onerror = () => resolve();
        document.body.appendChild(script);
    });
}

// --- HiFi Extractor Console Tab Logic ---
let availablePDFs = [];
let lastExtractedText = "";

async function loadAvailablePDFs() {
    const selector = document.getElementById('extractorFile');
    if (!selector) return;
    
    if (serverOnline) {
        try {
            const response = await fetch('/api/pdf-files');
            if (response.ok) {
                availablePDFs = await response.json();
            } else {
                throw new Error("Failed to load PDF files list");
            }
        } catch (e) {
            console.error("PDF files load error:", e);
            availablePDFs = INDEXED_FILES; // fallback to hardcoded list
        }
    } else {
        availablePDFs = INDEXED_FILES; // fallback to hardcoded list
    }
    
    selector.innerHTML = '';
    if (availablePDFs.length === 0) {
        selector.innerHTML = '<option value="">No PDF files found</option>';
        return;
    }
    
    availablePDFs.forEach(file => {
        const opt = document.createElement('option');
        opt.value = file;
        opt.innerText = file;
        selector.appendChild(opt);
    });
}

function setupHiFiExtractor() {
    const btnRun = document.getElementById('btnRunExtraction');
    const btnCopy = document.getElementById('btnCopyExtracted');
    const btnDownload = document.getElementById('btnDownloadExtracted');
    
    if (!btnRun) return;
    
    btnRun.addEventListener('click', async () => {
        const filename = document.getElementById('extractorFile').value;
        const pages = document.getElementById('extractorPages').value.trim();
        const ocr_lang = document.getElementById('extractorOcrLang').value.trim();
        const dpi = parseInt(document.getElementById('extractorOcrDpi').value) || 300;
        const suppress_margins = document.getElementById('extractorSuppressMargins').checked;
        const margin_method = document.getElementById('extractorMarginMethod').value;
        const header_zone = parseFloat(document.getElementById('extractorHeaderPct').value) || 5;
        const footer_zone = parseFloat(document.getElementById('extractorFooterPct').value) || 5;
        const chunk_size = document.getElementById('extractorEnableChunking').checked ? 
                           parseInt(document.getElementById('extractorChunkSize').value) || 512 : 0;
        const overlap = parseInt(document.getElementById('extractorOverlap').value) || 50;
        
        if (!filename) {
            alert("Please select a target PDF document.");
            return;
        }
        
        if (!serverOnline) {
            alert("The backend Flask server is offline. This operation requires a running local server.");
            return;
        }
        
        // Show spinner, hide other states
        document.getElementById('extractorSpinner').style.display = 'flex';
        document.getElementById('extractorEmptyState').style.display = 'none';
        document.getElementById('extractorResultArea').style.display = 'none';
        btnCopy.disabled = true;
        btnDownload.disabled = true;
        
        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename,
                    pages,
                    ocr_lang,
                    dpi,
                    suppress_margins,
                    margin_method,
                    header_zone,
                    footer_zone,
                    chunk_size,
                    overlap
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                lastExtractedText = data.markdown;
                
                // Set text preview
                document.getElementById('extractorOutputText').innerText = lastExtractedText || "No text extracted.";
                
                // Set stats header
                const statsDiv = document.getElementById('extractorStats');
                const elapsed = data.details.elapsed_seconds || 0.0;
                const chars = data.markdown.length;
                const totalPages = data.details.pages_processed || 0;
                statsDiv.innerHTML = `
                    <span><i class="fa-solid fa-clock"></i> Time: <b>${elapsed.toFixed(1)}s</b></span>
                    <span><i class="fa-solid fa-copy"></i> Extracted: <b>${totalPages} pages</b></span>
                    <span><i class="fa-solid fa-font"></i> Chars: <b>${chars.toLocaleString()}</b></span>
                `;
                
                // Show result area
                document.getElementById('extractorResultArea').style.display = 'flex';
                btnCopy.disabled = false;
                btnDownload.disabled = false;
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || "Unknown server error during extraction.");
            }
        } catch (e) {
            alert(`Extraction failed: ${e.message}`);
            document.getElementById('extractorEmptyState').style.display = 'flex';
        } finally {
            document.getElementById('extractorSpinner').style.display = 'none';
        }
    });
    
    // Copy button
    btnCopy.addEventListener('click', () => {
        if (!lastExtractedText) return;
        navigator.clipboard.writeText(lastExtractedText)
            .then(() => alert("Extracted Markdown text copied to clipboard!"))
            .catch(err => alert("Copy failed: " + err));
    });
    
    // Download button
    btnDownload.addEventListener('click', () => {
        if (!lastExtractedText) return;
        const blob = new Blob([lastExtractedText], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'extracted_document.md';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    });
}

