/**
 * BlueAbel AIOS - Main JavaScript
 * Handles UI interactions and AJAX requests
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initializeComponents();
    
    // Auto-hide alerts after 5 seconds
    initializeAlerts();
    
    // Check API status on page load
    checkApiStatus();
});

/**
 * Initialize UI components
 */
function initializeComponents() {
    // Initialize tabs if they exist
    const tabButtons = document.querySelectorAll('.tab-button');
    if (tabButtons.length > 0) {
        initializeTabs();
    }
    
    // Initialize dropdowns if they exist
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    if (dropdowns.length > 0) {
        initializeDropdowns();
    }
}

/**
 * Initialize tab functionality
 */
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the tab to show
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            // Add active class to current button and tab
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

/**
 * Initialize dropdown functionality
 */
function initializeDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            e.preventDefault();
            
            const dropdownMenu = this.nextElementSibling;
            
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                if (menu !== dropdownMenu) {
                    menu.classList.remove('show');
                }
            });
            
            // Toggle current dropdown
            dropdownMenu.classList.toggle('show');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.matches('.dropdown-toggle')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });
}

/**
 * Auto-hide alerts after delay
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });
}

/**
 * Check API status
 */
function checkApiStatus() {
    const apiStatusIndicator = document.getElementById('apiStatusIndicator');
    
    if (!apiStatusIndicator) return;
    
    fetch('/api-status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'online') {
                apiStatusIndicator.innerHTML = '<span class="status-dot online"></span><span class="status-text">Online</span>';
            } else {
                apiStatusIndicator.innerHTML = '<span class="status-dot offline"></span><span class="status-text">Offline</span>';
            }
        })
        .catch(error => {
            apiStatusIndicator.innerHTML = '<span class="status-dot offline"></span><span class="status-text">Offline</span>';
        });
    
    // Update status every 30 seconds
    setTimeout(checkApiStatus, 30000);
}

/**
 * Format date strings consistently
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

/**
 * Handle AJAX form submission
 */
function submitFormAsync(formElement, successCallback, errorCallback) {
    formElement.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(formElement);
        const submitButton = formElement.querySelector('button[type="submit"]');
        
        // Disable submit button and show loading state
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = 'Processing...';
        }
        
        fetch(formElement.action, {
            method: formElement.method,
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (typeof successCallback === 'function') {
                successCallback(data);
            }
        })
        .catch(error => {
            if (typeof errorCallback === 'function') {
                errorCallback(error);
            } else {
                console.error('Error submitting form:', error);
                alert('An error occurred while submitting the form. Please try again.');
            }
        })
        .finally(() => {
            // Re-enable submit button
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Submit';
            }
        });
    });
}