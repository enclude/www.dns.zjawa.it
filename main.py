import asyncio
import logging
import os
import random
import secrets
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

import aiosqlite

import config as cfg
import database
import ovh_api
import wordlist

# Rate limiter — śledzi nieudane próby /update per IP
_RATE_WINDOW = 60   # sekund
_RATE_MAX = 10      # max nieudanych prób w oknie
_failed: dict[str, list[float]] = defaultdict(list)


def _is_rate_limited(ip: str) -> bool:
    cutoff = time.monotonic() - _RATE_WINDOW
    _failed[ip] = [t for t in _failed[ip] if t > cutoff]
    return len(_failed[ip]) >= _RATE_MAX


def _record_failure(ip: str) -> None:
    _failed[ip].append(time.monotonic())


_log = logging.getLogger("dns")


def _setup_logging() -> None:
    data_dir = os.environ.get("DATA_DIR", "/app/data")
    handler = logging.FileHandler(os.path.join(data_dir, "dns.log"))
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"))
    handler.formatter.converter = time.gmtime
    _log.addHandler(handler)
    _log.setLevel(logging.INFO)


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
footer{margin-top:3em;padding-top:1em;border-top:1px solid #333;color:#555;font-size:.85em}
footer a{color:#555}
"""

_FOOTER = (
    "<footer>"
    "<a href='https://github.com/enclude/www.dns.zjawa.it' target='_blank'>"
    "github.com/enclude/www.dns.zjawa.it"
    "</a>"
    "</footer>"
)


def _page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html><html lang='pl'>"
        "<head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title}</title>"
        f"<style>{_STYLE}</style>"
        "</head><body>"
        f"{body}"
        f"{_FOOTER}"
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
    _setup_logging()
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
async def get_token(request: Request):
    conf = cfg.load()
    domains = conf.get("domains", [])
    if not domains:
        body = "<h1>B&#322;&aacute;d</h1><p>Brak skonfigurowanych domen w config.yaml.</p>"
        return HTMLResponse(_page("Błąd", body), status_code=503)

    domain = random.choice(domains)
    token = secrets.token_urlsafe(32)
    expiry_days = conf["settings"].get("token_expiry_days", 30)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days)

    for _ in range(10):
        existing = await database.get_existing_subdomains(domain)
        slug = wordlist.generate_slug(existing)
        try:
            await database.create_token(token, domain, slug, expires_at)
            break
        except aiosqlite.IntegrityError:
            continue
    else:
        body = "<h1>B&#322;&aacute;d</h1><p>Nie uda&#322;o si&#281; przydzieli&#263; subdomeny. Spr&oacute;buj ponownie.</p>"
        return HTMLResponse(_page("Błąd", body), status_code=503)

    fqdn = f"{slug}.{domain}"
    service_url = f"{request.url.scheme}://{request.headers.get('host', request.url.netloc)}"
    curl_example = f'curl "{service_url}/update?token={token}"'
    expires_str = expires_at.strftime("%Y-%m-%d %H:%M UTC")
    cname_example = f"moj-serwer.example.com.  IN CNAME  {fqdn}."
    body = (
        "<h1>Tw&oacute;j jednorazowy token</h1>"
        "<p class='warn'>&#9888; Token widoczny tylko raz &mdash; zapisz go teraz.</p>"
        f"<p>Subdomena: <span class='domain'>{fqdn}</span></p>"
        f"<p>Wa&#380;ny do: {expires_str} (przed&#322;u&#380;a si&#281; przy ka&#380;dym u&#380;yciu)</p>"
        "<h2>Token</h2>"
        f"<div class='token'>{token}</div>"
        "<h2>U&#380;ycie (curl z adresu IPv4)</h2>"
        f"<pre>{curl_example}</pre>"
        "<p>Pierwsze wywo&#322;anie stworzy rekord A. Ka&#380;de kolejne z innego IP zaktualizuje go.</p>"
        "<h2>Mo&#380;liwe zastosowania</h2>"
        "<ul>"
        "<li><strong>Dost&#281;p do domowego serwera</strong> &mdash; uruchom curl w cronie co kilka minut. "
        "Subdomena zawsze wska&#380;e na Tw&oacute;j aktualny adres IP, nawet je&#347;li si&#281; zmieni.</li>"
        "<li><strong>VPN / tunel SSH</strong> &mdash; po&#322;&aacute;cz si&#281; ze swoim hostem przez subdomen&#281; "
        "zamiast wpisywa&#263; IP na sztywno. Dzia&#322;a z dynamicznym IP od ISP.</li>"
        "<li><strong>W&#322;asna domena przez CNAME</strong> &mdash; dodaj do swojej strefy DNS wpis CNAME "
        "wskazuj&#261;cy na t&#281; subdomen&#281;. Zmiana IP wymaga tylko uruchomienia curl &mdash; "
        "bez dotykania w&#322;asnej strefy.</li>"
        "<li><strong>Self-hosting us&#322;ug</strong> &mdash; serwer WWW, Nextcloud, Home Assistant, kamera IP "
        "&mdash; cokolwiek wystawionego na zewn&#261;trz pod dynamicznym IP.</li>"
        "</ul>"
        "<h2>CNAME &mdash; w&#322;asna domena</h2>"
        "<p>Dodaj w swojej strefie DNS (u w&#322;asnego rejestratora):</p>"
        f"<pre>{cname_example}</pre>"
        "<p>Od tej chwili <code>moj-serwer.example.com</code> b&#281;dzie automatycznie pod&#261;&#380;a&#263; "
        "za Twoim IP &mdash; wystarczy regularnie wo&#322;a&#263; curl z tokena powy&#380;ej.</p>"
        "<h2>Cron &mdash; automatyczna aktualizacja</h2>"
        "<p>Dodaj do <code>crontab -e</code> na swoim serwerze/routerze:</p>"
        f"<pre>*/5 * * * * curl -s \"{service_url}/update?token={token}\" &gt; /dev/null</pre>"
        "<p>Co 5 minut &mdash; je&#347;li IP si&#281; nie zmieni&#322;o, zapytanie wr&oacute;ci natychmiast bez aktualizacji DNS.</p>"
    )
    return _page("Token DNS", body)


@app.get("/update")
async def update(request: Request, token: str):
    ip = _get_ip(request)

    if ":" in ip:
        return PlainTextResponse(
            "Blad: wykryto adres IPv6. Uzyj polaczenia IPv4.\n", status_code=400
        )

    if _is_rate_limited(ip):
        return PlainTextResponse(
            "Blad: zbyt wiele nieudanych prob. Sprobuj za minute.\n", status_code=429
        )

    record = await database.get_token(token)
    if not record:
        _record_failure(ip)
        return PlainTextResponse("Blad: nieprawidlowy lub wygasly token.\n", status_code=401)

    conf = cfg.load()
    domain = record["domain"]
    ttl = conf["settings"].get("ttl", 60)
    expiry_days = conf["settings"].get("token_expiry_days", 30)

    slug = record["subdomain"]
    fqdn = f"{slug}.{domain}"

    # IP unchanged — extend expiry and return existing FQDN, no OVH call
    if record["ip"] == ip and record["ovh_record_id"] is not None:
        await database.touch_token(token, expiry_days)
        _log.info("ip=%s fqdn=%s action=unchanged", ip, fqdn)
        return PlainTextResponse(f"{fqdn}\n")

    try:
        if record["ovh_record_id"] is None:
            # Pierwsze użycie tokena — subdomena już przypisana, tworzymy rekord w OVH
            record_id = await asyncio.to_thread(
                ovh_api.create_record, domain, slug, ip, ttl
            )
            await asyncio.to_thread(ovh_api.refresh_zone, domain)
            await database.set_subdomain(token, slug, record_id, ip, expiry_days)
            _log.info("ip=%s fqdn=%s action=created", ip, fqdn)
        else:
            await asyncio.to_thread(
                ovh_api.update_record, domain, record["ovh_record_id"], ip, ttl
            )
            await asyncio.to_thread(ovh_api.refresh_zone, domain)
            await database.update_ip(token, ip, expiry_days)
            _log.info("ip=%s fqdn=%s action=updated", ip, fqdn)
    except Exception as exc:
        return PlainTextResponse(f"Blad DNS API: {exc}\n", status_code=502)

    return PlainTextResponse(f"{fqdn}\n")

