"""Giao diện thử nghiệm — NGOÀI PHẠM VI CHẤM ĐIỂM.

Một trang HTML tĩnh phục vụ ở ``GET /`` để gọi thử ``/chat`` bằng trình duyệt
thay vì curl. Trang này gọi đúng API công khai như mọi client khác: gửi
``Authorization: Bearer`` và đọc mã lỗi trả về, nên nó cũng là cách trực quan
để thấy ba lớp bảo vệ của CP3 hoạt động (401 / 402 / 429).

Token do người dùng nhập và chỉ nằm trong trình duyệt (localStorage) — server
không lưu, không log.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PAGE = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Day 12 Chat Service</title>
<style>
  :root {
    --bg: #0f1117; --panel: #171a23; --line: #262a36;
    --text: #e6e8ee; --muted: #8b90a0; --accent: #6c8cff;
    --user: #223052; --bot: #1c2030;
    --ok: #4ade80; --warn: #fbbf24; --err: #f87171;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 15px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
    display: flex; justify-content: center; padding: 24px 16px;
  }
  main { width: 100%; max-width: 720px; }
  h1 { font-size: 18px; margin: 0 0 4px; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 20px; }
  .panel {
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 12px; padding: 16px; margin-bottom: 16px;
  }
  label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
  input, textarea {
    width: 100%; background: #0d0f16; color: var(--text);
    border: 1px solid var(--line); border-radius: 8px;
    padding: 9px 11px; font: inherit; font-size: 14px;
  }
  input:focus, textarea:focus { outline: none; border-color: var(--accent); }
  .row { display: flex; gap: 12px; }
  .row > div { flex: 1; }
  #log { min-height: 180px; display: flex; flex-direction: column; gap: 10px; }
  .msg { padding: 10px 13px; border-radius: 10px; max-width: 85%; white-space: pre-wrap; }
  .msg.me { background: var(--user); align-self: flex-end; }
  .msg.bot { background: var(--bot); align-self: flex-start; }
  .msg.sys { background: transparent; border: 1px dashed var(--line);
             color: var(--muted); font-size: 13px; align-self: center; max-width: 100%; }
  .meta { font-size: 11px; color: var(--muted); margin-top: 5px; }
  .empty { color: var(--muted); font-size: 13px; text-align: center; padding: 40px 0; }
  form { display: flex; gap: 10px; margin-top: 12px; }
  form textarea { resize: none; height: 44px; }
  button {
    background: var(--accent); color: #fff; border: 0; border-radius: 8px;
    padding: 0 20px; font: inherit; font-weight: 600; cursor: pointer;
  }
  button:disabled { opacity: .5; cursor: default; }
  .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
  .bar { display: flex; gap: 18px; font-size: 12px; color: var(--muted); align-items: center; }
  code { background: #0d0f16; padding: 1px 5px; border-radius: 4px; font-size: 12px; }
</style>
</head>
<body>
<main>
  <h1>Day 12 — Chat Service</h1>
  <div class="sub">Giao diện thử. Mọi request đi qua đúng đường
    <code>POST /chat</code> như client thật.</div>

  <div class="panel">
    <div class="row">
      <div>
        <label for="token">API_TOKEN (gửi dạng Bearer)</label>
        <input id="token" type="password" placeholder="dán token trong .env">
      </div>
      <div style="max-width:180px">
        <label for="client">X-Client-Id</label>
        <input id="client" value="sv01">
      </div>
    </div>
    <div class="bar" style="margin-top:14px">
      <span><span class="dot" id="health-dot"></span><span id="health-text">đang kiểm tra…</span></span>
      <span><span class="dot" id="ready-dot"></span><span id="ready-text">—</span></span>
    </div>
  </div>

  <div class="panel">
    <div id="log"><div class="empty">Chưa có tin nhắn nào.</div></div>
    <form id="form">
      <textarea id="message" placeholder="Nhập tin nhắn rồi Enter…"></textarea>
      <button id="send" type="submit">Gửi</button>
    </form>
  </div>
</main>

<script>
const $ = (id) => document.getElementById(id);
const log = $("log");

// Token chỉ nằm trong trình duyệt, không gửi đi đâu ngoài header Authorization
$("token").value = localStorage.getItem("day12_token") || "";
$("client").value = localStorage.getItem("day12_client") || "sv01";
$("token").oninput = (e) => localStorage.setItem("day12_token", e.target.value);
$("client").oninput = (e) => localStorage.setItem("day12_client", e.target.value);

function add(cls, text, meta) {
  const empty = log.querySelector(".empty");
  if (empty) empty.remove();
  const el = document.createElement("div");
  el.className = "msg " + cls;
  el.textContent = text;
  if (meta) {
    const m = document.createElement("div");
    m.className = "meta";
    m.textContent = meta;
    el.appendChild(m);
  }
  log.appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Hai probe của CP1/CP4: liveness không đụng Redis, readiness thì có
async function probe(path, dot, label, okText) {
  try {
    const r = await fetch(path);
    const good = r.status === 200;
    $(dot).style.background = good ? "var(--ok)" : "var(--err)";
    $(label).textContent = path + " " + r.status + (good ? " " + okText : "");
  } catch {
    $(dot).style.background = "var(--err)";
    $(label).textContent = path + " không gọi được";
  }
}
probe("/healthz", "health-dot", "health-text", "sống");
probe("/readyz", "ready-dot", "ready-text", "sẵn sàng");

// Mỗi mã lỗi tương ứng một lớp bảo vệ của CP3
const REASONS = {
  401: "401 — token sai hoặc thiếu. Kiểm tra ô API_TOKEN.",
  402: "402 — hết ngân sách trong ngày (DAILY_BUDGET_USD).",
  422: "422 — tin nhắn không hợp lệ (rỗng hoặc quá 2000 ký tự).",
  429: "429 — gọi quá nhanh, xô token đã cạn.",
  503: "503 — service chưa sẵn sàng hoặc đang tắt dần.",
};

$("form").onsubmit = async (e) => {
  e.preventDefault();
  const text = $("message").value.trim();
  if (!text) return;

  $("send").disabled = true;
  add("me", text);
  $("message").value = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + $("token").value,
        "X-Client-Id": $("client").value,
      },
      body: JSON.stringify({ message: text }),
    });

    if (!res.ok) {
      let note = REASONS[res.status] || (res.status + " — lỗi không rõ");
      const retry = res.headers.get("Retry-After");
      if (retry) note += " Thử lại sau " + retry + "s.";
      add("sys", note);
      return;
    }

    const data = await res.json();
    add(
      "bot",
      data.reply,
      "client " + data.client_id +
      " · " + data.turns_before + " lượt trước đó" +
      " · " + data.usage.prompt + "+" + data.usage.completion + " token" +
      " · $" + data.usd_cost.toFixed(8)
    );
  } catch (err) {
    add("sys", "Không gọi được service: " + err.message);
  } finally {
    $("send").disabled = false;
    $("message").focus();
  }
};

// Enter gửi, Shift+Enter xuống dòng
$("message").onkeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("form").requestSubmit();
  }
};
</script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    """Trang thử nghiệm. ``include_in_schema=False`` để nó không lẫn vào
    /docs cùng ba endpoint thật của lab."""
    return PAGE
