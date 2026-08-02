// Configuration
const CONFIG = {
    cartKey: 'coffeeCart',
    currency: '$'
};

// Utility functions
function getCart() {
    const cart = localStorage.getItem(CONFIG.cartKey);
    return cart ? JSON.parse(cart) : {};
}

function saveCart(cart) {
    localStorage.setItem(CONFIG.cartKey, JSON.stringify(cart));
}

function updateCartCount() {
    const cart = getCart();
    const count = Object.values(cart).reduce((sum, qty) => sum + qty, 0);
    document.getElementById('cart-count').textContent = count;
}

function addToCart(id) {
    const cart = getCart();
    cart[id] = (cart[id] || 0) + 1;
    saveCart(cart);
    updateCartCount();
}

function removeFromCart(id) {
    const cart = getCart();
    if (cart[id]) {
        cart[id] -= 1;
        if (cart[id] <= 0) delete cart[id];
        saveCart(cart);
        updateCartCount();
    }
}

function clearCart() {
    localStorage.removeItem(CONFIG.cartKey);
    updateCartCount();
    renderCart();
}

// Rendering functions
async function loadCatalog() {
    const res = await fetch('coffee-data.json');
    const data = await res.json();
    const catalog = document.getElementById('catalog');
    data.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <img src="${item.image}" alt="${item.name}">
            <div class="card-content">
                <h3>${item.name}</h3>
                <p>${item.description}</p>
                <div class="price">${CONFIG.currency}${item.price.toFixed(2)}</div>
                <button data-id="${item.id}" aria-label="Add ${item.name} to cart">Add to Cart</button>
            </div>
        `;
        catalog.appendChild(card);
    });
    // Attach event listeners
    catalog.addEventListener('click', e => {
        if (e.target.matches('button[data-id]')) {
            const id = e.target.getAttribute('data-id');
            addToCart(id);
        }
    });
}

function renderCart() {
    const cart = getCart();
    const cartItems = document.getElementById('cart-items');
    cartItems.innerHTML = '';
    let total = 0;
    for (const id in cart) {
        const qty = cart[id];
        const item = coffeeData.find(c => c.id === id);
        if (!item) continue;
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${item.name} × ${qty}</span>
            <span>${CONFIG.currency}${(item.price * qty).toFixed(2)}</span>
            <button data-id="${id}" aria-label="Remove one ${item.name}">✕</button>
        `;
        cartItems.appendChild(li);
        total += item.price * qty;
    }
    document.getElementById('cart-total').textContent = `Total: ${CONFIG.currency}${total.toFixed(2)}`;
}

// Global variable to hold catalog data for cart rendering
let coffeeData = [];

// Event listeners for cart modal
document.getElementById('cart-button').addEventListener('click', () => {
    document.getElementById('cart-modal').classList.remove('hidden');
    renderCart();
});

document.getElementById('close-cart').addEventListener('click', () => {
    document.getElementById('cart-modal').classList.add('hidden');
});

document.getElementById('clear-cart').addEventListener('click', () => {
    if (confirm('Clear all items from cart?')) clearCart();
});

// Handle remove button in cart
document.getElementById('cart-items').addEventListener('click', e => {
    if (e.target.matches('button[data-id]')) {
        const id = e.target.getAttribute('data-id');
        removeFromCart(id);
        renderCart();
    }
});

// Initialize
(async () => {
    const res = await fetch('coffee-data.json');
    coffeeData = await res.json();
    await loadCatalog();
    updateCartCount();
})();