import asyncio
import random
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

import config as cfg
import database
import ovh_api
import wordlist

_STYLE = """
body{font-family:monospace;max-width:720px;margin:40px auto;padding:0 20px;background:#111;color:#ddd}
h1{color:#7ef}h2{color:#adf;margin-top:1.5em}
code{background:#222;padding:3px 8px;border-radius:4px;color:#afa}
pre{background:#222;padding:12px;border-radius:6px;overflow-x:auto;color:#afa}
.token{background:#1a1a00;border:1px solid #ff9;padding:14px;border-radius:6px;
       word-break:break-all;color:#ff9;font-size:1.15em;letter-spacing:.05em}
.warn{color:#f87;font-weight:bold}
a{color:#7bf}
ul,ol{line-height:2}
.domain{color:#afa}
"""


def _page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html><html lang='pl'>"
        "<head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title}</title>"
        f"<style>{_STYLE}</style>"
        "</head><body>"
        f"{body}"
        "</body></html>"
    )


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


@app.get("/", response_class=HTMLResponse)
async def index():
    conf = cfg.load()
    domains = conf.get("domains", [])
    items = "".join(f"<li><span class='domain'>{d}</span></li>" for d in domains)
    body = (
        "<h1>DNS Auto-Record</h1>"
        "<p>Aplikacja automatycznie tworzy rekordy DNS A dla Twojego publicznego IP.</p>"
        "<h2>Jak to dzia&#322;a?</h2>"
        "<ol>"
        "<li><a href='/token'>Pobierz jednorazowy token</a> &mdash; zostanie wylosowana domena z listy.</li>"
        "<li>Uruchom curl z adresu IPv4, kt&oacute;ry chcesz zarejestrowa&#263;:<br>"
        "<code>curl \"https://&lt;domena&gt;/update?token=TW&Oacute;J_TOKEN\"</code></li>"
        "<li>Subdomena (5 s&#322;&oacute;w po polsku) zostanie skierowana na Tw&oacute;j IP.</li>"
        "<li>Kolejne wywo&#322;ania z innego IP zaktualizuj&#261; rekord.</li>"
        "</ol>"
        "<h2>Obs&#322;ugiwane domeny</h2>"
        f"<ul>{items}</ul>"
        "<p><a href='/token'>&#8594; Pobierz token</a></p>"
    )
    return _page("DNS Auto-Record", body)


@app.get("/token", response_class=HTMLResponse)
async def get_token():
    conf = cfg.load()
    domains = conf.get("domains", [])
    if not domains:
        body = "<h1>B&#322;&aacute;d</h1><p>Brak skonfigurowanych domen w config.yaml.</p>"
        return HTMLResponse(_page("Błąd", body), status_code=503)

    domain = random.choice(domains)
    token = secrets.token_hex(16)
    expiry_days = conf["settings"].get("token_expiry_days", 30)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days)

    await database.create_token(token, domain, expires_at)

    expires_str = expires_at.strftime("%Y-%m-%d %H:%M UTC")
    curl_example = f"curl \"https://{domain}/update?token={token}\""
    body = (
        "<h1>Tw&oacute;j jednorazowy token</h1>"
        "<p class='warn'>&#9888; Token widoczny tylko raz &mdash; zapisz go teraz.</p>"
        f"<p>Domena: <span class='domain'>{domain}</span></p>"
        f"<p>Wa&#380;ny do: {expires_str}</p>"
        "<h2>Token</h2>"
        f"<div class='token'>{token}</div>"
        "<h2>U&#380;ycie (curl z adresu IPv4)</h2>"
        f"<pre>{curl_example}</pre>"
        "<p>Ka&#380;de kolejne wywo&#322;anie z innego IP zaktualizuje rekord DNS.</p>"
        "<p>Je&#347;li IP si&#281; nie zmieni&#322;o &mdash; zostanie zwr&oacute;cona istniej&#261;ca subdomena bez zmiany DNS.</p>"
    )
    return _page("Token DNS", body)


@app.get("/update")
async def update(request: Request, token: str):
    record = await database.get_token(token)
    if not record:
        return PlainTextResponse("Blad: nieprawidlowy lub wygasly token.\n", status_code=401)

    ip = _get_ip(request)

    if ":" in ip:
        return PlainTextResponse(
            "Blad: wykryto adres IPv6. Uzyj polaczenia IPv4.\n", status_code=400
        )

    # IP unchanged — return existing FQDN immediately, no OVH call
    if record["ip"] == ip and record["subdomain"] is not None:
        fqdn = f"{record['subdomain']}.{record['domain']}"
        return PlainTextResponse(f"{fqdn}\n")

    conf = cfg.load()
    domain = record["domain"]
    ttl = conf["settings"].get("ttl", 60)

    try:
        if record["subdomain"] is None:
            existing = await database.get_existing_subdomains(domain)
            slug = wordlist.generate_slug(existing)
            record_id = await asyncio.to_thread(
                ovh_api.create_record, domain, slug, ip, ttl
            )
            await asyncio.to_thread(ovh_api.refresh_zone, domain)
            await database.set_subdomain(token, slug, record_id, ip)
            fqdn = f"{slug}.{domain}"
        else:
            await asyncio.to_thread(
                ovh_api.update_record, domain, record["ovh_record_id"], ip, ttl
            )
            await asyncio.to_thread(ovh_api.refresh_zone, domain)
            await database.update_ip(token, ip)
            fqdn = f"{record['subdomain']}.{record['domain']}"
    except Exception as exc:
        return PlainTextResponse(f"Blad OVH API: {exc}\n", status_code=502)

    return PlainTextResponse(f"{fqdn}\n")

