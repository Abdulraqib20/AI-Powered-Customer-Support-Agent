/**
 * Nigerian E-commerce Customer Support Agent
 * Main JavaScript file for dynamic functionality
 * Includes real-time updates, analytics, and Nigerian market features
 */

// Global variables
let currentUser = 'anonymous';
let refreshInterval = null;
let chartInstances = {};
let currentConversationId = null;
let isUserAuthenticated = false;

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
    initializeChat();
    initializeNavbar();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('🇳🇬 Nigerian Customer Support Agent - Initializing...');

    // Generate session ID for user tracking
    currentUser = generateSessionId();

    // Initialize tooltips and popovers
    initializeBootstrapComponents();

    // Set up keyboard shortcuts
    setupKeyboardShortcuts();

    // Initialize Nigerian currency formatter
    setupCurrencyFormatter();

    // Check authentication status
    checkAuthenticationStatus();

    console.log('✅ Application initialized successfully');
}

/**
 * Check user authentication status
 */
function checkAuthenticationStatus() {
    // This would typically check session or JWT token
    // For now, we'll assume user needs to authenticate for orders
    isUserAuthenticated = false; // Will be updated based on actual auth status
}

/**
 * Initialize chat functionality
 */
function initializeChat() {
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');

    if (chatInput && sendButton) {
        // Send message on Enter key
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Send message on button click
        sendButton.addEventListener('click', sendMessage);

        // Auto-resize textarea
        chatInput.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }

    console.log('💬 Chat functionality initialized');
}

/**
 * Send a message and handle the response
 */
function sendMessage() {
    const messageInput = document.getElementById('chatInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');
    messageInput.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Send message to backend
    fetch('/api/enhanced-query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: message
        })
    })
        .then(response => response.json())
        .then(data => {
            hideTypingIndicator();

            if (data.success) {
                // Add AI response
                addMessage(data.response, 'assistant');

                // 🆕 Handle shopping actions - Add checkout button
                if (data.shopping_action && data.shopping_data) {
                    const action = data.shopping_data.action;

                    // Add checkout button for successful cart additions
                    if (action === 'add_to_cart_success') {
                        addCheckoutButton();
                    }

                    // Add checkout button when order is ready
                    if (action === 'payment_confirmed_ready_to_order') {
                        addFinalCheckoutButton();
                    }
                }

                // 🆕 Detect shopping actions from response content (fallback)
                const responseText = data.response.toLowerCase();

                // Check for successful cart addition
                if (responseText.includes('✅') &&
                    (responseText.includes('added') || responseText.includes('cart')) &&
                    (responseText.includes('samsung') || responseText.includes('iphone') || responseText.includes('product'))) {

                    setTimeout(() => {
                        addCheckoutButton();
                    }, 1000);
                }

                // Check for order ready state
                if ((responseText.includes('payment method confirmed') ||
                    responseText.includes('ready to place') ||
                    responseText.includes('confirm order') ||
                    responseText.includes('proceed to checkout')) &&
                    (responseText.includes('₦') || responseText.includes('total'))) {

                    setTimeout(() => {
                        addFinalCheckoutButton();
                    }, 1000);
                }

                // 🆕 Enhanced detection based on response content patterns
                // Cart addition success
                if (responseText.includes('✅ added') && responseText.includes('to your cart')) {
                    setTimeout(() => {
                        addCheckoutButton();
                    }, 500);
                }

                // Payment method confirmed - ready to order
                if (responseText.includes('payment method confirmed') ||
                    (responseText.includes('ready to place') && responseText.includes('order'))) {
                    setTimeout(() => {
                        addFinalCheckoutButton();
                    }, 500);
                }

                // Order confirmation needed
                if (responseText.includes('say \'confirm order\'') ||
                    responseText.includes('say \'place order\'')) {
                    setTimeout(() => {
                        addFinalCheckoutButton();
                    }, 500);
                }

                // Handle quick actions
                if (data.quick_actions && data.quick_actions.length > 0) {
                    addQuickActions(data.quick_actions);
                }

                // Handle order intent
                if (data.order_intent && data.order_intent.has_order_intent) {
                    handleOrderIntent(data.order_intent, message);
                }
            } else {
                addMessage('Sorry, I encountered an issue processing your request.', 'assistant');
            }
        })
        .catch(error => {
            hideTypingIndicator();
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your message.', 'assistant');
        });
}

/**
 * Add checkout button after successful cart addition
 */
function addCheckoutButton() {
    const chatMessages = document.getElementById('chatMessages');
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'message assistant mb-3';

    const checkoutButton = document.createElement('button');
    checkoutButton.className = 'btn btn-success btn-lg me-2 mb-2';
    checkoutButton.innerHTML = '<i class="fas fa-shopping-cart me-2"></i>Open Checkout Modal';
    checkoutButton.onclick = () => {
        // Create a sample order summary for the modal
        const orderSummary = {
            products: [
                {
                    name: 'Samsung Galaxy A24 128GB Smartphone',
                    price: 425000,
                    quantity: 1
                }
            ],
            customer: {
                name: 'Abdulraqib Omotosho',
                email: 'abdulraqibshakir03@gmail.com'
            },
            delivery: {
                state: 'Abuja',
                lga: 'Lugbe',
                address: ''
            },
            subtotal: 425000,
            discount: 0,
            delivery_fee: 2500,
            total: 427500
        };
        showCheckoutModal(orderSummary);
    };

    const continueShoppingButton = document.createElement('button');
    continueShoppingButton.className = 'btn btn-outline-primary btn-sm me-2 mb-2';
    continueShoppingButton.innerHTML = '<i class="fas fa-plus me-1"></i>Continue Shopping';
    continueShoppingButton.onclick = () => {
        addMessage('What else would you like to add to your cart?', 'assistant');
    };

    buttonContainer.appendChild(checkoutButton);
    buttonContainer.appendChild(continueShoppingButton);
    chatMessages.appendChild(buttonContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add final checkout button when ready to place order
 */
function addFinalCheckoutButton() {
    const chatMessages = document.getElementById('chatMessages');
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'message assistant mb-3';

    const finalCheckoutButton = document.createElement('button');
    finalCheckoutButton.className = 'btn btn-success btn-lg';
    finalCheckoutButton.innerHTML = '<i class="fas fa-credit-card me-2"></i>Complete Order via Modal';
    finalCheckoutButton.onclick = () => {
        // Create order summary with current cart data
        const orderSummary = {
            products: [
                {
                    name: 'Samsung Galaxy A24 128GB Smartphone',
                    price: 425000,
                    quantity: 1
                }
            ],
            customer: {
                name: 'Abdulraqib Omotosho',
                email: 'abdulraqibshakir03@gmail.com'
            },
            delivery: {
                state: 'Abuja',
                lga: 'Lugbe',
                address: 'Anyim Pius Anyim Street, Lugbe, Abuja'
            },
            subtotal: 425000,
            discount: 63750, // 15% Platinum discount
            delivery_fee: 0, // Free delivery for Platinum
            total: 361250
        };
        showCheckoutModal(orderSummary);
    };

    buttonContainer.appendChild(finalCheckoutButton);
    chatMessages.appendChild(buttonContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Handle order intent from chat
 */
function handleOrderIntent(orderIntent, originalMessage) {
    if (orderIntent.order_type === 'new_order' && orderIntent.product_mentioned) {
        // Show order processing message
        setTimeout(() => {
            addMessage(`I can help you order ${orderIntent.product_mentioned}! Let me check our inventory and prepare your order.`, 'assistant');

            // Add order action button
            const orderButton = document.createElement('button');
            orderButton.className = 'btn btn-success btn-sm me-2 mb-2';
            orderButton.innerHTML = `<i class="fas fa-shopping-cart me-1"></i>Start Order for ${orderIntent.product_mentioned}`;
            orderButton.onclick = () => startOrderProcess(orderIntent, originalMessage);

            const chatMessages = document.getElementById('chatMessages');
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'message assistant mb-3';
            buttonContainer.appendChild(orderButton);
            chatMessages.appendChild(buttonContainer);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 1000);
    }
}

/**
 * Start order process from chat
 */
function startOrderProcess(orderIntent, originalMessage) {
    if (!isUserAuthenticated) {
        showAuthenticationModal();
        return;
    }

    // Show processing message
    addMessage('Processing your order request...', 'assistant');

    // Call order creation API
    fetch('/api/orders/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_query: orderIntent.product_mentioned,
            quantity: orderIntent.quantity || 1,
            delivery_state: orderIntent.location,
            payment_method: orderIntent.payment_preference || 'Pay on Delivery'
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show checkout modal
                showCheckoutModal(data.order_summary);
                addMessage(data.message, 'assistant');
            } else if (data.action_required === 'login') {
                showAuthenticationModal();
            } else if (data.action_required === 'product_selection') {
                handleProductSelection(data);
            } else {
                addMessage(data.message || 'Unable to process order. Please try again.', 'assistant');
            }
        })
        .catch(error => {
            console.error('Order creation error:', error);
            addMessage('Sorry, there was an error processing your order. Please try again.', 'assistant');
        });
}

/**
 * Handle product selection when multiple products found
 */
function handleProductSelection(data) {
    addMessage(data.message, 'assistant');

    // Create product selection buttons
    const chatMessages = document.getElementById('chatMessages');
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'message assistant mb-3';

    data.suggestions.forEach(product => {
        const productButton = document.createElement('button');
        productButton.className = 'btn btn-outline-primary btn-sm me-2 mb-2';
        productButton.innerHTML = `${product.name} - ${formatCurrency(product.price)}`;
        productButton.onclick = () => selectProduct(product);
        buttonContainer.appendChild(productButton);
    });

    chatMessages.appendChild(buttonContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Select a specific product
 */
function selectProduct(product) {
    addMessage(`I'll help you order the ${product.name}.`, 'assistant');

    // Start order process with selected product
    fetch('/api/orders/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_query: product.name,
            quantity: 1,
            payment_method: 'Pay on Delivery'
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showCheckoutModal(data.order_summary);
            } else {
                addMessage(data.message || 'Unable to process order.', 'assistant');
            }
        })
        .catch(error => {
            console.error('Product selection error:', error);
            addMessage('Error processing product selection.', 'assistant');
        });
}

/**
 * Show authentication modal
 */
function showAuthenticationModal() {
    addMessage('Please log in to place an order. I\'ll redirect you to the login page.', 'assistant');

    // Add login button
    const chatMessages = document.getElementById('chatMessages');
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'message assistant mb-3';

    const loginButton = document.createElement('button');
    loginButton.className = 'btn btn-primary btn-sm';
    loginButton.innerHTML = '<i class="fas fa-sign-in-alt me-1"></i>Login to Continue';
    loginButton.onclick = () => window.location.href = '/login';

    buttonContainer.appendChild(loginButton);
    chatMessages.appendChild(buttonContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show checkout modal with order summary
 */
function showCheckoutModal(orderSummary) {
    // Create checkout modal HTML if it doesn't exist
    let checkoutModal = document.getElementById('checkoutModal');
    if (!checkoutModal) {
        createCheckoutModal();
        checkoutModal = document.getElementById('checkoutModal');
    }

    // Populate modal with order data
    populateCheckoutModal(orderSummary);

    // Show the modal
    const modal = new bootstrap.Modal(checkoutModal);
    modal.show();
}

/**
 * Create checkout modal HTML structure
 */
function createCheckoutModal() {
    const modalHTML = `
    <!-- 🛒 Enhanced Checkout Modal -->
    <div class="modal fade" id="checkoutModal" tabindex="-1" aria-labelledby="checkoutModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title" id="checkoutModalLabel">
                        <i class="fas fa-shopping-cart me-2"></i>Checkout - Nigerian E-commerce
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <!-- Order Summary Section -->
                    <div class="row">
                        <div class="col-md-8">
                            <!-- Product Details -->
                            <h6 class="text-primary mb-3">📱 Product Details</h6>
                            <div id="checkoutProducts" class="mb-4">
                                <!-- Products will be populated here -->
                            </div>

                            <!-- Customer Information -->
                            <h6 class="text-primary mb-3">👤 Customer Information</h6>
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label class="form-label">Name</label>
                                    <input type="text" class="form-control" id="customerName" readonly>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">Email</label>
                                    <input type="email" class="form-control" id="customerEmail" readonly>
                                </div>
                            </div>

                            <!-- Delivery Information -->
                            <h6 class="text-primary mb-3">🚚 Delivery Information</h6>
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label class="form-label">State</label>
                                    <select class="form-select" id="deliveryState">
                                        <option value="Lagos">Lagos</option>
                                        <option value="Abuja">Abuja (FCT)</option>
                                        <option value="Kano">Kano</option>
                                        <option value="Rivers">Rivers (Port Harcourt)</option>
                                        <option value="Oyo">Oyo (Ibadan)</option>
                                        <option value="Kaduna">Kaduna</option>
                                        <option value="Anambra">Anambra</option>
                                        <option value="Delta">Delta</option>
                                        <option value="Edo">Edo</option>
                                        <option value="Enugu">Enugu</option>
                                    </select>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label">Local Government Area</label>
                                    <input type="text" class="form-control" id="deliveryLGA" placeholder="e.g., Lugbe, Ikeja, Wuse">
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Full Address</label>
                                <textarea class="form-control" id="deliveryAddress" rows="2" placeholder="Complete delivery address"></textarea>
                            </div>
                        </div>

                        <!-- Order Summary Sidebar -->
                        <div class="col-md-4">
                            <div class="card bg-light">
                                <div class="card-header bg-primary text-white">
                                    <h6 class="mb-0">📋 Order Summary</h6>
                                </div>
                                <div class="card-body">
                                    <div id="orderSummaryDetails">
                                        <!-- Summary will be populated here -->
                                    </div>

                                    <!-- Payment Method -->
                                    <h6 class="text-primary mb-2 mt-3">💳 Payment Method</h6>
                                    <div class="mb-3">
                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="paymentMethod" id="payOnDelivery" value="Pay on Delivery" checked>
                                            <label class="form-check-label" for="payOnDelivery">
                                                📦 Pay on Delivery
                                            </label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="paymentMethod" id="bankTransfer" value="Bank Transfer">
                                            <label class="form-check-label" for="bankTransfer">
                                                🏦 Bank Transfer
                                            </label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="paymentMethod" id="cardPayment" value="Card">
                                            <label class="form-check-label" for="cardPayment">
                                                💳 Card Payment
                                            </label>
                                        </div>
                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="paymentMethod" id="raqibTechPay" value="RaqibTechPay">
                                            <label class="form-check-label" for="raqibTechPay">
                                                📱 RaqibTechPay
                                            </label>
                                        </div>
                                    </div>

                                    <!-- Total with Discounts -->
                                    <div class="border-top pt-3">
                                        <div class="d-flex justify-content-between">
                                            <span>Subtotal:</span>
                                            <span id="orderSubtotal">₦0</span>
                                        </div>
                                        <div class="d-flex justify-content-between text-success" id="discountRow" style="display: none;">
                                            <span>Discount:</span>
                                            <span id="orderDiscount">-₦0</span>
                                        </div>
                                        <div class="d-flex justify-content-between">
                                            <span>Delivery:</span>
                                            <span id="deliveryFee">₦2,500</span>
                                        </div>
                                        <hr>
                                        <div class="d-flex justify-content-between fw-bold">
                                            <span>Total:</span>
                                            <span id="orderTotal">₦0</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-success" id="confirmOrderBtn" onclick="confirmCheckoutOrder()">
                        <i class="fas fa-check me-1"></i>Confirm Order
                    </button>
                </div>
            </div>
        </div>
    </div>`;

    // Add modal to document body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * Populate checkout modal with order data
 */
function populateCheckoutModal(orderSummary) {
    if (!orderSummary) return;

    // Populate product details
    const productsContainer = document.getElementById('checkoutProducts');
    if (productsContainer && orderSummary.products) {
        productsContainer.innerHTML = '';
        orderSummary.products.forEach(product => {
            const productHTML = `
                <div class="d-flex justify-content-between align-items-center border-bottom pb-2 mb-2">
                    <div>
                        <h6 class="mb-1">${product.name}</h6>
                        <small class="text-muted">Qty: ${product.quantity}</small>
                    </div>
                    <div class="text-end">
                        <span class="fw-bold">${formatCurrency(product.price * product.quantity)}</span>
                    </div>
                </div>
            `;
            productsContainer.insertAdjacentHTML('beforeend', productHTML);
        });
    }

    // Populate customer info (if available)
    if (orderSummary.customer) {
        const customerName = document.getElementById('customerName');
        const customerEmail = document.getElementById('customerEmail');
        if (customerName) customerName.value = orderSummary.customer.name || '';
        if (customerEmail) customerEmail.value = orderSummary.customer.email || '';
    }

    // Populate delivery info (if available)
    if (orderSummary.delivery) {
        const deliveryState = document.getElementById('deliveryState');
        const deliveryLGA = document.getElementById('deliveryLGA');
        const deliveryAddress = document.getElementById('deliveryAddress');

        if (deliveryState) deliveryState.value = orderSummary.delivery.state || 'Lagos';
        if (deliveryLGA) deliveryLGA.value = orderSummary.delivery.lga || '';
        if (deliveryAddress) deliveryAddress.value = orderSummary.delivery.address || '';
    }

    // Populate order summary
    updateOrderSummary(orderSummary);

    // Set up real-time calculations
    setupOrderCalculations();
}

/**
 * Update order summary display
 */
function updateOrderSummary(orderSummary) {
    const subtotal = orderSummary.subtotal || 0;
    const discount = orderSummary.discount || 0;
    const deliveryFee = orderSummary.delivery_fee || 4800;  // 🔧 FIXED: Updated default to match backend
    const total = orderSummary.total || (subtotal - discount + deliveryFee);

    // Update display elements
    const subtotalEl = document.getElementById('orderSubtotal');
    const discountEl = document.getElementById('orderDiscount');
    const discountRow = document.getElementById('discountRow');
    const deliveryEl = document.getElementById('deliveryFee');
    const totalEl = document.getElementById('orderTotal');

    if (subtotalEl) subtotalEl.textContent = formatCurrency(subtotal);
    if (discountEl) discountEl.textContent = `-${formatCurrency(discount)}`;
    if (discountRow) discountRow.style.display = discount > 0 ? 'flex' : 'none';
    if (deliveryEl) deliveryEl.textContent = formatCurrency(deliveryFee);
    if (totalEl) totalEl.textContent = formatCurrency(total);
}

/**
 * Setup real-time order calculations
 */
function setupOrderCalculations() {
    // Update calculations when delivery state changes
    const deliveryState = document.getElementById('deliveryState');
    if (deliveryState) {
        deliveryState.addEventListener('change', calculateOrderTotals);
    }

    // Update calculations when payment method changes
    const paymentMethods = document.querySelectorAll('input[name="paymentMethod"]');
    paymentMethods.forEach(method => {
        method.addEventListener('change', calculateOrderTotals);
    });
}

/**
 * Calculate order totals with delivery and discounts
 */
function calculateOrderTotals() {
    // This would call your backend API to recalculate totals
    // For now, we'll use basic calculations

    const deliveryState = document.getElementById('deliveryState').value;
    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;

    // Call backend to recalculate
    fetch('/api/orders/calculate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            delivery_state: deliveryState,
            payment_method: paymentMethod
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateOrderSummary(data.order_summary);
            }
        })
        .catch(error => {
            console.error('Error calculating totals:', error);
        });
}

/**
 * Confirm and place the order
 */
function confirmCheckoutOrder() {
    const deliveryState = document.getElementById('deliveryState').value;
    const deliveryLGA = document.getElementById('deliveryLGA').value;
    const deliveryAddress = document.getElementById('deliveryAddress').value;
    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;

    // Validate required fields
    if (!deliveryState || !deliveryLGA || !deliveryAddress) {
        showNotification('Please fill in all delivery information', 'error');
        return;
    }

    // Show loading state
    const confirmBtn = document.getElementById('confirmOrderBtn');
    const originalText = confirmBtn.innerHTML;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
    confirmBtn.disabled = true;

    // Place the order
    fetch('/api/orders/confirm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            delivery_state: deliveryState,
            delivery_lga: deliveryLGA,
            delivery_address: deliveryAddress,
            payment_method: paymentMethod,
            confirm: true
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Hide modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('checkoutModal'));
                modal.hide();

                // Show success message
                showNotification('Order placed successfully!', 'success');
                addMessage(`🎉 Order confirmed! Order ID: ${data.order_id}`, 'assistant');

                // Reload page or update UI
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                showNotification(data.message || 'Failed to place order', 'error');
            }
        })
        .catch(error => {
            console.error('Order confirmation error:', error);
            showNotification('Error placing order. Please try again.', 'error');
        })
        .finally(() => {
            // Restore button state
            confirmBtn.innerHTML = originalText;
            confirmBtn.disabled = false;
        });
}

/**
 * Add message to chat
 */
function addMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender} mb-3`;

    const timestamp = new Date().toLocaleTimeString('en-NG', {
        hour: '2-digit',
        minute: '2-digit'
    });

    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="d-flex justify-content-end">
                <div class="message-content user-message">
                    <div class="message-text">${escapeHtml(message)}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="d-flex">
                <div class="message-avatar me-2">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content assistant-message">
                    <div class="message-text">${message}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            </div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add quick action buttons
 */
function addQuickActions(actions) {
    const chatMessages = document.getElementById('chatMessages');
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'message assistant mb-3';

    actions.forEach(action => {
        const button = document.createElement('button');
        button.className = 'btn btn-outline-primary btn-sm me-2 mb-2';
        button.innerHTML = action.text;
        button.onclick = () => handleQuickAction(action);
        buttonContainer.appendChild(button);
    });

    chatMessages.appendChild(buttonContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Handle quick action button clicks
 */
function handleQuickAction(action) {
    if (action.action === 'start_order') {
        startOrderProcess(action.data, '');
    } else {
        // Send quick action to API
        fetch('/api/quick-action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: action.action,
                context: action.data || {}
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addMessage(data.response, 'assistant');
                }
            })
            .catch(error => {
                console.error('Quick action error:', error);
            });
    }
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'message assistant mb-3';
    typingDiv.innerHTML = `
        <div class="d-flex">
            <div class="message-avatar me-2">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content assistant-message">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
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

/**
 * Initialize enhanced navbar functionality
 */
function initializeNavbar() {
    const navbar = document.querySelector('.navbar');
    const brandLogo = document.querySelector('.brand-logo');

    if (navbar) {
        // Add scroll effect to navbar
        let lastScrollTop = 0;
        window.addEventListener('scroll', function () {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            // Add/remove scrolled class for styling
            if (scrollTop > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }, false);
    }

    // Add logo click animation
    if (brandLogo) {
        brandLogo.addEventListener('click', function (e) {
            e.preventDefault();
            this.style.transform = 'scale(0.95) rotate(5deg)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    }

    // Add AI status pulse effect
    const statusDot = document.querySelector('.status-dot');
    if (statusDot) {
        // Enhance the pulse effect
        setInterval(() => {
            statusDot.style.transform = 'scale(1.3)';
            setTimeout(() => {
                statusDot.style.transform = 'scale(1)';
            }, 200);
        }, 3000);
    }

    console.log('🎨 Enhanced navbar initialized');
}

console.log('  Nigerian Customer Support Agent - JavaScript loaded successfully');
