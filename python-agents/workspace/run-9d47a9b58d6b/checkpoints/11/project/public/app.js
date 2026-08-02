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

// Escape HTML helper
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Render items into the grid
function renderCatalogue(items) {
  // Clear existing content
  catalogueElement.textContent = '';
  if (items.length === 0) {
    const p = document.createElement('p');
    p.className = 'col-span-full text-center';
    p.textContent = 'No items found.';
    catalogueElement.appendChild(p);
    return;
  }
  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'bg-white rounded shadow p-4 flex flex-col';

    const img = document.createElement('img');
    img.src = item.image;
    img.alt = item.name;
    img.className = 'card-img rounded mb-4';
    card.appendChild(img);

    const h3 = document.createElement('h3');
    h3.className = 'text-xl font-semibold mb-2';
    h3.textContent = escapeHtml(item.name);
    card.appendChild(h3);

    const desc = document.createElement('p');
    desc.className = 'text-sm text-gray-600 mb-4';
    desc.textContent = escapeHtml(item.description);
    card.appendChild(desc);

    const price = document.createElement('p');
    price.className = 'mt-auto font-bold';
    price.textContent = escapeHtml(`$${item.price.toFixed(2)}`);
    card.appendChild(price);

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