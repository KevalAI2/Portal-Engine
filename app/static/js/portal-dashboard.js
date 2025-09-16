// Portal Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Set default user ID to "1"
    document.getElementById('user-id').value = '1';
    
    // Initialize any other default values
    console.log('Portal Dashboard initialized');
});

// API Configuration Functions
async function testConnection() {
    const button = event.target;
    const statusDiv = document.getElementById('connection-status');
    
    showLoading(button, 'Testing...');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'GET',
                url: 'http://localhost:3031/ping',
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(statusDiv, result);
    } catch (error) {
        displayError(statusDiv, 'Connection failed: ' + error.message);
    } finally {
        hideLoading(button, 'Test Connection');
    }
}

// Health Check Functions
async function checkHealth(type) {
    const button = event.target;
    const statusDiv = document.getElementById('health-status');
    
    showLoading(button, 'Checking...');
    
    try {
        const endpoint = type === 'health' ? '/api/v1/health/' : `/api/v1/health/${type}`;
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'GET',
                url: `http://localhost:3031${endpoint}`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(statusDiv, result);
    } catch (error) {
        displayError(statusDiv, 'Health check failed: ' + error.message);
    } finally {
        hideLoading(button, `Check ${type.charAt(0).toUpperCase() + type.slice(1)}`);
    }
}

// User Operations Functions
async function getUserProfile() {
    const userId = document.getElementById('user-id').value;
    const dataDiv = document.getElementById('profile-data');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'GET',
                url: `http://localhost:3031/api/v1/users/${userId}/profile`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get user profile: ' + error.message);
    }
}

async function getUserLocation() {
    const userId = document.getElementById('user-id').value;
    const dataDiv = document.getElementById('location-data');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'GET',
                url: `http://localhost:3031/api/v1/users/${userId}/location`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get user location: ' + error.message);
    }
}

async function getUserInteractions() {
    const userId = document.getElementById('user-id').value;
    const dataDiv = document.getElementById('interaction-data');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'GET',
                url: `http://localhost:3031/api/v1/users/${userId}/interactions`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get user interactions: ' + error.message);
    }
}

// Recommendations Functions
async function generateRecommendations() {
    const userId = document.getElementById('user-id').value;
    const prompt = document.getElementById('custom-prompt').value;
    const dataDiv = document.getElementById('recommendations-data');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'POST',
                url: `http://localhost:3031/api/v1/users/${userId}/generate-recommendations`,
                headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt || null })
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to generate recommendations: ' + error.message);
    }
}

async function generateDirectRecommendations() {
    const prompt = document.getElementById('custom-prompt').value;
    const dataDiv = document.getElementById('recommendations-data');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'POST',
                url: 'http://localhost:3031/api/v1/users/generate-recommendations',
                headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt || null })
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to generate direct recommendations: ' + error.message);
    }
}

async function clearRecommendations() {
    const userId = document.getElementById('user-id').value;
    const dataDiv = document.getElementById('recommendations-data');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'DELETE',
                url: `http://localhost:3031/api/v1/users/${userId}/recommendations`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to clear recommendations: ' + error.message);
    }
}

// Results & Analytics Functions
async function getRankedResults() {
    const userId = document.getElementById('user-id').value;
    const category = document.getElementById('category-filter').value;
    const limit = document.getElementById('results-limit').value;
    const minScore = document.getElementById('min-score').value;
    const dataDiv = document.getElementById('ranked-results');
    
    try {
        let url = `http://localhost:3031/api/v1/users/${userId}/results?`;
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (limit) params.append('limit', limit);
        if (minScore) params.append('min_score', minScore);
        url += params.toString();
        
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'GET',
                url: url,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get ranked results: ' + error.message);
    }
}

// Internal Details & Debugging Functions
async function getSearchQueries() {
    const dataDiv = document.getElementById('search-queries');
    const userId = document.getElementById('search-user-id').value;
    
    try {
        let url = '/ui/debug/search-queries';
        if (userId && userId.trim() !== '') {
            url += `?user_id=${encodeURIComponent(userId.trim())}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get search queries: ' + error.message);
    }
}

async function getMLParameters() {
    const dataDiv = document.getElementById('ml-parameters');
    
    try {
        const response = await fetch('/ui/debug/ml-parameters');
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get ML parameters: ' + error.message);
    }
}

async function getPrefetchStats() {
    const dataDiv = document.getElementById('prefetch-stats');
    
    try {
        const response = await fetch('/ui/debug/prefetch-stats');
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get prefetch stats: ' + error.message);
    }
}

// Processing Pipeline Functions
async function getPipelineDetails() {
    const dataDiv = document.getElementById('pipeline-details');
    
    try {
        const response = await fetch('/ui/debug/pipeline-details');
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get pipeline details: ' + error.message);
    }
}

async function getEngineDetails() {
    const dataDiv = document.getElementById('engine-details');
    
    try {
        const response = await fetch('/ui/debug/engine-details');
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get engine details: ' + error.message);
    }
}

async function getPerformanceMetrics() {
    const dataDiv = document.getElementById('performance-metrics');
    
    try {
        const response = await fetch('/ui/debug/performance-metrics');
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to get performance metrics: ' + error.message);
    }
}

// Processing Tasks Functions
async function processUserAsync() {
    const userId = document.getElementById('user-id').value;
    const priority = document.getElementById('task-priority').value;
    const dataDiv = document.getElementById('task-status');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'POST',
                url: `http://localhost:3031/api/v1/users/${userId}/process-comprehensive?priority=${priority}`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to process user: ' + error.message);
    }
}

async function processUserDirect() {
    const userId = document.getElementById('user-id').value;
    const dataDiv = document.getElementById('task-status');
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'POST',
                url: `http://localhost:3031/api/v1/users/${userId}/process-comprehensive-direct`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to process user directly: ' + error.message);
    }
}

async function checkTaskStatus() {
    const taskId = document.getElementById('task-id').value;
    const dataDiv = document.getElementById('task-status');
    
    if (!taskId.trim()) {
        displayError(dataDiv, 'Please enter a task ID');
        return;
    }
    
    try {
        const response = await fetch('/ui/proxy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'GET',
                url: `http://localhost:3031/api/v1/users/1/processing-status/${taskId}`,
                headers: { 'Accept': 'application/json' }
            })
        });
        
        const result = await response.json();
        displayJSON(dataDiv, result);
    } catch (error) {
        displayError(dataDiv, 'Failed to check task status: ' + error.message);
    }
}

// Utility Functions
function displayJSON(container, data) {
    if (data.success && data.data) {
        container.innerHTML = createJSONViewer(data.data);
    } else {
        container.innerHTML = createJSONViewer(data);
    }
}

function displayError(container, message) {
    container.innerHTML = `<p class="text-danger">${message}</p>`;
}

function showLoading(button, text) {
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${text}`;
}

function hideLoading(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

// JSON Viewer Functions
function createJSONViewer(obj) {
    const container = document.createElement('div');
    container.className = 'json-viewer-container';
    
    const controls = document.createElement('div');
    controls.className = 'json-viewer-controls';
    controls.innerHTML = `
        <h6 class="json-viewer-title">JSON Response</h6>
        <div class="json-viewer-actions">
            <button class="json-expand-all-btn" onclick="expandAllJSON(this)">Expand All</button>
            <button class="json-copy-btn" onclick="copyJSON(this)">Copy JSON</button>
        </div>
    `;
    
    const viewer = document.createElement('div');
    viewer.className = 'json-viewer';
    viewer.innerHTML = createJSONViewerHTML(obj, 0);
    
    // Add click handlers for toggles
    viewer.addEventListener('click', function(e) {
        if (e.target.classList.contains('json-toggle')) {
            toggleJSONNode(e.target);
        }
    });
    
    container.appendChild(controls);
    container.appendChild(viewer);
    
    return container.outerHTML;
}

function createJSONViewerHTML(obj, depth = 0) {
    const indent = '  '.repeat(depth);
    const nextIndent = '  '.repeat(depth + 1);
    
    if (obj === null) {
        return `<span class="json-null">null</span>`;
    }
    
    if (typeof obj === 'undefined') {
        return `<span class="json-null">undefined</span>`;
    }
    
    if (typeof obj === 'boolean') {
        return `<span class="json-boolean">${obj}</span>`;
    }
    
    if (typeof obj === 'number') {
        return `<span class="json-number">${obj}</span>`;
    }
    
    if (typeof obj === 'string') {
        const escaped = obj.replace(/"/g, '\\"');
        return `<span class="json-string">"${escaped}"</span>`;
    }
    
    if (Array.isArray(obj)) {
        if (obj.length === 0) {
            return `<span class="json-bracket">[</span><span class="json-bracket">]</span>`;
        }
        
        const id = 'array_' + Math.random().toString(36).substr(2, 9);
        const items = obj.map((item, index) => {
            const itemHtml = createJSONViewerHTML(item, depth + 1);
            const comma = index < obj.length - 1 ? '<span class="json-comma">,</span>' : '';
            return `<div class="json-line">${nextIndent}${itemHtml}${comma}</div>`;
        }).join('');
        
        return `
            <span class="json-toggle" data-target="${id}">▼</span>
            <span class="json-bracket">[</span>
            <div id="${id}" class="json-array">
                ${items}
            </div>
            <div class="json-line">${indent}<span class="json-bracket">]</span></div>
        `;
    }
    
    if (typeof obj === 'object') {
        const keys = Object.keys(obj);
        if (keys.length === 0) {
            return `<span class="json-bracket">{</span><span class="json-bracket">}</span>`;
        }
        
        const id = 'object_' + Math.random().toString(36).substr(2, 9);
        const items = keys.map((key, index) => {
            const valueHtml = createJSONViewerHTML(obj[key], depth + 1);
            const comma = index < keys.length - 1 ? '<span class="json-comma">,</span>' : '';
            return `
                <div class="json-line">
                    ${nextIndent}<span class="json-key">"${key}"</span>: ${valueHtml}${comma}
                </div>
            `;
        }).join('');
        
        return `
            <span class="json-toggle" data-target="${id}">▼</span>
            <span class="json-bracket">{</span>
            <div id="${id}" class="json-object">
                ${items}
            </div>
            <div class="json-line">${indent}<span class="json-bracket">}</span></div>
        `;
    }
    
    return `<span class="json-string">"${String(obj)}"</span>`;
}

function toggleJSONNode(toggle) {
    const targetId = toggle.getAttribute('data-target');
    const target = document.getElementById(targetId);
    
    if (!target) return;
    
    if (target.style.display === 'none') {
        target.style.display = 'block';
        toggle.textContent = '▼';
    } else {
        target.style.display = 'none';
        toggle.textContent = '▶';
    }
}

// Copy JSON to clipboard
window.copyJSON = function(button) {
    const container = button.closest('.json-viewer-container');
    const viewer = container.querySelector('.json-viewer');
    
    // Extract JSON data from the viewer
    const jsonText = extractJSONFromViewer(viewer);
    
    navigator.clipboard.writeText(jsonText).then(() => {
        showCopyNotification();
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = jsonText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showCopyNotification();
    });
};

// Expand all JSON nodes
window.expandAllJSON = function(button) {
    const container = button.closest('.json-viewer-container');
    const toggles = container.querySelectorAll('.json-toggle');
    
    toggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-target');
        const target = document.getElementById(targetId);
        if (target && target.style.display === 'none') {
            target.style.display = 'block';
            toggle.textContent = '▼';
        }
    });
    
    button.textContent = 'Collapse All';
    button.onclick = function() { collapseAllJSON(this); };
};

// Collapse all JSON nodes
window.collapseAllJSON = function(button) {
    const container = button.closest('.json-viewer-container');
    const toggles = container.querySelectorAll('.json-toggle');
    
    toggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-target');
        const target = document.getElementById(targetId);
        if (target && target.style.display !== 'none') {
            target.style.display = 'none';
            toggle.textContent = '▶';
        }
    });
    
    button.textContent = 'Expand All';
    button.onclick = function() { expandAllJSON(this); };
};

// Extract JSON text from viewer
function extractJSONFromViewer(viewer) {
    // This is a simplified extraction - in a real implementation,
    // you'd want to reconstruct the JSON from the DOM elements
    return JSON.stringify({ message: "JSON data extracted from viewer" }, null, 2);
}

// Show copy notification
function showCopyNotification() {
    // Remove existing notification
    const existing = document.querySelector('.copy-notification');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = 'copy-notification';
    notification.textContent = 'JSON copied to clipboard!';
    
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}
