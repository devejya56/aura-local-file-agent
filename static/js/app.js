/* ══════════════════════════════════════════════════════════
   AURA — Dashboard Application Logic
   Handles API calls, SSE live updates, file upload, and navigation
   ══════════════════════════════════════════════════════════ */

// ── View Navigation ─────────────────────────────────────────

document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const viewName = tab.dataset.view;
        switchView(viewName);
    });
});

function switchView(viewName) {
    // Update tabs
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

    // Update views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const view = document.getElementById(`view-${viewName}`);
    if (view) {
        view.classList.remove('active');
        // Force reflow for animation
        void view.offsetWidth;
        view.classList.add('active');
    }

    // Refresh data for the view
    if (viewName === 'history') loadHistory();
    if (viewName === 'settings') loadConfig();
    if (viewName === 'dashboard') { loadStats(); loadArchivedFiles(); }
}


// ── API Helpers ─────────────────────────────────────────────

async function api(endpoint, options = {}) {
    try {
        const resp = await fetch(`/api/${endpoint}`, options);
        return await resp.json();
    } catch (err) {
        console.error(`API error [${endpoint}]:`, err);
        return null;
    }
}


// ── Dashboard Stats ─────────────────────────────────────────

async function loadStats() {
    const data = await api('stats');
    if (!data) return;

    animateNumber('statProcessed', data.files_processed);
    animateNumber('statMoves', data.total_moves);
    animateNumber('statIndexed', data.total_indexed);
    document.getElementById('statModel').textContent = data.model || '—';

    // Update status indicator
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    if (data.agent_running) {
        dot.classList.remove('offline');
        text.textContent = 'Watching';
    } else {
        dot.classList.add('offline');
        text.textContent = 'Stopped';
    }
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const current = parseInt(el.textContent) || 0;
    if (current === target) return;

    const duration = 600;
    const start = performance.now();

    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        el.textContent = Math.round(current + (target - current) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}


// ── Live Activity Feed (SSE) ────────────────────────────────

let eventSource = null;

function connectSSE() {
    if (eventSource) eventSource.close();

    eventSource = new EventSource('/api/events');

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'keepalive') return;
            handleEvent(data);
        } catch (e) {
            console.error('SSE parse error:', e);
        }
    };

    eventSource.onerror = () => {
        console.warn('SSE connection lost, reconnecting in 5s...');
        setTimeout(connectSSE, 5000);
    };
}

function handleEvent(event) {
    addActivityItem(event);
    loadStats();
    if (event.type === 'file_processed') {
        loadArchivedFiles();
    }
}

function addActivityItem(event) {
    const list = document.getElementById('activityList');

    // Clear empty state
    const empty = list.querySelector('.activity-empty');
    if (empty) empty.remove();

    const item = document.createElement('div');
    item.className = 'activity-item';

    let icon = '📄';
    let badgeClass = 'badge-processing';
    let statusText = '';

    switch (event.type) {
        case 'file_detected':
            icon = '🔍';
            badgeClass = 'badge-processing';
            statusText = 'Processing...';
            break;
        case 'file_processed':
            icon = '✅';
            badgeClass = 'badge-success';
            statusText = 'Organized';
            break;
        case 'file_failed':
            icon = '❌';
            badgeClass = 'badge-failed';
            statusText = 'Failed';
            break;
        case 'file_uploaded':
            icon = '📤';
            badgeClass = 'badge-upload';
            statusText = 'Uploaded';
            break;
        case 'agent_started':
            icon = '▶️';
            badgeClass = 'badge-success';
            statusText = 'Agent started';
            break;
        case 'agent_stopped':
            icon = '⏸️';
            badgeClass = 'badge-failed';
            statusText = 'Agent stopped';
            break;
    }

    const filename = event.data?.filename || event.data?.message || event.type;
    const time = new Date(event.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    item.innerHTML = `
        <div class="item-icon ${badgeClass}">${icon}</div>
        <div class="item-content">
            <div class="item-title">${escapeHtml(filename)}</div>
            <div class="item-sub">${statusText}</div>
        </div>
        <span class="item-time">${time}</span>
    `;

    list.insertBefore(item, list.firstChild);

    // Keep max 30 items
    while (list.children.length > 30) {
        list.removeChild(list.lastChild);
    }
}


// ── File Upload / Drag & Drop ───────────────────────────────

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
        uploadFile(e.dataTransfer.files[0]);
    }
});

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
        fileInput.value = '';
    }
});

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    showToast(`Uploading ${file.name}...`);

    const resp = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
    });

    const result = await resp.json();
    if (result.success) {
        showToast(`✓ ${file.name} uploaded`);
    } else {
        showToast(`✗ Upload failed: ${result.error}`);
    }
}


// ── History ─────────────────────────────────────────────────

async function loadHistory() {
    const moves = await api('history?n=30');
    if (!moves) return;

    const tbody = document.getElementById('historyBody');

    if (moves.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-text">No history yet</td></tr>';
        return;
    }

    tbody.innerHTML = moves.map(m => `
        <tr>
            <td>${m.id}</td>
            <td><span class="history-cat">${escapeHtml(m.category || 'Unknown')}</span></td>
            <td title="${escapeHtml(m.original_path)}">${escapeHtml(basename(m.original_path))}</td>
            <td title="${escapeHtml(m.new_path)}">${escapeHtml(basename(m.new_path))}</td>
            <td>${formatTime(m.timestamp)}</td>
        </tr>
    `).join('');
}

async function handleUndo() {
    const result = await api('undo', { method: 'POST' });
    if (result?.success) {
        showToast('✓ Last move undone');
        loadHistory();
        loadStats();
        loadArchivedFiles();
    } else {
        showToast('✗ Nothing to undo');
    }
}


// ── Search ──────────────────────────────────────────────────

document.getElementById('searchInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSearch();
});

async function handleSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) return;

    const container = document.getElementById('searchResults');
    container.innerHTML = '<div class="search-empty"><p>Searching...</p></div>';

    const results = await api('search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 8 }),
    });

    if (!results || results.length === 0) {
        container.innerHTML = '<div class="search-empty"><p>No results found</p></div>';
        return;
    }

    container.innerHTML = results.map(r => {
        const meta = r.metadata || {};
        const score = r.distance != null ? ((1 - r.distance) * 100).toFixed(1) : '?';
        const preview = (r.document || '').substring(0, 200);
        return `
            <div class="search-result">
                <div class="sr-header">
                    <span class="sr-filename">📄 ${escapeHtml(meta.filename || 'Unknown')}</span>
                    <span class="sr-score">${score}% match</span>
                </div>
                <p class="sr-preview">${escapeHtml(preview)}${preview.length >= 200 ? '...' : ''}</p>
            </div>
        `;
    }).join('');
}


// ── Chat (RAG) ──────────────────────────────────────────────

document.getElementById('chatInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleChat();
});

async function handleChat() {
    const input = document.getElementById('chatInput');
    const query = input.value.trim();
    if (!query) return;

    input.value = '';
    const messages = document.getElementById('chatMessages');

    // Add User Message
    messages.innerHTML += `
        <div class="message user-message">
            <div class="msg-content">${escapeHtml(query)}</div>
        </div>
    `;
    messages.scrollTop = messages.scrollHeight;

    // Add Typing Indicator
    const typingId = 'typing-' + Date.now();
    messages.innerHTML += `
        <div class="message system-message" id="${typingId}">
            <div class="msg-avatar">✨</div>
            <div class="msg-content processing-dots">Thinking<span>.</span><span>.</span><span>.</span></div>
        </div>
    `;
    messages.scrollTop = messages.scrollHeight;

    // Call API
    const result = await api('chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    });

    // Remove Typing Indicator
    document.getElementById(typingId)?.remove();

    if (!result || result.error) {
        messages.innerHTML += `
            <div class="message system-message error">
                <div class="msg-avatar">⚠️</div>
                <div class="msg-content">${escapeHtml(result?.error || 'Failed to get a response.')}</div>
            </div>
        `;
    } else {
        // Format Sources
        let sourcesHtml = '';
        if (result.sources && result.sources.length > 0) {
            sourcesHtml = '<div class="chat-sources"><span>Sources:</span>';
            result.sources.forEach(src => {
                sourcesHtml += `<span class="chat-source-badge" title="${escapeHtml(src.path)}">${escapeHtml(src.filename)}</span>`;
            });
            sourcesHtml += '</div>';
        }

        // Add System Response
        messages.innerHTML += `
            <div class="message system-message">
                <div class="msg-avatar">
                    <svg width="20" height="20" viewBox="0 0 28 28" fill="none">
                        <circle cx="14" cy="14" r="12" stroke="#FC6E20" stroke-width="2" fill="none" />
                        <circle cx="14" cy="14" r="6" fill="#FFB380" />
                    </svg>
                </div>
                <div class="msg-content">
                    <p style="white-space: pre-wrap; margin: 0;">${escapeHtml(result.answer)}</p>
                    ${sourcesHtml}
                </div>
            </div>
        `;
    }
    messages.scrollTop = messages.scrollHeight;
}


// ── Native Folder Organization ──────────────────────────────

async function handleSelectFolder() {
    showToast('Opening folder picker...');

    const result = await api('select-folder');
    if (!result || !result.path) {
        showToast('No folder selected');
        return;
    }

    if (confirm(`Do you want Aura to organize all files inside:\n${result.path}?`)) {
        const processResult = await api('process-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: result.path })
        });

        if (processResult?.success) {
            showToast('Started background processing...');
        } else {
            showToast('Failed to start processing');
        }
    }
}


// ── Settings ────────────────────────────────────────────────

async function loadConfig() {
    const cfg = await api('config');
    if (!cfg) return;

    document.getElementById('cfgWatch').textContent = cfg.watch_directory;
    document.getElementById('cfgArchive').textContent = cfg.archive_directory;
    document.getElementById('cfgDb').textContent = cfg.db_path;
    document.getElementById('cfgOllama').textContent = cfg.ollama_base_url;
    document.getElementById('cfgModel').textContent = cfg.llm_model;
    document.getElementById('cfgTemp').textContent = cfg.llm_temperature;
    document.getElementById('cfgVector').textContent = cfg.enable_vector_search ? 'Enabled' : 'Disabled';
    document.getElementById('cfgBackup').textContent = cfg.enable_backup ? 'Enabled' : 'Disabled';
    document.getElementById('cfgLog').textContent = cfg.log_level;
}


// ── Agent Control ───────────────────────────────────────────

async function toggleAgent(start) {
    const endpoint = start ? 'watcher/start' : 'watcher/stop';
    const result = await api(endpoint, { method: 'POST' });

    if (result?.success) {
        showToast(start ? '▶ Agent started' : '⏸ Agent stopped');
        loadStats();
    }
}


// ── Archived Files ──────────────────────────────────────────

async function loadArchivedFiles() {
    const files = await api('archived-files');
    if (!files) return;

    const list = document.getElementById('fileList');
    document.getElementById('fileCount').textContent = files.length;

    if (files.length === 0) {
        list.innerHTML = '<p class="empty-text">No files organized yet</p>';
        return;
    }

    list.innerHTML = files.map(f => {
        const ext = f.extension || '';
        const icon = getFileIcon(ext);
        return `
            <div class="file-item">
                <span class="fi-icon">${icon}</span>
                <span class="fi-name" title="${escapeHtml(f.path)}">${escapeHtml(f.name)}</span>
                <span class="fi-cat">${escapeHtml(f.category)}</span>
            </div>
        `;
    }).join('');
}


// ── Utility Functions ───────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

function basename(path) {
    return path ? path.split(/[\\/]/).pop() : '';
}

function formatTime(isoStr) {
    if (!isoStr) return '—';
    try {
        return new Date(isoStr).toLocaleString([], {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    } catch {
        return isoStr;
    }
}

function getFileIcon(ext) {
    const icons = {
        '.pdf': '📕', '.doc': '📘', '.docx': '📘', '.txt': '📄',
        '.py': '🐍', '.js': '📜', '.json': '📦', '.csv': '📊',
        '.md': '📝', '.html': '🌐', '.xml': '📋', '.yaml': '⚙️',
        '.png': '🖼️', '.jpg': '🖼️', '.gif': '🖼️', '.svg': '🎨',
        '.zip': '📦', '.sql': '🗄️', '.log': '📋',
    };
    return icons[ext?.toLowerCase()] || '📄';
}

function showToast(message) {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3500);
}


// ── Initialize ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadArchivedFiles();
    connectSSE();

    // Auto-refresh stats every 10 seconds
    setInterval(loadStats, 10000);
});
