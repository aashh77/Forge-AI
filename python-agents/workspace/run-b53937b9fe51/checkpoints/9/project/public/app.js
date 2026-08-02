// Utility functions
const API_BASE = '/api';
const CART_KEY = 'coffee_cart';

function getCart() {
  const cart = localStorage.getItem(CART_KEY);
  return cart ? JSON.parse(cart) : {};
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function updateCartCount() {
  const cart = getCart();
  const count = Object.values(cart).reduce((sum, qty) => sum + qty, 0);
  document.getElementById('cart-count').textContent = count;
}

// Render product list
async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE}/products`);
    const products = await res.json();
    const list = document.getElementById('product-list');
    list.innerHTML = '';
    products.forEach(p => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <img src="https://picsum.photos/seed/${p.id}/300/200" alt="${p.name}">
        <div class="card-content">
          <h3>${p.name}</h3>
          <p>$${p.price.toFixed(2)}</p>
          <button data-id="${p.id}"><i class="fas fa-cart-plus"></i> Add to Cart</button>
        </div>
      `;
      list.appendChild(card);
    });
    // Attach event listeners
    list.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => addToCart(btn.dataset.id));
    });
  } catch (err) {
    console.error('Failed to load products', err);
  }
}

function addToCart(id) {
  const cart = getCart();
  cart[id] = (cart[id] || 0) + 1;
  saveCart(cart);
  updateCartCount();
}

// Render cart
async function renderCart() {
  const cart = getCart();
  const itemsDiv = document.getElementById('cart-items');
  itemsDiv.innerHTML = '';
  let total = 0;
  const productIds = Object.keys(cart);
  if (productIds.length === 0) {
    itemsDiv.textContent = 'Your cart is empty.';
  } else {
    // Fetch product details for each id
    const res = await fetch(`${API_BASE}/products`);
    const products = await res.json();
    const prodMap = Object.fromEntries(products.map(p => [p.id, p]));
    productIds.forEach(id => {
      const qty = cart[id];
      const prod = prodMap[id];
      const item = document.createElement('div');
      item.className = 'cart-item';
      item.innerHTML = `<span>${prod.name} x${qty}</span><span>$${(prod.price * qty).toFixed(2)}</span>`;
      itemsDiv.appendChild(item);
      total += prod.price * qty;
    });
  }
  document.getElementById('cart-total').textContent = total.toFixed(2);
}

// UI interactions
document.getElementById('view-cart-btn').addEventListener('click', () => {
  document.getElementById('cart').classList.remove('hidden');
  renderCart();
});

document.getElementById('close-cart-btn').addEventListener('click', () => {
  document.getElementById('cart').classList.add('hidden');
});

// Initial load
updateCartCount();
loadProducts();