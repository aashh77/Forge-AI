// Coffee catalogue data
const coffeeItems = [
    {id:1, name:'Espresso', type:'espresso', price:2.5, description:'Strong and bold espresso shot.', image:'https://picsum.photos/300/200?random=1'},
    {id:2, name:'Cappuccino', type:'cappuccino', price:3.0, description:'Espresso with steamed milk and foam.', image:'https://picsum.photos/300/200?random=2'},
    {id:3, name:'Latte', type:'latte', price:3.5, description:'Smooth espresso with steamed milk.', image:'https://picsum.photos/300/200?random=3'},
    {id:4, name:'Americano', type:'americano', price:2.0, description:'Espresso diluted with hot water.', image:'https://picsum.photos/300/200?random=4'},
    {id:5, name:'Mocha', type:'latte', price:4.0, description:'Chocolate flavored latte.', image:'https://picsum.photos/300/200?random=5'},
    {id:6, name:'Macchiato', type:'espresso', price:2.8, description:'Espresso with a dash of milk foam.', image:'https://picsum.photos/300/200?random=6'}
];

// Cart state stored in localStorage
const CART_KEY = 'cafe_aroma_cart';
let cart = JSON.parse(localStorage.getItem(CART_KEY)) || [];

function saveCart() {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCount();
}

function updateCartCount() {
    const countEl = document.getElementById('cart-count');
    countEl.textContent = cart.reduce((sum, item) => sum + item.qty, 0);
}

function renderItems(filter='all') {
    const container = document.getElementById('items');
    container.innerHTML = '';
    const filtered = coffeeItems.filter(item => filter==='all' || item.type===filter);
    filtered.forEach(item => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
            <img src="${item.image}" alt="${item.name} photo">
            <div class="content">
                <h3>${item.name}</h3>
                <p>${item.description}</p>
                <div class="price">$${item.price.toFixed(2)}</div>
                <button data-id="${item.id}"><i class="fas fa-cart-plus"></i> Add to cart</button>
            </div>
        `;
        container.appendChild(card);
    });
    // Attach event listeners to buttons
    container.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = parseInt(btn.dataset.id);
            const existing = cart.find(ci => ci.id===id);
            if(existing){
                existing.qty += 1;
            } else {
                const coffee = coffeeItems.find(ci => ci.id===id);
                cart.push({id:coffee.id, name:coffee.name, price:coffee.price, qty:1});
            }
            saveCart();
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    renderItems();
    updateCartCount();
    const filterEl = document.getElementById('type-filter');
    filterEl.addEventListener('change', () => {
        renderItems(filterEl.value);
    });
});
