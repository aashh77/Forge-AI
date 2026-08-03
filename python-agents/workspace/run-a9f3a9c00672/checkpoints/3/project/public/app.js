// Catalogue data – in a real project this could be fetched from a JSON file
const catalogue = [
    {id:1, name:'Classic Espresso', category:'Espresso', price:2.5, description:'A strong, aromatic shot of espresso.', image:'https://picsum.photos/300/200?random=1'},
    {id:2, name:'Vanilla Latte', category:'Latte', price:4.0, description:'Smooth latte with vanilla syrup.', image:'https://picsum.photos/300/200?random=2'},
    {id:3, name:'Cappuccino', category:'Cappuccino', price:3.5, description:'Espresso with steamed milk and foam.', image:'https://picsum.photos/300/200?random=3'},
    {id:4, name:'Americano', category:'Americano', price:2.0, description:'Espresso diluted with hot water.', image:'https://picsum.photos/300/200?random=4'},
    {id:5, name:'Mocha', category:'Mocha', price:4.5, description:'Chocolate flavored latte.', image:'https://picsum.photos/300/200?random=5'},
    {id:6, name:'Caramel Macchiato', category:'Latte', price:5.0, description:'Espresso with caramel and milk.', image:'https://picsum.photos/300/200?random=6'},
    {id:7, name:'Flat White', category:'Latte', price:4.0, description:'Strong espresso with microfoam.', image:'https://picsum.photos/300/200?random=7'},
    {id:8, name:'Cold Brew', category:'Americano', price:3.0, description:'Slow‑steeped cold coffee.', image:'https://picsum.photos/300/200?random=8'},
    {id:9, name:'Espresso Con Panna', category:'Espresso', price:3.0, description:'Espresso topped with whipped cream.', image:'https://picsum.photos/300/200?random=9'},
    {id:10, name:'Hazelnut Latte', category:'Latte', price:4.5, description:'Latte with hazelnut flavor.', image:'https://picsum.photos/300/200?random=10'}
];

const catalogueContainer = document.getElementById('catalogue');
const categoryFilter = document.getElementById('categoryFilter');
const priceFilter = document.getElementById('priceFilter');
const applyBtn = document.getElementById('applyFilters');

function renderCatalogue(items){
    catalogueContainer.innerHTML = '';
    if(items.length === 0){
        catalogueContainer.innerHTML = '<p>No items match your filter.</p>';
        return;
    }
    items.forEach(item => {
        const card = document.createElement('article');
        card.className = 'card';
        card.innerHTML = `
            <img src="${item.image}" alt="${item.name}" />
            <div class="card-content">
                <h3>${item.name}</h3>
                <p>${item.description}</p>
                <div class="price">$${item.price.toFixed(2)}</div>
            </div>
        `;
        catalogueContainer.appendChild(card);
    });
}

function applyFilters(){
    const selectedCategory = categoryFilter.value;
    const maxPrice = parseFloat(priceFilter.value);
    let filtered = catalogue;
    if(selectedCategory !== 'all'){
        filtered = filtered.filter(item => item.category === selectedCategory);
    }
    if(!isNaN(maxPrice)){
        filtered = filtered.filter(item => item.price <= maxPrice);
    }
    renderCatalogue(filtered);
    // Persist filter state
    localStorage.setItem('categoryFilter', selectedCategory);
    localStorage.setItem('priceFilter', priceFilter.value);
}

// Load persisted filter state
function loadPersistedFilters(){
    const savedCategory = localStorage.getItem('categoryFilter');
    const savedPrice = localStorage.getItem('priceFilter');
    if(savedCategory){ categoryFilter.value = savedCategory; }
    if(savedPrice){ priceFilter.value = savedPrice; }
    applyFilters();
}

applyBtn.addEventListener('click', applyFilters);

// Initial load
loadPersistedFilters();