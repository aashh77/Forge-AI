const http = require('http');
const fs = require('fs');
const path = require('path');
const STATIC_ROOT = path.join(__dirname, "public");
const PORT = process.env.PORT || 4100;
const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webp': 'image/webp'
};
const server = http.createServer((req, res) => {
  if (req.url === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'ok' }));
  }
  let rel = req.url === '/' ? 'index.html' : req.url;
  rel = path.normalize(rel).replace(/^(\.\/)+/, '');
  if (rel.startsWith('..')) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    return res.end('Forbidden');
  }
  let filePath = path.join(STATIC_ROOT, rel);
  if (!path.extname(filePath)) filePath += '.html';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        return res.end("<h1>Forge AI Deployment</h1><p>The generated app is being served statically.</p>");
      }
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('Not found');
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
});
server.listen(PORT, '127.0.0.1', () => console.log('Static server listening on port ' + PORT));
