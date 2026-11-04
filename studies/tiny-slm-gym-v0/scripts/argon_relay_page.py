"""Tailnet-only page for running Argon prompts in the Gemini app: copy buttons + a box to paste each reply back.

  python argon_relay_page.py  -> http://<groot tailscale ip>:8765/
Replies are saved to argon-app/replies/<prompt>-<timestamp>.txt (never overwritten).
"""
import html
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

DIR = Path(__file__).resolve().parent.parent / "argon-app"
REPLIES = DIR / "replies"
HOST, PORT = "100.113.138.100", 8765
NOTES = {
    "1-breakout-write-MAX": "Highest reasoning setting. Effort A/B: same prompt as #2.",
    "2-breakout-write-DEFAULT": "Default setting (no extended/deep thinking). Effort A/B vs #1.",
    "3-seaquest-write-MAX": "Highest setting. Argon via agy scored 1.8; Astra 43.2.",
    "4-council-seat-MAX": "Highest setting. Long paste (54 KB). Argon joins the council as 5th seat.",
    "5-qwen-weight-edit-relay-round1-MAX": "Highest setting. Round 1 of a relay: paste the reply back, I run its code "
                                           "on Modal and give you round 2.",
    "6-TASK-breakout-write-with-tools": "TASK mode. Same Breakout write, but Argon may play the game and search/train. "
                                        "Scored here on 1,000 fresh episodes; a separate tool-use arm.",
    "7-TASK-gemma270m-weight-edit": "TASK mode. The blog's follow-up where Astra failed (Gemma 270M). Deliverable: "
                                    "apply_edit.py, which I audit and score on MATH-500 myself.",
    "8-TASK-qwen35-recreate-exp8": "TASK mode. Recreate the blog's headline (Qwen3.5-0.8B 7.9 -> 48.1). Deliverable: "
                                   "apply_edit.py, audited and scored on our held-out protocol.",
}


def page():
    rows = []
    for p in sorted(DIR.glob("*.txt")):
        k = p.stem
        got = sorted(REPLIES.glob(k + "-*.txt"))
        rows.append(f"""
<section><h2>{html.escape(k)}</h2><p>{html.escape(NOTES.get(k, ''))} ({len(p.read_text()):,} chars)
{'<b>reply received ✓</b>' if got else ''}</p>
<textarea id="p-{k}" readonly>{html.escape(p.read_text())}</textarea>
<button onclick="cp('p-{k}', this)">Copy prompt</button>
<form method="post" action="/reply"><input type="hidden" name="k" value="{k}">
<textarea name="text" placeholder="Paste Argon's full reply here"></textarea>
<button type="submit">Send reply to groot</button></form></section>""")
    return f"""<!doctype html><meta name=viewport content="width=device-width,initial-scale=1">
<title>Argon prompts</title><style>body{{font:15px system-ui;margin:12px;background:#111;color:#eee}}
section{{border:1px solid #444;border-radius:10px;padding:10px;margin:12px 0}}textarea{{width:100%;height:90px;
background:#222;color:#ddd;border:1px solid #555;border-radius:6px}}button{{font-size:16px;padding:10px 14px;margin:6px 0;
border-radius:8px;border:0;background:#4b7bec;color:#fff}}</style>
<h1>Argon prompts</h1><p>Copy → paste into the Gemini app (Argon) → paste its whole reply below → Send.</p>
{''.join(rows)}
<script>function cp(id,b){{const t=document.getElementById(id);t.focus();t.select();t.setSelectionRange(0,t.value.length);
let ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}
if(navigator.clipboard&&window.isSecureContext){{navigator.clipboard.writeText(t.value).then(()=>b.textContent='Copied ✓')}}
b.textContent=ok?'Copied ✓':'Selected — tap Copy';}}</script>"""


class H(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send(page())

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        if n > 5_000_000:
            return self._send("too large", 413)
        q = parse_qs(self.rfile.read(n).decode(errors="replace"))
        k, text = q.get("k", [""])[0], q.get("text", [""])[0]
        if not (DIR / f"{k}.txt").exists() or not text.strip():
            return self._send("unknown prompt or empty reply", 400)
        REPLIES.mkdir(exist_ok=True)
        (REPLIES / f"{k}-{time.strftime('%Y%m%dT%H%M%S')}.txt").write_text(text)
        self._send(f"<meta http-equiv=refresh content='1;url=/'>Saved reply for {html.escape(k)} ({len(text):,} chars).")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
