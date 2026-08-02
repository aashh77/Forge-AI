// Sample coffee data
const coffees = [
  {id:1,name:'Espresso',description:'Strong and bold',price:3.5, image:'https://picsum.photos/300/200?random=1'},
  {id:2,name:'Cappuccino',description:'Foamy delight',price:4.0, image:'https://picsum.photos/300/200?random=2'},
  {id:3,name:'Latte',description:'Smooth and creamy',price:4.5, image:'https://picsum.photos/300/200?random=3'},
  {id:4,name:'Americano',description:'Classic espresso with water',price:3.0, image:'https://picsum.photos/300/200?random=4'},
  {id:5,name:'Mocha',description:'Chocolate flavored',price:5.0, image:'https://picsum.photos/300/200?random=5'}
];

const catalogue = document.getElementById('catalogue');
const cartCount = document.getElementById('cart-count');
const cartSection = document.getElementById('cart');
const cartItemsList = document.getElementById('cart-items');
const viewCartBtn = document.getElementById('view-cart');
const checkoutBtn = document.getElementById('checkout');

// Load cart from localStorage
function loadCart(){
  const cart = JSON.parse(localStorage.getItem('cart')) || [];
  return cart;
}

// Save cart to localStorage
function saveCart(cart){
  localStorage.setItem('cart', JSON.stringify(cart));
}

// Update cart count display
function updateCartCount(){
  const cart = loadCart();
  cartCount.textContent = cart.reduce((sum,item)=>sum+item.qty,0);
}

// Render catalogue items
function renderCatalogue(){
  catalogue.innerHTML = '';
  coffees.forEach(c=>{
    const card = document.createElement('div');
    card.className='card';
    card.innerHTML=`
      <img src="${c.image}" alt="${c.name}">
      <div class="card-content">
        <h3>${c.name}</h3>
        <p>${c.description}</p>
        <p>Price: $${c.price.toFixed(2)}</p>
        <button aria-label="Add ${c.name} to cart" data-id="${c.id}">Add to Cart</button>
      </div>`;
    catalogue.appendChild(card);
  });
}

// Add item to cart
function addToCart(id){
  const cart = loadCart();
  const item = cart.find(i=>i.id===id);
  if(item){
    item.qty += 1;
  }else{
    const coffee = coffees.find(c=>c.id===id);
    cart.push({id:coffee.id,name:coffee.name,price:coffee.price,qty:1});
  }
  saveCart(cart);
  updateCartCount();
}

// Render cart items
function renderCart(){
  const cart = loadCart();
  cartItemsList.innerHTML='';
  cart.forEach(item=>{
    const li = document.createElement('li');
    li.textContent=`${item.name} x ${item.qty} - $${(item.price*item.qty).toFixed(2)}`;
    cartItemsList.appendChild(li);
  });
}

// Event listeners
catalogue.addEventListener('click',e=>{
  if(e.target.tagName==='BUTTON' && e.target.dataset.id){
    addToCart(parseInt(e.target.dataset.id));
  }
});

viewCartBtn.addEventListener('click',()=>{
  cartSection.hidden = !cartSection.hidden;
  if(!cartSection.hidden){
    renderCart();
  }
});

checkoutBtn.addEventListener('click',()=>{
  alert('Checkout not implemented.');
});

// Initial render
renderCatalogue();
updateCartCount();