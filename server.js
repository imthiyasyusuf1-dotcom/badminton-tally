const http = require('http');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, 'scores.json');
const PORT = 8840 + 1; // 8841, avoid clash with existing funnel proxies

const PLAYERS = ["Matty", "Wilford", "Sidney", "Marcus", "Yusuf"];

function loadScores() {
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    const init = {};
    PLAYERS.forEach(p => init[p] = 0);
    fs.writeFileSync(DATA_FILE, JSON.stringify(init));
    return init;
  }
}

function saveScores(scores) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(scores));
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === '/scores' && req.method === 'GET') {
    const scores = loadScores();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(scores));
    return;
  }

  if (req.url === '/adjust' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const { player, delta } = JSON.parse(body);
        if (!PLAYERS.includes(player)) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'unknown player' }));
          return;
        }
        const scores = loadScores();
        scores[player] = Math.max(0, (scores[player] || 0) + delta);
        saveScores(scores);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(scores));
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  if (req.url === '/reset' && req.method === 'POST') {
    const scores = {};
    PLAYERS.forEach(p => scores[p] = 0);
    saveScores(scores);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(scores));
    return;
  }

  res.writeHead(404);
  res.end('not found');
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Badminton tally server on http://127.0.0.1:${PORT}`);
});
