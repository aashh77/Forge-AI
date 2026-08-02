// app.js – Handles catalogue rendering and search

const catalogueElement = document.getElementById('catalogue');
const searchInput = document.getElementById('search');
let catalogueData = [];

// Fetch catalogue JSON on load
fetch('catalogue.json')
  .then(res => res.json())
  .then(data => {
    catalogueData = data;
    renderCatalogue(catalogueData);
  })
  .catch(err => console.error('Error loading catalogue:', err));

// Render items into the grid
function renderCatalogue(items) {
  catalogueElement.innerHTML = '';
  if (items.length === 0) {
    catalogueElement.innerHTML = '<p class="col-span-full text-center">No items found.</p>';
    return;
  }
  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'bg-white rounded shadow p-4 flex flex-col';
    card.innerHTML = `
      <img src="${item.image}" alt="${item.name}" class="card-img rounded mb-4">
      <h3 class="text-xl font-semibold mb-2">${item.name}</h3>
      <p class="text-sm text-gray-600 mb-4">${item.description}</p>
      <p class="mt-auto font-bold">$${item.price.toFixed(2)}</p>
    `;
    catalogueElement.appendChild(card);
  });
}

// Search functionality – filter items client‑side
searchInput.addEventListener('input', () => {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = catalogueData.filter(item =>
    item.name.toLowerCase().includes(query) ||
    item.description.toLowerCase().includes(query)
  );
  renderCatalogue(filtered);
});