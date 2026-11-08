"""PathSetu backend prototype. Standard library only: run with `python server.py`.

Endpoints
  POST /api/flags                 an AI reader (or you, with curl) sends a flagged scan
  GET  /api/worklist              patients sorted by priority
  GET  /api/metrics               flagged / booked / completed / revenue recovered
  POST /api/patients/<id>/complete  front desk marks the scan done
  GET  /webhook                   Meta's one-time webhook verification
  POST /webhook                   patient replies from WhatsApp (button taps)
"""
import json
import os
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import priority
import whatsapp
from messages import TEXT

DB = os.environ.get("PATHSETU_DB", "pathsetu.db")
VERIFY_TOKEN = os.environ.get("WA_VERIFY_TOKEN", "pathsetu-demo")
INTRO_TEMPLATE = os.environ.get("WA_INTRO_TEMPLATE", "")   # e.g. "pathsetu_followup_intro" once approved
PRICE_RECOVERED = 2975 + 500
QUESTIONS = ["smoke", "sugar", "cough"]
STAGES = ["flagged", "messaged", "answered", "booked", "completed"]


def db():
    con = sqlite3.connect(DB)
    con.execute("create table if not exists patients (id text primary key, data text, created real)")
    return con


def load(pid):
    with db() as con:
        row = con.execute("select data from patients where id=?", (pid,)).fetchone()
    return json.loads(row[0]) if row else None


def save(p):
    with db() as con:
        con.execute("insert or replace into patients values (?,?,?)", (p["id"], json.dumps(p, ensure_ascii=False), p.get("created", time.time())))


def all_patients():
    with db() as con:
        return [json.loads(r[0]) for r in con.execute("select data from patients order by created desc")]


def with_priority(p):
    return {**p, "priority": priority.compute(p)}


# ---------------- conversation ----------------
def ask(p):
    q = p["q"]
    t = TEXT[p["lang"]]
    whatsapp.send_buttons(p["phone"], t["q"][q], [(f"ans:{p['id']}:{q}:1", t["yes"]), (f"ans:{p['id']}:{q}:0", t["no"])])


def start_conversation(p):
    t = TEXT[p["lang"]]
    if INTRO_TEMPLATE:
        whatsapp.send_template(p["phone"], INTRO_TEMPLATE, p["lang"], [p["name"].split()[0]])
    else:
        whatsapp.send_text(p["phone"], t["hello"].format(first=p["name"].split()[0]))
    whatsapp.send_text(p["phone"], t["ask"])
    p.update(stage="messaged", q=0, answers={})
    ask(p)


def on_button(button_id):
    kind, pid, *rest = button_id.split(":")
    p = load(pid)
    if not p:
        return
    t = TEXT[p["lang"]]
    if kind == "ans":
        q, yes = int(rest[0]), rest[1] == "1"
        before = priority.compute(p)["tier"]
        p["answers"][QUESTIONS[q]] = yes
        p["q"] = q + 1
        if p["q"] < 3:
            ask(p)
        else:
            p["stage"] = "answered"
            after = priority.compute(p)
            p.setdefault("log", []).append(f"answers in, priority {before} -> {after['tier']}")
            if after["tier"] == "P1":
                p["log"].append("navigator task: call within 24 h")
            whatsapp.send_buttons(p["phone"], t["slot"], [(f"slot:{pid}:book", t["book"]), (f"slot:{pid}:other", t["other"]), (f"slot:{pid}:call", t["call"])])
    elif kind == "slot":
        if rest[0] == "book":
            p["stage"] = "booked"
            whatsapp.send_text(p["phone"], t["booked"])
        elif rest[0] == "call":
            p.setdefault("log", []).append("call-back requested")
            whatsapp.send_text(p["phone"], t["callback"])
        else:
            whatsapp.send_text(p["phone"], t["other_sent"])
    save(p)


# ---------------- HTTP ----------------
class Handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False, indent=1).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/worklist":
            rank = {"P1": 0, "P2": 1, "P3": 2}
            rows = [with_priority(p) for p in all_patients()]
            rows.sort(key=lambda r: (r["stage"] == "completed", rank[r["priority"]["tier"]], r["created"]))
            return self._json(200, rows)
        if url.path == "/api/metrics":
            ps = all_patients()
            done = sum(p["stage"] == "completed" for p in ps)
            return self._json(200, {"flagged": len(ps), "booked": sum(p["stage"] in ("booked", "completed") for p in ps),
                                    "completed": done, "completion_rate": round(done / len(ps), 2) if ps else 0,
                                    "revenue_recovered_inr": done * PRICE_RECOVERED})
        if url.path == "/webhook":
            q = parse_qs(url.query)
            if q.get("hub.verify_token", [""])[0] == VERIFY_TOKEN:
                self.send_response(200); self.end_headers()
                return self.wfile.write(q.get("hub.challenge", [""])[0].encode())
            return self._json(403, {"error": "verify token does not match WA_VERIFY_TOKEN"})
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/flags":
            f = self._body()
            missing = [k for k in ("name", "age", "phone", "finding", "severity", "reader_confidence") if k not in f]
            if missing:
                return self._json(400, {"error": f"missing fields: {', '.join(missing)}"})
            p = {"id": f.get("id") or f"PS-{int(time.time() * 1000) % 10**7}", "lang": f.get("lang", "en"),
                 "stage": "flagged", "answers": None, "log": [], "created": time.time(), **f}
            if f.get("auto_send", True):
                start_conversation(p)
            save(p)
            return self._json(201, with_priority(p))
        if path.startswith("/api/patients/") and path.endswith("/complete"):
            p = load(path.split("/")[3])
            if not p:
                return self._json(404, {"error": "no such patient"})
            p["stage"] = "completed"
            whatsapp.send_text(p["phone"], TEXT[p["lang"]]["done"])
            save(p)
            return self._json(200, with_priority(p))
        if path == "/webhook":
            body = self._body()
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    for msg in change.get("value", {}).get("messages", []):
                        reply = msg.get("interactive", {}).get("button_reply")
                        if reply:
                            on_button(reply["id"])
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"PathSetu backend on http://localhost:{port}  (WhatsApp {'LIVE' if os.environ.get('WA_TOKEN') else 'dry-run'})")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
