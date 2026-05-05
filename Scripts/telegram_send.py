# -*- coding: utf-8 -*-
"""
telegram_send.py — Halo_Pro Telegram Outbound

Pure-stdlib HTTP-Client (urllib + json) für Telegram Bot API.
Eigener Halo_Pro-Bot (separat von Halos privatem Bot).

API:
  send_text(text, parse_mode='HTML', target_id=None) -> bool
  send_photo(photo_path, caption=None, target_id=None) -> bool
  send_document(doc_path, caption=None, target_id=None) -> bool

Konfiguration:
  Bot-Token via halo_credentials --get telegram_pro
  USER_ID hardcoded auf Mads User-ID (5996284268)
  Override via env: HALO_PRO_TG_BOT_TOKEN, HALO_PRO_TG_USER_ID

CLI:
  python Scripts/telegram_send.py text "Hi Mad"
  python Scripts/telegram_send.py photo path/to/img.png [--caption "..."]
  python Scripts/telegram_send.py doc path/to/file.pdf [--caption "..."]

Setup:
  1. @BotFather: /newbot -> Halo_Pro_Bot -> Token kopieren
  2. python Scripts/halo_credentials.py --add telegram_pro <TOKEN>
  3. Test: python Scripts/telegram_send.py text "Halo_Pro live"
"""

import io
import json
import mimetypes
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
CRED_SCRIPT = str(SCRIPT_DIR / "halo_credentials.py")
PYTHON_EXE = "D:/Anthropic_Claude/Programme/Python/python.exe"
SERVICE_NAME = "telegram_pro"

USER_ID = int(os.environ.get("HALO_PRO_TG_USER_ID", "5996284268"))
TIMEOUT_S = 30
LOG_FILE = ROOT / "Logs/telegram_send.log"


def _get_token() -> str:
    """Bot-Token aus halo_credentials.py holen — Env-Override moeglich."""
    env_token = os.environ.get("HALO_PRO_TG_BOT_TOKEN")
    if env_token:
        return env_token
    r = subprocess.run([PYTHON_EXE, CRED_SCRIPT, "--get", SERVICE_NAME],
                       capture_output=True, text=True)
    m = re.search(r'`([^`]+)`', r.stdout)
    if not m:
        sys.exit(f"Kein {SERVICE_NAME} Token. Setup:\n"
                 f"  1. @BotFather /newbot -> Token holen\n"
                 f"  2. python Scripts/halo_credentials.py --add {SERVICE_NAME} <TOKEN>")
    return m.group(1)


def _api_base() -> str:
    return f"https://api.telegram.org/bot{_get_token()}"


def _log(msg: str) -> None:
    try:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def _post_json(method: str, payload: dict) -> dict:
    url = f"{_api_base()}/{method}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        return json.loads(r.read())


def _build_multipart(fields: dict, files: dict) -> tuple[bytes, str]:
    """multipart/form-data body builder."""
    boundary = secrets.token_hex(16)
    buf = io.BytesIO()
    for k, v in fields.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        buf.write(str(v).encode("utf-8"))
        buf.write(b"\r\n")
    for k, (filename, content, mimetype) in files.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode())
        buf.write(f"Content-Type: {mimetype}\r\n\r\n".encode())
        buf.write(content)
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue(), f"multipart/form-data; boundary={boundary}"


def _post_multipart(method: str, fields: dict, files: dict) -> dict:
    url = f"{_api_base()}/{method}"
    body, ctype = _build_multipart(fields, files)
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": ctype}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        return json.loads(r.read())


def send_text(text: str, parse_mode: str = "HTML", target_id: int | None = None) -> bool:
    target = target_id or USER_ID
    try:
        result = _post_json("sendMessage", {
            "chat_id": target,
            "text": text,
            "parse_mode": parse_mode,
        })
        ok = bool(result.get("ok"))
        _log(f"text {'OK' if ok else 'FAIL'}: target={target} text={text[:60]!r}")
        if not ok:
            _log(f"text response: {result}")
        return ok
    except Exception as e:
        _log(f"text ERR: {e}")
        return False


def send_photo(photo_path: str | Path, caption: str | None = None, target_id: int | None = None) -> bool:
    target = target_id or USER_ID
    p = Path(photo_path)
    if not p.exists():
        _log(f"photo SKIP: file not found {p}")
        return False
    try:
        mime, _ = mimetypes.guess_type(str(p))
        mime = mime or "image/png"
        fields = {"chat_id": target}
        if caption:
            fields["caption"] = caption
            fields["parse_mode"] = "HTML"
        files = {"photo": (p.name, p.read_bytes(), mime)}
        result = _post_multipart("sendPhoto", fields, files)
        ok = bool(result.get("ok"))
        _log(f"photo {'OK' if ok else 'FAIL'}: target={target} file={p.name} ({p.stat().st_size}B)")
        if not ok:
            _log(f"photo response: {result}")
        return ok
    except Exception as e:
        _log(f"photo ERR: {e}")
        return False


def send_document(doc_path: str | Path, caption: str | None = None, target_id: int | None = None) -> bool:
    target = target_id or USER_ID
    p = Path(doc_path)
    if not p.exists():
        _log(f"document SKIP: file not found {p}")
        return False
    try:
        mime, _ = mimetypes.guess_type(str(p))
        mime = mime or "application/octet-stream"
        fields = {"chat_id": target}
        if caption:
            fields["caption"] = caption
            fields["parse_mode"] = "HTML"
        files = {"document": (p.name, p.read_bytes(), mime)}
        result = _post_multipart("sendDocument", fields, files)
        ok = bool(result.get("ok"))
        _log(f"document {'OK' if ok else 'FAIL'}: target={target} file={p.name} ({p.stat().st_size}B)")
        if not ok:
            _log(f"document response: {result}")
        return ok
    except Exception as e:
        _log(f"document ERR: {e}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Halo_Pro Telegram Outbound")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_text = sub.add_parser("text", help="Sende Text")
    p_text.add_argument("message")

    p_photo = sub.add_parser("photo", help="Sende Bild")
    p_photo.add_argument("path")
    p_photo.add_argument("--caption", default=None)

    p_doc = sub.add_parser("doc", help="Sende Dokument (PDF, etc.)")
    p_doc.add_argument("path")
    p_doc.add_argument("--caption", default=None)

    args = parser.parse_args()
    ok = False
    if args.cmd == "text":
        ok = send_text(args.message)
    elif args.cmd == "photo":
        ok = send_photo(args.path, args.caption)
    elif args.cmd == "doc":
        ok = send_document(args.path, args.caption)
    print("delivered" if ok else "FAILED — Logs/telegram_send.log pruefen")
    sys.exit(0 if ok else 1)
