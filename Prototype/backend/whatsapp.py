"""Minimal WhatsApp Cloud API client (standard library only).

Without WA_TOKEN and WA_PHONE_NUMBER_ID set, every call is printed instead of sent
(dry-run), so you can build and demo the flow before Meta approves anything.
"""
import json
import os
import urllib.request

API = "https://graph.facebook.com/v21.0/{pid}/messages"


def _post(payload):
    token, pid = os.environ.get("WA_TOKEN"), os.environ.get("WA_PHONE_NUMBER_ID")
    if not token or not pid:
        print("[whatsapp dry-run]", json.dumps(payload, ensure_ascii=False))
        return {"dry_run": True}
    req = urllib.request.Request(
        API.format(pid=pid), data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def send_template(to, name, lang="en", params=None):
    """Business-initiated first message. Must be a template Meta has approved (Utility category).

    For your first test use Meta's built-in template name="hello_world", lang="en_US".
    """
    comp = [{"type": "body", "parameters": [{"type": "text", "text": str(x)} for x in params]}] if params else []
    return _post({"messaging_product": "whatsapp", "to": to, "type": "template",
                  "template": {"name": name, "language": {"code": lang}, "components": comp}})


def send_text(to, body):
    return _post({"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}})


def send_buttons(to, body, buttons):
    """Up to 3 reply buttons. buttons = [(id, title), ...]; title max 20 characters."""
    return _post({"messaging_product": "whatsapp", "to": to, "type": "interactive",
                  "interactive": {"type": "button", "body": {"text": body},
                                  "action": {"buttons": [{"type": "reply", "reply": {"id": i, "title": t[:20]}}
                                                         for i, t in buttons[:3]]}}})
