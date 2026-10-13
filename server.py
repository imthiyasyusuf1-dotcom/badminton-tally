#!/usr/bin/env python3
"""Tiny shared badminton tally server. One room, five players, live sync."""
import json, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PLAYERS = ["Matty", "Wilford", "Sidney", "Marcus", "Yusuf"]
DATA_FILE = os.path.join(os.path.dirname(__file__), "scores.json")
lock = threading.Lock()

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            d = json.load(f)
        for p in PLAYERS:
            d.setdefault(p, 0)
        return d
    return {p: 0 for p in PLAYERS}

def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

scores = load()

PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Badminton Tally</title>
<style>
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(160deg, #0f172a, #1e293b);
    min-height: 100vh; padding: 20px; color: #fff;
  }
  h1 { text-align: center; font-size: 22px; font-weight: 700; margin: 10px 0 20px; letter-spacing: 0.5px; }
  .card {
    background: rgba(255,255,255,0.06); border-radius: 18px; padding: 16px 18px;
    margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between;
    border: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(10px);
  }
  .name { font-size: 19px; font-weight: 600; flex: 1; }
  .score { font-size: 28px; font-weight: 800; width: 50px; text-align: center; color: #4ade80; }
  .btns { display: flex; gap: 8px; }
  button {
    width: 46px; height: 46px; border-radius: 14px; border: none; font-size: 22px;
    font-weight: 700; cursor: pointer; transition: transform 0.08s ease;
  }
  button:active { transform: scale(0.9); }
  .plus { background: #22c55e; color: #fff; }
  .minus { background: #ef4444; color: #fff; }
  .reset {
    display: block; margin: 24px auto 0; background: rgba(255,255,255,0.08);
    color: #f87171; border: 1px solid rgba(255,255,255,0.15); padding: 10px 20px;
    border-radius: 12px; font-size: 14px; font-weight: 600;
  }
  .sub { text-align:center; color:#94a3b8; font-size:13px; margin-bottom: 18px; }
</style>
</head>
<body>
<h1>🏸 Badminton Tally</h1>
<div class="sub">tap + when you win a game</div>
<div id="list"></div>
<button class="reset" onclick="resetAll()">Reset all scores</button>
<script>
async function fetchScores() {
  const r = await fetch('/scores');
  const d = await r.json();
  render(d);
}
function render(d) {
  const list = document.getElementById('list');
  list.innerHTML = '';
  for (const name in d) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="name">${name}</div>
      <div class="score">${d[name]}</div>
      <div class="btns">
        <button class="minus" onclick="change('${name}',-1)">-</button>
        <button class="plus" onclick="change('${name}',1)">+</button>
      </div>`;
    list.appendChild(card);
  }
}
async function change(name, delta) {
  const r = await fetch('/update', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({name, delta})
  });
  const d = await r.json();
  render(d);
}
async function resetAll() {
  if (!confirm('Reset all scores to 0?')) return;
  const r = await fetch('/reset', {method:'POST'});
  const d = await r.json();
  render(d);
}
fetchScores();
setInterval(fetchScores, 2000);
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/scores":
            with lock:
                self._json(scores)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        if self.path == "/update":
            data = json.loads(raw)
            name = data.get("name")
            delta = int(data.get("delta", 0))
            with lock:
                if name in scores:
                    scores[name] = max(0, scores[name] + delta)
                    save(scores)
                self._json(scores)
        elif self.path == "/reset":
            with lock:
                for p in PLAYERS:
                    scores[p] = 0
                save(scores)
                self._json(scores)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Serving on port {port}")
    server.serve_forever()
