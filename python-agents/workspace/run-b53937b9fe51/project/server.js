const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 4100;

// CORS configuration to allow only the deployed Vercel domain and credentials
const corsOptions = {
  origin: 'https://myapp.vercel.app',
  credentials: true
};

app.use(cors(corsOptions));
app.use(express.json());
app.use(express.static('public'));

// Health check route
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// Helper to read and write data.json
const getData = () => JSON.parse(fs.readFileSync(path.join(__dirname, 'data.json'), 'utf8'));
const writeData = (data) => fs.writeFileSync(path.join(__dirname, 'data.json'), JSON.stringify(data, null, 2));

// API routes
app.get('/api/catalogue', (req, res) => {
  const data = getData();
  res.json(data.catalogue);
});

app.get('/api/cart', (req, res) => {
  const data = getData();
  res.json(data.cart);
});

app.post('/api/cart', (req, res) => {
  const newItem = req.body;
  const data = getData();
  const existing = data.cart.find(i => i.id === newItem.id);
  if (existing) {
    existing.qty += newItem.qty || 1;
  } else {
    data.cart.push({ ...newItem, qty: newItem.qty || 1 });
  }
  writeData(data);
  res.json({ success: true, cart: data.cart });
});

app.delete('/api/cart/:id', (req, res) => {
  const id = req.params.id;
  const data = getData();
  data.cart = data.cart.filter(item => item.id !== id);
  writeData(data);
  res.json({ success: true, cart: data.cart });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
// Injected by Forge AI deployment manager
try {
  if (typeof app !== 'undefined' && app && typeof app.get === 'function') {
    app.get('/api/health', (req, res) => {
      res.setHeader('Content-Type', 'application/json');
      res.statusCode = 200;
      res.end(JSON.stringify({ status: 'ok' }));
    });
  }
} catch (e) {
  console.error('[Forge AI] Could not inject /api/health:', e.message);
}
