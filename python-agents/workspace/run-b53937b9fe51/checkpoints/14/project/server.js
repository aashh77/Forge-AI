const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 4100;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

const DATA_FILE = path.join(__dirname, 'data.json');

function readData() {
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    return { catalogue: [], cart: [] };
  }
}

function writeData(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/api/catalogue', (req, res) => {
  const data = readData();
  res.json(data.catalogue);
});

app.post('/api/cart/add', (req, res) => {
  const { id, name, price, quantity } = req.body;
  if (!id || !name || !price || !quantity) {
    return res.status(400).json({ error: 'Missing item fields' });
  }
  const data = readData();
  const existing = data.cart.find(item => item.id === id);
  if (existing) {
    existing.quantity += quantity;
  } else {
    data.cart.push({ id, name, price, quantity });
  }
  writeData(data);
  res.json({ success: true, cart: data.cart });
});

app.get('/api/cart', (req, res) => {
  const data = readData();
  res.json(data.cart);
});

app.delete('/api/cart/remove', (req, res) => {
  const { id } = req.body;
  if (!id) {
    return res.status(400).json({ error: 'Missing id' });
  }
  const data = readData();
  data.cart = data.cart.filter(item => item.id !== id);
  writeData(data);
  res.json({ success: true, cart: data.cart });
});

app.post('/api/cart/clear', (req, res) => {
  const data = readData();
  data.cart = [];
  writeData(data);
  res.json({ success: true, cart: data.cart });
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});