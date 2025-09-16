// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const quickTestForm = document.getElementById('quick-test-form');
    const responseContainer = document.getElementById('response-container');
    
    // Handle quick test form submission
    quickTestForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const endpointValue = document.getElementById('test-endpoint').value;
        if (!endpointValue) {
            showError('Please select an endpoint');
            return;
        }
        
        const [method, urlTemplate] = endpointValue.split(':');
        const userId = document.getElementById('test-user-id').value;
        
        // Build the actual URL
        let url = urlTemplate;
        if (urlTemplate.includes('{user_id}')) {
            if (!userId.trim()) {
                showError('Please enter a User ID');
                return;
            }
            url = urlTemplate.replace('{user_id}', userId.trim());
        }
        
        // Build headers and body based on endpoint
        const { headers, body, finalUrl } = buildRequestData(method, url);
        
        await sendRequest(method, finalUrl, headers, body);
    });
    
    // Send API request
    async function sendRequest(method, url, headers, body) {
        const startTime = Date.now();
        
        try {
            showLoading();
            
            const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
            
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
            
        } catch (error) {
            displayError(error.message);
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
        
        const statusBadge = `<span class="badge bg-${result.success ? 'success' : 'danger'}">${result.status_code || 'Error'}</span>`;
        const timeBadge = `<span class="badge bg-info">${duration}ms</span>`;
        
        let responseContent = '';
        if (result.success) {
            responseContent = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6>Response</h6>
                    <div>
                        ${statusBadge}
                        ${timeBadge}
                    </div>
                </div>
                ${formatJSON(result.data)}
            `;
        } else {
            responseContent = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6>Error</h6>
                    <div>
                        ${statusBadge}
                        ${timeBadge}
                    </div>
                </div>
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
    }
    
    // Display error
    function displayError(message) {
        const responseDiv = document.createElement('div');
        responseDiv.className = 'response-error response-animation';
        responseDiv.innerHTML = `
            <h6>Error</h6>
            <div class="json-response">${message}</div>
        `;
        responseContainer.innerHTML = '';
        responseContainer.appendChild(responseDiv);
    }
    
    // Show error message
    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // Show loading state
    function showLoading() {
        const submitBtn = quickTestForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
    }
    
    // Hide loading state
    function hideLoading() {
        const submitBtn = quickTestForm.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Send Request';
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
        const viewer = container.querySelector('.json-viewer');
        
        // Extract the original JSON data from the response
        const responseContainer = container.closest('.response-animation');
        if (responseContainer) {
            // Find the original data from the response
            const responseData = responseContainer.dataset.responseData;
            if (responseData) {
                try {
                    const jsonData = JSON.parse(responseData);
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
    
    // Build request data based on method and URL
    function buildRequestData(method, url) {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
        
        let body = null;
        let finalUrl = url;
        
        // Add query parameters for GET requests
        if (method === 'GET') {
            const queryParams = new URLSearchParams();
            
            if (url.includes('/results')) {
                const category = document.getElementById('test-category').value;
                const limit = document.getElementById('test-limit').value;
                const minScore = document.getElementById('test-min-score').value;
                
                if (category) queryParams.append('category', category);
                if (limit) queryParams.append('limit', limit);
                if (minScore) queryParams.append('min_score', minScore);
            }
            
            if (url.includes('/process-comprehensive')) {
                const priority = document.getElementById('test-priority').value;
                if (priority) queryParams.append('priority', priority);
            }
            
            if (queryParams.toString()) {
                finalUrl += '?' + queryParams.toString();
            }
        }
        
        // Add body for POST requests
        if (method === 'POST') {
            if (url.includes('/generate-recommendations')) {
                const prompt = document.getElementById('test-prompt').value;
                body = JSON.stringify({
                    prompt: prompt || null
                });
            } else if (url.includes('/process-comprehensive')) {
                const priority = document.getElementById('test-priority').value;
                body = JSON.stringify({
                    priority: parseInt(priority) || 5
                });
            }
        }
        
        return { headers, body, finalUrl };
    }
    
    // Load endpoint form based on selection
    window.loadEndpointForm = function() {
        const endpointValue = document.getElementById('test-endpoint').value;
        const formDiv = document.getElementById('endpoint-form');
        const submitBtn = document.getElementById('submit-btn');
        
        if (!endpointValue) {
            formDiv.style.display = 'none';
            submitBtn.disabled = true;
            return;
        }
        
        const [method, url] = endpointValue.split(':');
        formDiv.style.display = 'block';
        submitBtn.disabled = false;
        
        // Show/hide relevant fields based on endpoint
        const userIdField = document.getElementById('test-user-id').parentElement;
        const priorityField = document.getElementById('priority-field');
        const categoryField = document.getElementById('category-field');
        const limitField = document.getElementById('limit-field');
        const minScoreField = document.getElementById('min-score-field');
        const promptField = document.getElementById('prompt-field');
        
        // Reset all fields
        [priorityField, categoryField, limitField, minScoreField, promptField].forEach(field => {
            field.style.display = 'none';
        });
        
        // Show user ID field for user endpoints
        if (url.includes('{user_id}')) {
            userIdField.style.display = 'block';
        } else {
            userIdField.style.display = 'none';
        }
        
        // Show specific fields based on endpoint
        if (url.includes('/process-comprehensive')) {
            priorityField.style.display = 'block';
        }
        
        if (url.includes('/results')) {
            categoryField.style.display = 'block';
            limitField.style.display = 'block';
            minScoreField.style.display = 'block';
        }
        
        if (url.includes('/generate-recommendations')) {
            promptField.style.display = 'block';
        }
    };
    
    // Test endpoint function (called from template)
    window.testEndpoint = function(method, path, parameters) {
        // Find the matching option in the dropdown
        const endpointSelect = document.getElementById('test-endpoint');
        const optionValue = `${method}:${path}`;
        
        // Set the dropdown value
        endpointSelect.value = optionValue;
        
        // Load the form
        loadEndpointForm();
        
        // Focus on the form
        endpointSelect.focus();
        
        // Scroll to the form
        document.getElementById('quick-test-form').scrollIntoView({ behavior: 'smooth' });
    };
});