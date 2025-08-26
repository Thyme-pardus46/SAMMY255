// Main JavaScript for Field Supervision Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeNotifications();
    initializeFormValidation();
    initializeFileUploads();
    initializeTooltips();
    initializeModals();
    initializeDataTables();
});

// Notification System
function initializeNotifications() {
    // Load notifications count
    loadNotificationCount();
    
    // Set up periodic refresh
    setInterval(loadNotificationCount, 30000); // Refresh every 30 seconds
}

function loadNotificationCount() {
    // This would typically make an AJAX call to get unread notification count
    // For now, we'll simulate it
    const notificationBadge = document.getElementById('notification-count');
    if (notificationBadge) {
        // Simulate getting notification count
        const count = Math.floor(Math.random() * 5); // Random for demo
        notificationBadge.textContent = count;
        notificationBadge.style.display = count > 0 ? 'block' : 'none';
    }
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Password strength validation
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (input.name === 'password') {
            input.addEventListener('input', validatePasswordStrength);
        }
    });
}

function validatePasswordStrength(event) {
    const password = event.target.value;
    const strengthIndicator = document.getElementById('password-strength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    let feedback = [];
    
    // Check length
    if (password.length >= 8) strength++;
    else feedback.push('At least 8 characters');
    
    // Check for uppercase
    if (/[A-Z]/.test(password)) strength++;
    else feedback.push('One uppercase letter');
    
    // Check for lowercase
    if (/[a-z]/.test(password)) strength++;
    else feedback.push('One lowercase letter');
    
    // Check for numbers
    if (/\d/.test(password)) strength++;
    else feedback.push('One number');
    
    // Check for special characters
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
    else feedback.push('One special character');
    
    // Update UI
    const strengthClasses = ['weak', 'fair', 'good', 'strong'];
    const strengthTexts = ['Weak', 'Fair', 'Good', 'Strong'];
    
    strengthIndicator.className = `password-strength ${strengthClasses[Math.min(strength - 1, 3)]}`;
    strengthIndicator.textContent = strength > 0 ? strengthTexts[Math.min(strength - 1, 3)] : 'Too weak';
    
    if (feedback.length > 0) {
        strengthIndicator.title = 'Missing: ' + feedback.join(', ');
    }
}

// File Upload Handling
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const uploadArea = input.closest('.file-upload-area');
        if (uploadArea) {
            setupDragAndDrop(uploadArea, input);
        }
        
        input.addEventListener('change', handleFileSelect);
    });
}

function setupDragAndDrop(uploadArea, fileInput) {
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect({ target: fileInput });
        }
    });
    
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
}

function handleFileSelect(event) {
    const files = event.target.files;
    const fileList = event.target.parentNode.querySelector('.file-list');
    
    if (fileList) {
        fileList.innerHTML = '';
        
        Array.from(files).forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item d-flex justify-content-between align-items-center p-2 border rounded mb-2';
            
            fileItem.innerHTML = `
                <div class="file-info d-flex align-items-center">
                    <i class="bi bi-file-earmark me-2"></i>
                    <span class="file-name">${file.name}</span>
                    <span class="file-size text-muted ms-2">(${formatFileSize(file.size)})</span>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(this, ${index})">
                    <i class="bi bi-x"></i>
                </button>
            `;
            
            fileList.appendChild(fileItem);
        });
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function removeFile(button, index) {
    button.closest('.file-item').remove();
    // Note: Removing from FileList is not directly possible in most browsers
    // You would need to implement a custom solution for this
}

// Initialize Bootstrap Tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => 
        new bootstrap.Tooltip(tooltipTriggerEl)
    );
}

// Initialize Modals
function initializeModals() {
    // Auto-focus first input in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });
}

// Initialize DataTables (if jQuery is available)
function initializeDataTables() {
    if (typeof $ !== 'undefined' && $.fn.DataTable) {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 25,
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        });
    }
}

// Utility Functions
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container') || document.body;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    if (duration > 0) {
        setTimeout(() => {
            alert.remove();
        }, duration);
    }
}

function formatDate(date, format = 'short') {
    const options = format === 'short' ? 
        { year: 'numeric', month: 'short', day: 'numeric' } :
        { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    
    return new Date(date).toLocaleDateString('en-US', options);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Status Badge Helper
function getStatusBadge(status) {
    const statusMap = {
        'pending': { class: 'status-pending', icon: 'clock', text: 'Pending' },
        'approved': { class: 'status-approved', icon: 'check-circle', text: 'Approved' },
        'in_progress': { class: 'status-in-progress', icon: 'arrow-right-circle', text: 'In Progress' },
        'completed': { class: 'status-completed', icon: 'check-circle-fill', text: 'Completed' },
        'rejected': { class: 'status-rejected', icon: 'x-circle', text: 'Rejected' }
    };
    
    const statusInfo = statusMap[status] || { class: 'status-pending', icon: 'question-circle', text: status };
    
    return `<span class="status-badge ${statusInfo.class}">
                <i class="bi bi-${statusInfo.icon} me-1"></i>
                ${statusInfo.text}
            </span>`;
}

// AJAX Helper Functions
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    return fetch(url, config)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showAlert('An error occurred. Please try again.', 'danger');
            throw error;
        });
}

// Form Submission Helper
function submitForm(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    const loadingButton = form.querySelector('button[type="submit"]');
    const originalText = loadingButton.innerHTML;
    
    loadingButton.disabled = true;
    loadingButton.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
    
    fetch(form.action, {
        method: form.method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (successCallback) successCallback(data);
            else showAlert(data.message || 'Success!', 'success');
        } else {
            if (errorCallback) errorCallback(data);
            else showAlert(data.message || 'An error occurred.', 'danger');
        }
    })
    .catch(error => {
        console.error('Form submission error:', error);
        if (errorCallback) errorCallback({ message: 'Network error occurred.' });
        else showAlert('Network error occurred.', 'danger');
    })
    .finally(() => {
        loadingButton.disabled = false;
        loadingButton.innerHTML = originalText;
    });
}

// Export functions for global use
window.FieldSupervision = {
    showAlert,
    formatDate,
    confirmAction,
    getStatusBadge,
    makeRequest,
    submitForm
};