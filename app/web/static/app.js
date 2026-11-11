// Frontend logic for AI Document Generation Engine

let templateFileId = null;
let referenceFileIds = [];
let currentJobId = null;
let pollInterval = null;

document.addEventListener("DOMContentLoaded", () => {
    initDropzones();
    initTabs();
    initActionHandlers();
});

function initDropzones() {
    // Template dropzone
    const templDrop = document.getElementById("template-dropzone");
    const templInput = document.getElementById("template-file-input");

    templDrop.addEventListener("click", (e) => {
        if (!e.target.closest("#remove-template")) templInput.click();
    });

    templDrop.addEventListener("dragover", (e) => { e.preventDefault(); templDrop.classList.add("dragover"); });
    templDrop.addEventListener("dragleave", () => templDrop.classList.remove("dragover"));
    templDrop.addEventListener("drop", (e) => {
        e.preventDefault();
        templDrop.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) uploadTemplate(e.dataTransfer.files[0]);
    });

    templInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) uploadTemplate(e.target.files[0]);
    });

    document.getElementById("remove-template").addEventListener("click", (e) => {
        e.stopPropagation();
        templateFileId = null;
        document.getElementById("template-chip").style.display = "none";
        document.getElementById("template-prompt").style.display = "block";
        templInput.value = "";
    });

    // Reference dropzone
    const refDrop = document.getElementById("reference-dropzone");
    const refInput = document.getElementById("reference-file-input");

    refDrop.addEventListener("click", () => refInput.click());
    refDrop.addEventListener("dragover", (e) => { e.preventDefault(); refDrop.classList.add("dragover"); });
    refDrop.addEventListener("dragleave", () => refDrop.classList.remove("dragover"));
    refDrop.addEventListener("drop", (e) => {
        e.preventDefault();
        refDrop.classList.remove("dragover");
        for (const file of e.dataTransfer.files) uploadReference(file);
    });

    refInput.addEventListener("change", (e) => {
        for (const file of e.target.files) uploadReference(file);
    });
}

async function uploadTemplate(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        templateFileId = data.file_id;

        document.getElementById("template-name").textContent = data.filename;
        document.getElementById("template-size").textContent = `(${(data.file_size / 1024).toFixed(1)} KB)`;
        document.getElementById("template-chip").style.display = "flex";
        document.getElementById("template-prompt").style.display = "none";
    } catch (err) {
        alert("Template upload failed: " + err.message);
    }
}

async function uploadReference(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        referenceFileIds.push(data.file_id);

        const list = document.getElementById("reference-file-list");
        const item = document.createElement("div");
        item.className = "file-list-item";
        item.id = `ref-item-${data.file_id}`;
        item.innerHTML = `
            <span><strong>${data.filename}</strong> (${(data.file_size / 1024).toFixed(1)} KB)</span>
            <button type="button" class="btn-icon" onclick="removeReference('${data.file_id}')">&times;</button>
        `;
        list.appendChild(item);
    } catch (err) {
        alert("Reference upload failed: " + err.message);
    }
}

window.removeReference = function(fileId) {
    referenceFileIds = referenceFileIds.filter(id => id !== fileId);
    const elem = document.getElementById(`ref-item-${fileId}`);
    if (elem) elem.remove();
};

function initActionHandlers() {
    document.getElementById("btn-start-generation").addEventListener("click", startGeneration);
    document.getElementById("btn-submit-clarifications").addEventListener("click", submitClarifications);
}

async function startGeneration() {
    if (!templateFileId) {
        alert("Please upload a template document (.docx or .pdf) first.");
        return;
    }

    const payload = {
        template_file_id: templateFileId,
        reference_file_ids: referenceFileIds,
        instruction: document.getElementById("instruction-input").value.trim() || null,
        additional_text: document.getElementById("additional-text").value.trim() || null,
        output_format: document.getElementById("output-format").value
    };

    // Show progress card
    document.getElementById("progress-card").style.display = "block";
    document.getElementById("results-card").style.display = "none";
    updateProgressUI("queued", 0);

    try {
        const res = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        currentJobId = data.job_id;

        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollJobStatus, 800);
    } catch (err) {
        alert("Failed to initiate generation: " + err.message);
    }
}

async function pollJobStatus() {
    if (!currentJobId) return;

    try {
        const res = await fetch(`/api/status/${currentJobId}`);
        if (!res.ok) return;
        const job = await res.json();

        updateProgressUI(job.current_step, job.progress_percentage);

        if (job.status === "pending_clarification") {
            clearInterval(pollInterval);
            showClarificationModal(job.clarifications_needed);
        } else if (job.status === "completed") {
            clearInterval(pollInterval);
            renderResults(job);
        } else if (job.status === "failed") {
            clearInterval(pollInterval);
            alert("Generation failed: " + (job.error_message || "Unknown error"));
        }
    } catch (err) {
        console.error("Poll error:", err);
    }
}

function updateProgressUI(step, percent) {
    const fill = document.getElementById("progress-bar-fill");
    fill.style.width = `${percent}%`;

    const badge = document.getElementById("progress-status-badge");
    badge.textContent = step.replace("_", " ").toUpperCase();

    const stageOrder = [
        "uploading",
        "analysing_template",
        "reading_references",
        "mapping_info",
        "generating_docx",
        "checking_formatting",
        "completed"
    ];

    const currentIdx = stageOrder.indexOf(step);
    stageOrder.forEach((stage, idx) => {
        const elem = document.getElementById(`stage-${stage}`);
        if (!elem) return;
        elem.classList.remove("active", "done");
        if (idx < currentIdx) elem.classList.add("done");
        else if (idx === currentIdx) elem.classList.add("active");
    });
}

function showClarificationModal(questions) {
    const modal = document.getElementById("clarification-modal");
    const container = document.getElementById("clarification-form-fields");
    container.innerHTML = "";

    (questions || []).forEach((q, idx) => {
        const group = document.createElement("div");
        group.className = "form-group";
        group.innerHTML = `
            <label>${q}</label>
            <input type="text" class="form-control clarification-input" data-index="${idx}" data-question="${q}" placeholder="Enter verified value">
        `;
        container.appendChild(group);
    });

    modal.style.display = "flex";
}

async function submitClarifications() {
    const inputs = document.querySelectorAll(".clarification-input");
    const clarifications = {};

    inputs.forEach(input => {
        const val = input.value.trim();
        const q = input.getAttribute("data-question");
        // extract field name from question if possible: e.g. 'student_name'
        const match = q.match(/'([^']+)'/);
        const key = match ? match[1] : `clarification_${input.getAttribute("data-index")}`;
        if (val) clarifications[key] = val;
    });

    document.getElementById("clarification-modal").style.display = "none";

    try {
        await fetch(`/api/resolve/${currentJobId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(clarifications)
        });
        pollInterval = setInterval(pollJobStatus, 800);
    } catch (err) {
        alert("Failed to submit clarifications: " + err.message);
    }
}

function renderResults(job) {
    document.getElementById("results-card").style.display = "block";
    document.getElementById("btn-download-docx").href = job.docx_download_url || "#";
    document.getElementById("btn-download-pdf").href = job.pdf_download_url || "#";

    // 1. Render Mapping Table
    const tbody = document.querySelector("#mapping-table tbody");
    tbody.innerHTML = "";
    const mappings = job.mapping_report?.mappings || {};

    Object.keys(mappings).forEach(k => {
        const m = mappings[k];
        const row = document.createElement("tr");
        const statusBadge = m.status === "verified" ? "badge-success" : (m.status === "conflict" ? "badge-danger" : "badge-warning");
        row.innerHTML = `
            <td><code>${m.template_field}</code></td>
            <td><strong>${m.mapped_value}</strong></td>
            <td>${m.source || "N/A"}</td>
            <td>${m.source_page || 1}</td>
            <td>${(m.confidence * 100).toFixed(0)}%</td>
            <td><span class="badge ${statusBadge}">${m.status}</span></td>
        `;
        tbody.appendChild(row);
    });

    // 2. Render Validation Report
    const valContainer = document.getElementById("validation-report-content");
    const v = job.validation_report;
    if (v) {
        valContainer.innerHTML = `
            <div class="stats-grid" style="margin-bottom: 1.25rem;">
                <div class="stat-box">
                    <div class="stat-value">${v.is_valid ? "VALID" : "CORRECTED"}</div>
                    <div class="stat-label">Visual Status</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${v.iteration}</div>
                    <div class="stat-label">Correction Loops</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${v.generated_page_count} / ${v.template_page_count}</div>
                    <div class="stat-label">Generated vs Template Pages</div>
                </div>
            </div>
            <h4>Corrections Applied:</h4>
            <ul>${(v.corrections_applied || []).map(c => `<li>${c}</li>`).join("") || "<li>None required - formatting visually perfect on first pass.</li>"}</ul>
        `;
    }

    // 3. Render Token Stats
    const tokenGrid = document.getElementById("token-stats-grid");
    const t = job.token_usage;
    if (t) {
        tokenGrid.innerHTML = `
            <div class="stat-box">
                <div class="stat-value">${t.local_operations_count}</div>
                <div class="stat-label">Local 0-Token Operations</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${t.qwen_local_tokens.toLocaleString()}</div>
                <div class="stat-label">Qwen3:8B Local Tokens</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${t.gemini_cloud_tokens.toLocaleString()}</div>
                <div class="stat-label">Gemini Cloud Tokens</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">$${t.estimated_cost_savings_usd.toFixed(4)}</div>
                <div class="stat-label">Cloud Cost Saved</div>
            </div>
        `;
    }

    // 4. Render Template Profile
    document.getElementById("template-profile-code").textContent = JSON.stringify(job.template_profile, null, 2);
}

function initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById(btn.getAttribute("data-tab")).classList.add("active");
        });
    });
}
