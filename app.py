import base64
import hashlib
import html
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from aiohttp import web

DATABASE = Path(os.environ.get("LICENSE_DB", "data/licenses.sqlite3"))
USERNAME = os.environ.get("ADMIN_USERNAME", "khakimovv1")
PASSWORD = os.environ.get("ADMIN_PASSWORD")
if PASSWORD is None:
    local_password = Path(__file__).with_name("admin.password")
    PASSWORD = local_password.read_text(encoding="utf-8").rstrip("\r\n") if local_password.is_file() else ""
if not PASSWORD:
    raise SystemExit("ADMIN_PASSWORD ni sozlang.")
AUTH = "Basic " + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
CSRF = secrets.token_urlsafe(32)
SECURITY_HEADERS = {"Cache-Control": "no-store", "X-Frame-Options": "DENY",
                    "X-Content-Type-Options": "nosniff"}


@contextmanager
def database():
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@web.middleware
async def protect(request, handler):
    if request.path != "/api/licenses/verify":
        supplied = request.headers.get("Authorization", "").encode()
        if not secrets.compare_digest(supplied, AUTH.encode()):
            return web.Response(status=401, text="Admin hisobiga kiring.",
                                headers={"WWW-Authenticate": 'Basic realm="Kalitlar", charset="UTF-8"'})
        if request.method == "POST":
            form = await request.post()
            if form.get("csrf") != CSRF:
                raise web.HTTPForbidden()
    return await handler(request)


async def set_response_headers(request, response):
    response.headers.update(SECURITY_HEADERS)


def panel(new_key=None):
    with database() as db:
        rows = db.execute("SELECT * FROM licenses ORDER BY id DESC").fetchall()
    token = f'<input type="hidden" name="csrf" value="{CSRF}">'
    listing = []
    for row in rows:
        status = "Bekor qilingan" if row["revoked"] else ("Faol" if row["expires"] > time.time() else "Muddati tugagan")
        action = ""
        if status == "Faol":
            action = f'<form action="/admin/{row["id"]}/revoke" method="post">{token}<button>Bekor qilish</button></form>'
        expiry = time.strftime("%Y-%m-%d %H:%M", time.gmtime(row["expires"] + 5*3600))
        listing.append(f'<tr><td>{html.escape(row["label"])}</td><td>{expiry}</td><td>{status}</td><td>{action}</td></tr>')
    notice = f'<aside>Yangi kalitni hozir nusxalang<br><code>{new_key}</code></aside>' if new_key else ""
    page = Path(__file__).with_name("panel.html").read_text(encoding="utf-8")
    return web.Response(text=page.replace("{{token}}", token).replace("{{notice}}", notice)
                        .replace("{{rows}}", "".join(listing) or '<tr><td colspan="4">Hali kalit yaratilmagan.</td></tr>'),
                        content_type="text/html")


async def index(request):
    return panel()


async def create(request):
    form = await request.post()
    label = str(form.get("label", "")).strip()
    try:
        days = int(form.get("days", ""))
    except ValueError:
        days = 0
    if not label or len(label) > 80 or not 1 <= days <= 3650:
        raise web.HTTPBadRequest(text="Nom va 1–3650 kun oralig‘idagi muddatni kiriting.")
    key = secrets.token_urlsafe(32)
    with database() as db:
        db.execute("INSERT INTO licenses(label,hash,expires) VALUES(?,?,?)",
                   (label, digest(key), int(time.time()) + days * 86400))
    return panel(key)


async def revoke(request):
    identifier = request.match_info["id"].lstrip("0") or "0"
    if len(identifier) > 19 or int(identifier) > 2**63 - 1:
        raise web.HTTPNotFound(text="Bunday kalit topilmadi.")
    with database() as db:
        changed = db.execute("UPDATE licenses SET revoked=1 WHERE id=?",
                             (int(identifier),)).rowcount
    if not changed:
        raise web.HTTPNotFound(text="Bunday kalit topilmadi.")
    raise web.HTTPSeeOther("/")


async def verify(request):
    if request.content_type != "application/json":
        raise web.HTTPUnsupportedMediaType()
    try:
        payload = await request.json()
    except (UnicodeError, ValueError):
        raise web.HTTPBadRequest()
    key = payload.get("key") if isinstance(payload, dict) else None
    if not isinstance(key, str) or not 1 <= len(key) <= 256:
        return web.json_response({"valid": False}, status=400)
    with database() as db:
        valid = db.execute("SELECT 1 FROM licenses WHERE hash=? AND revoked=0 AND expires>?",
                           (digest(key), int(time.time()))).fetchone()
    return web.json_response({"valid": bool(valid)})


DATABASE.parent.mkdir(parents=True, exist_ok=True)
with database() as db:
    db.execute("""CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY, label TEXT NOT NULL, hash TEXT UNIQUE NOT NULL,
        expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0)""")

app = web.Application(middlewares=[protect], client_max_size=8192)
app.on_response_prepare.append(set_response_headers)
app.add_routes([web.get("/", index), web.post("/admin/create", create),
                web.post(r"/admin/{id:[0-9]+}/revoke", revoke), web.post("/api/licenses/verify", verify)])

if __name__ == "__main__":
    web.run_app(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8080")))
