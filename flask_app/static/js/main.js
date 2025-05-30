/**
 * Nigerian E-commerce Customer Support Agent
 * Main JavaScript file for dynamic functionality
 * Includes real-time updates, analytics, and Nigerian market features
 */

// Global variables
let currentUser = 'anonymous';
let refreshInterval = null;
let chartInstances = {};

// Nigerian market-specific data
const NIGERIAN_STATES = [
    'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
    'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Gombe', 'Imo',
    'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 'Lagos',
    'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers',
    'Sokoto', 'Taraba', 'Yobe', 'Zamfara', 'FCT'
];

const PAYMENT_METHODS = {
    'Pay on Delivery': { color: '#1e3a8a', icon: '🚚' },
    'Bank Transfer': { color: '#008751', icon: '🏦' },
    'Card': { color: '#fbbf24', icon: '💳' },
    'RaqibTechPay': { color: '#14b8a6', icon: '📱' }
};

const ORDER_STATUSES = {
    'Pending': { color: '#0dcaf0', icon: '⏳' },
    'Processing': { color: '#ffc107', icon: '⚙️' },
    'Delivered': { color: '#198754', icon: '✅' },
    'Returned': { color: '#dc3545', icon: '↩️' }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
    setupEventListeners();
    startRealTimeUpdates();
    loadInitialData();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('  Nigerian Customer Support Agent - Initializing...');

    // Generate session ID for user tracking
    currentUser = generateSessionId();

    // Initialize tooltips and popovers
    initializeBootstrapComponents();

    // Set up keyboard shortcuts
    setupKeyboardShortcuts();

    // Initialize Nigerian currency formatter
    setupCurrencyFormatter();

    console.log('✅ Application initialized successfully');
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Tab switching
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', handleTabSwitch);
    });

    // Filter inputs
    const searchInput = document.getElementById('customerSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearchInput, 300));
    }

    // State and tier filters
    const stateFilter = document.getElementById('stateFilter');
    const tierFilter = document.getElementById('tierFilter');

    if (stateFilter) {
        stateFilter.addEventListener('change', handleFilterChange);
    }

    if (tierFilter) {
        tierFilter.addEventListener('change', handleFilterChange);
    }

    // Window resize handler for charts
    window.addEventListener('resize', debounce(handleWindowResize, 250));

    // Visibility change handler for performance optimization
    document.addEventListener('visibilitychange', handleVisibilityChange);

    console.log('📡 Event listeners configured');
}

/**
 * Start real-time updates
 */
function startRealTimeUpdates() {
    // Update every 30 seconds
    refreshInterval = setInterval(() => {
        if (!document.hidden) {
            updateRealTimeMetrics();
        }
    }, 30000);

    console.log('🔄 Real-time updates started');
}

/**
 * Load initial data
 */
function loadInitialData() {
    // Load customers on Customer Profiles tab
    if (document.getElementById('customersTable')) {
        loadCustomers();
    }

    // Load analytics data
    loadUsageAnalytics();
    loadBusinessAnalytics();

    // Initialize charts
    setTimeout(initializeCharts, 1000);
}

/**
 * Customer management functions
 */
function loadCustomers() {
    const loading = document.getElementById('customersLoading');
    const search = document.getElementById('customerSearch')?.value || '';
    const state = document.getElementById('stateFilter')?.value || 'all';
    const tier = document.getElementById('tierFilter')?.value || 'all';

    if (loading) {
        loading.style.display = 'block';
        loading.innerHTML = `
            <div class="nigeria-loading me-2"></div>
            <div class="spinner-border text-success" role="status"></div>
            <div class="mt-2">Loading Nigerian customers...</div>
        `;
    }

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (state !== 'all') params.append('state', state);
    if (tier !== 'all') params.append('tier', tier);

    fetch(`/api/customers?${params}`)
        .then(response => response.json())
        .then(data => {
            if (loading) loading.style.display = 'none';

            if (data.success) {
                displayCustomers(data.data);
                updateCustomerStats(data.data);
            } else {
                showErrorMessage('Failed to load customers');
            }
        })
        .catch(error => {
            if (loading) loading.style.display = 'none';
            console.error('Error loading customers:', error);
            showErrorMessage('Connection error while loading customers');
        });
}

/**
 * Display customers in table with Nigerian styling
 */
function displayCustomers(customers) {
    const tbody = document.getElementById('customersTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (customers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <i class="bi bi-inbox display-4 text-muted"></i>
                    <p class="mt-2 text-muted">No customers found</p>
                </td>
            </tr>
        `;
        return;
    }

    customers.forEach((customer, index) => {
        const row = document.createElement('tr');
        row.className = 'customer-row';
        row.style.animationDelay = `${index * 0.05}s`;

        const stateClass = getStateClass(customer.state);
        const tierBadge = getTierBadge(customer.account_tier);

        row.innerHTML = `
            <td class="fw-bold">${customer.customer_id}</td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar-circle me-2">${customer.name.charAt(0).toUpperCase()}</div>
                    <div>
                        <div class="fw-semibold">${escapeHtml(customer.name)}</div>
                    </div>
                </div>
            </td>
            <td>${escapeHtml(customer.email)}</td>
            <td>
                <span class="badge ${stateClass} rounded-pill">
                    📍 ${customer.state}
                </span>
            </td>
            <td class="text-muted">${escapeHtml(customer.lga)}</td>
            <td>${tierBadge}</td>
            <td>
                <a href="tel:${customer.phone}" class="text-decoration-none">
                    📞 ${customer.phone}
                </a>
            </td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary"
                            onclick="viewCustomerDetails(${customer.customer_id})"
                            title="View Details">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-success"
                            onclick="editCustomer(${customer.customer_id})"
                            title="Edit Customer">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-info"
                            onclick="sendQuickMessage('Show orders for customer ${customer.customer_id}')"
                            title="View Orders">
                        <i class="bi bi-cart"></i>
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(row);
    });

    // Apply table styling
    const table = document.getElementById('customersTable');
    if (table) {
        table.classList.add('table-nigeria');
    }
}

/**
 * Analytics and Chart Functions
 */
function loadUsageAnalytics() {
    fetch('/api/analytics?type=usage')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateUsageMetrics(data.data);
                createUsageCharts(data.data);
            }
        })
        .catch(error => {
            console.error('Error loading usage analytics:', error);
        });
}

function loadBusinessAnalytics() {
    fetch('/api/analytics?type=summary')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                createBusinessCharts(data.data);
                updateBusinessMetrics(data.data);
            }
        })
        .catch(error => {
            console.error('Error loading business analytics:', error);
        });
}

function createBusinessCharts(data) {
    // Customer Distribution Chart with Nigerian colors
    if (data.customer_distribution && document.getElementById('customerDistributionChart')) {
        const ctx = document.getElementById('customerDistributionChart').getContext('2d');

        // Destroy existing chart
        if (chartInstances.customerDistribution) {
            chartInstances.customerDistribution.destroy();
        }

        const stateLabels = data.customer_distribution.map(item => item.state);
        const customerCounts = data.customer_distribution.map(item => item.customer_count);

        chartInstances.customerDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: stateLabels.slice(0, 10),
                datasets: [{
                    data: customerCounts.slice(0, 10),
                    backgroundColor: generateNigerianColors(10),
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '  Customer Distribution by State'
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} customers (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Revenue Chart with Naira formatting
    if (data.revenue_by_state && document.getElementById('revenueChart')) {
        const ctx = document.getElementById('revenueChart').getContext('2d');

        if (chartInstances.revenue) {
            chartInstances.revenue.destroy();
        }

        const revenueLabels = data.revenue_by_state.map(item => item.state);
        const revenueAmounts = data.revenue_by_state.map(item => parseFloat(item.total_revenue));

        chartInstances.revenue = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: revenueLabels.slice(0, 10),
                datasets: [{
                    label: 'Revenue (₦)',
                    data: revenueAmounts.slice(0, 10),
                    backgroundColor: 'rgba(0, 135, 81, 0.8)',
                    borderColor: 'rgba(0, 135, 81, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '💰 Revenue by State (Nigerian Naira)'
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${context.label}: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Utility Functions
 */
function generateSessionId() {
    return 'user_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

function generateNigerianColors(count) {
    const colors = [
        '#008751', '#1e3a8a', '#fbbf24', '#dc2626', '#14b8a6',
        '#9333ea', '#ea580c', '#059669', '#7c3aed', '#0891b2'
    ];

    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatTime(date) {
    return new Intl.DateTimeFormat('en-NG', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }).format(date);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function getStateClass(state) {
    const stateClasses = {
        'Lagos': 'badge-lagos',
        'Abuja': 'badge-abuja',
        'Kano': 'badge-kano',
        'Rivers': 'badge-rivers'
    };
    return stateClasses[state] || 'bg-secondary';
}

function getTierBadge(tier) {
    const tierConfig = {
        'Bronze': { color: 'secondary', icon: '🥉' },
        'Silver': { color: 'info', icon: '🥈' },
        'Gold': { color: 'warning', icon: '🥇' },
        'Platinum': { color: 'success', icon: '💎' }
    };

    const config = tierConfig[tier] || tierConfig['Bronze'];
    return `<span class="badge bg-${config.color} rounded-pill">
                ${config.icon} ${tier}
            </span>`;
}

// Export functions for global access
window.sendQuickMessage = function (message) {
    document.getElementById('chatInput').value = message;
};
window.handleChatKeyPress = function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
    }
};
window.loadCustomers = loadCustomers;
window.viewCustomerDetails = function (customerId) {
    console.log(`Viewing customer details for ID: ${customerId}`);
    // Customer details viewing will be handled by the integrated system
};

console.log('  Nigerian Customer Support Agent - JavaScript loaded successfully');
