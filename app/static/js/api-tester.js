// API Tester JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const apiTestForm = document.getElementById('api-test-form');
    const responseContainer = document.getElementById('response-container');
    const responseHeaders = document.getElementById('response-headers');
    const requestHistory = document.getElementById('request-history');
    const clearHistoryBtn = document.getElementById('clear-history');
    const addHeaderBtn = document.getElementById('add-header');
    const statusBadge = document.getElementById('status-badge');
    const timeBadge = document.getElementById('time-badge');
    
    let requestHistoryData = JSON.parse(localStorage.getItem('apiTesterHistory') || '[]');
    
    // Initialize
    renderHistory();
    
    // Handle form submission
    apiTestForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await sendRequest();
    });
    
    // Handle method change to show/hide body section
    document.getElementById('method').addEventListener('change', function() {
        const method = this.value;
        const bodySection = document.getElementById('body-section');
        
        if (['POST', 'PUT', 'PATCH'].includes(method)) {
            bodySection.style.display = 'block';
        } else {
            bodySection.style.display = 'none';
        }
    });
    
    // Clear history
    clearHistoryBtn.addEventListener('click', function() {
        requestHistoryData = [];
        localStorage.setItem('apiTesterHistory', JSON.stringify(requestHistoryData));
        renderHistory();
    });
    
    // Handle history item clicks
    requestHistory.addEventListener('click', function(e) {
        const historyItem = e.target.closest('.history-item');
        if (historyItem) {
            const index = parseInt(historyItem.dataset.index);
            loadHistoryItem(index);
        }
    });
    
    
    // Send API request
    async function sendRequest() {
        const method = document.getElementById('method').value;
        const url = document.getElementById('url').value;
        const body = document.getElementById('body').value;
        
        // Auto-configure headers based on method and content
        const headers = {
            'Accept': 'application/json'
        };
        
        // Add Content-Type for requests with body
        if (['POST', 'PUT', 'PATCH'].includes(method) && body.trim()) {
            headers['Content-Type'] = 'application/json';
        }
        
        const startTime = Date.now();
        
        try {
            showLoading();
            
            const fullUrl = url.startsWith('http') ? url : `${window.location.origin}/api/v1${url}`;
            
            const response = await fetch('/ui/proxy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    method: method,
                    url: fullUrl,
                    headers: headers,
                    body: body || null
                })
            });
            
            const result = await response.json();
            const endTime = Date.now();
            const duration = endTime - startTime;
            
            displayResponse(result, duration);
            
            // Add to history
            addToHistory(method, url, headers, body, result, duration);
            
        } catch (error) {
            displayError(error.message);
            addToHistory(method, url, headers, body, { success: false, error: error.message }, 0);
        } finally {
            hideLoading();
        }
    }
    
    // Display response
    function displayResponse(result, duration) {
        const responseDiv = document.createElement('div');
        responseDiv.className = 'response-animation';
        
        let statusClass = 'response-info';
        if (result.success) {
            if (result.status_code >= 200 && result.status_code < 300) {
                statusClass = 'response-success';
            } else if (result.status_code >= 400) {
                statusClass = 'response-error';
            }
        } else {
            statusClass = 'response-error';
        }
        
        responseDiv.className += ` ${statusClass}`;
        
        // Update status badges
        statusBadge.textContent = result.status_code || 'Error';
        statusBadge.className = `badge bg-${result.success ? 'success' : 'danger'}`;
        timeBadge.textContent = `${duration}ms`;
        
        let responseContent = '';
        if (result.success) {
            responseContent = formatJSON(result.data);
        } else {
            responseContent = `
                <div class="json-response">${result.error || 'Unknown error'}</div>
            `;
        }
        
        responseDiv.innerHTML = responseContent;
        
        // Store response data for copying
        if (result.success && result.data) {
            responseDiv.dataset.responseData = JSON.stringify(result.data);
        }
        
        responseContainer.innerHTML = '';
        responseContainer.appendChild(responseDiv);
        
        // Display headers
        displayHeaders(result.headers || {});
    }
    
    // Display response headers
    function displayHeaders(headers) {
        if (Object.keys(headers).length === 0) {
            responseHeaders.innerHTML = '<p class="text-muted">No response headers.</p>';
            return;
        }
        
        const headersDiv = document.createElement('div');
        headersDiv.className = 'json-response';
        
        let headersText = '';
        for (const [key, value] of Object.entries(headers)) {
            headersText += `${key}: ${value}\n`;
        }
        
        headersDiv.textContent = headersText.trim();
        responseHeaders.innerHTML = '';
        responseHeaders.appendChild(headersDiv);
    }
    
    // Display error
    function displayError(message) {
        const responseDiv = document.createElement('div');
        responseDiv.className = 'response-error response-animation';
        responseDiv.innerHTML = `
            <div class="json-response">${message}</div>
        `;
        responseContainer.innerHTML = '';
        responseContainer.appendChild(responseDiv);
        
        // Update status badges
        statusBadge.textContent = 'Error';
        statusBadge.className = 'badge bg-danger';
        timeBadge.textContent = '0ms';
        
        responseHeaders.innerHTML = '<p class="text-muted">No response headers.</p>';
    }
    
    // Add to history
    function addToHistory(method, url, headers, body, result, duration) {
        const historyItem = {
            id: Date.now(),
            method: method,
            url: url,
            headers: headers,
            body: body,
            result: result,
            duration: duration,
            timestamp: new Date().toLocaleString()
        };
        
        requestHistoryData.unshift(historyItem);
        
        // Keep only last 50 items
        if (requestHistoryData.length > 50) {
            requestHistoryData = requestHistoryData.slice(0, 50);
        }
        
        localStorage.setItem('apiTesterHistory', JSON.stringify(requestHistoryData));
        renderHistory();
    }
    
    // Render history
    function renderHistory() {
        if (requestHistoryData.length === 0) {
            requestHistory.innerHTML = '<p class="text-muted">No requests made yet.</p>';
            return;
        }
        
        const historyHTML = requestHistoryData.map((item, index) => `
            <div class="history-item" data-index="${index}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <span class="history-method badge bg-${getMethodColor(item.method)} me-2">${item.method}</span>
                        <span class="history-url">${item.url}</span>
                    </div>
                    <div class="text-end">
                        <div class="history-time">${item.timestamp}</div>
                        <small class="text-muted">${item.duration}ms</small>
                    </div>
                </div>
            </div>
        `).join('');
        
        requestHistory.innerHTML = historyHTML;
    }
    
    // Load history item
    function loadHistoryItem(index) {
        const item = requestHistoryData[index];
        if (!item) return;
        
        // Update form
        document.getElementById('method').value = item.method;
        document.getElementById('url').value = item.url;
        document.getElementById('body').value = item.body || '';
        
        // Show/hide body section based on method
        const method = item.method;
        const bodySection = document.getElementById('body-section');
        
        if (['POST', 'PUT', 'PATCH'].includes(method)) {
            bodySection.style.display = 'block';
        } else {
            bodySection.style.display = 'none';
        }
        
        // Update visual selection
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('selected'));
        document.querySelector(`[data-index="${index}"]`).classList.add('selected');
    }
    
    // Get method color
    function getMethodColor(method) {
        const colors = {
            'GET': 'success',
            'POST': 'primary',
            'PUT': 'warning',
            'DELETE': 'danger',
            'PATCH': 'info',
            'OPTIONS': 'secondary'
        };
        return colors[method] || 'secondary';
    }
    
    // Show loading state
    function showLoading() {
        const submitBtn = apiTestForm.querySelector('button[type="submit"]');
        const spinner = document.getElementById('loading-spinner');
        
        submitBtn.disabled = true;
        spinner.classList.remove('d-none');
    }
    
    // Hide loading state
    function hideLoading() {
        const submitBtn = apiTestForm.querySelector('button[type="submit"]');
        const spinner = document.getElementById('loading-spinner');
        
        submitBtn.disabled = false;
        spinner.classList.add('d-none');
    }
    
    // Format JSON for display with interactive viewer
    function formatJSON(obj) {
        if (typeof obj === 'string') {
            try {
                obj = JSON.parse(obj);
            } catch (e) {
                return obj;
            }
        }
        
        // Create interactive JSON viewer with controls
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
        viewer.innerHTML = createJSONViewer(obj, 0);
        
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
    
    // Create interactive JSON viewer HTML
    function createJSONViewer(obj, depth = 0) {
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
                const itemHtml = createJSONViewer(item, depth + 1);
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
                const valueHtml = createJSONViewer(obj[key], depth + 1);
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
    
    // Toggle JSON node visibility
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
        const responseContainer = container.closest('.response-animation');
        
        if (responseContainer && responseContainer.dataset.responseData) {
            try {
                const jsonData = JSON.parse(responseContainer.dataset.responseData);
                const jsonString = JSON.stringify(jsonData, null, 2);
                navigator.clipboard.writeText(jsonString).then(() => {
                    showCopyNotification();
                }).catch(() => {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = jsonString;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    showCopyNotification();
                });
            } catch (e) {
                console.error('Error copying JSON:', e);
            }
        }
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
});
