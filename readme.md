# dns.zjawa.it

Aplikacja do automatycznego zarządzania rekordami DNS A w OVH. Pozwala zarejestrować dynamiczny adres IP pod unikalną, łatwą do zapamiętania subdomeną złożoną z 5 polskich słów.

## Jak to działa

1. Otwierasz w przeglądarce adres aplikacji i pobierasz **jednorazowy token**.
2. Uruchamiasz `curl` z urządzenia, którego IP chcesz zarejestrować:
   ```
   curl "https://dns.zjawa.it/update?token=TWÓJ_TOKEN"
   ```
3. Aplikacja wykrywa Twój publiczny adres IPv4, generuje losową subdomenę (np. `kasza-klimat-kot-jelen-morze.zjawa.it`) i tworzy rekord A w OVH DNS.
4. Każde kolejne wywołanie z **innego IP** aktualizuje rekord. Wywołanie z tego samego IP zwraca istniejącą subdomenę bez zbędnych wywołań API.

## Wymagania

- Docker + Docker Compose
- Konto OVH z aktywną domeną
- Klucze OVH API: Application Key, Application Secret, Consumer Key

## Konfiguracja

### 1. Utwórz katalog na dane

```bash
mkdir -p /opt/nginx/dns.zjawa.it
```

### 2. Skopiuj i uzupełnij plik konfiguracyjny

```bash
cp config.yaml.example /opt/nginx/dns.zjawa.it/config.yaml
```

Edytuj `/opt/nginx/dns.zjawa.it/config.yaml`:

```yaml
ovh:
  endpoint: ovh-eu
  application_key: "TWÓJ_AK"
  application_secret: "TWÓJ_AS"
  consumer_key: "TWÓJ_CK"

domains:
  - zjawa.it

settings:
  ttl: 60               # TTL rekordu DNS w sekundach
  token_expiry_days: 30 # Ważność tokena w dniach
```

Klucze OVH uzyskasz w [panelu API OVH](https://www.ovh.com/auth/api/createToken). Wymagane uprawnienia:

| Metoda | Ścieżka |
|--------|---------|
| GET | `/domain/zone/*` |
| POST | `/domain/zone/*` |
| PUT | `/domain/zone/*` |
| DELETE | `/domain/zone/*` |

### 3. Utwórz plik `.env`

```bash
cp .env.example .env
```

Uzupełnij `.env` tymi samymi kluczami (alternatywa dla `config.yaml`):

```
OVH_APPLICATION_KEY=TWÓJ_AK
OVH_APPLICATION_SECRET=TWÓJ_AS
OVH_CONSUMER_KEY=TWÓJ_CK
```

### 4. Uruchom kontener

```bash
docker compose up -d
```

Aplikacja nasłuchuje na porcie `8000`.

## Nginx Proxy Manager

Aplikacja jest zaprojektowana do pracy za zewnętrznym reverse proxy (NPM na innym hoście). Skonfiguruj Proxy Host w NPM:

- **Forward Hostname/IP:** adres hosta z kontenerem
- **Forward Port:** `8000`
- **Websockets Support:** nie wymagane

Uvicorn uruchomiony jest z flagą `--proxy-headers`, więc prawdziwy IP klienta jest poprawnie odczytywany z nagłówka `X-Forwarded-For`.

> **Bezpieczeństwo:** Zablokuj port `8000` na firewallu hosta tak, by był dostępny tylko z IP serwera NPM:
> ```bash
> ufw allow from <IP_NPM> to any port 8000
> ```

## Użycie

### Pobieranie tokena

Otwórz w przeglądarce:
```
https://dns.zjawa.it/token
```

Token jest wyświetlany **tylko raz** — zapisz go. Wygasa po 30 dniach (konfigurowalne).

### Rejestracja / aktualizacja IP

```bash
curl "https://dns.zjawa.it/update?token=TWÓJ_TOKEN"
```

Odpowiedź (plain text):
```
kasza-klimat-kot-jelen-morze.zjawa.it
```

Wywołanie zwraca tę samą subdomenę za każdym razem. Rekord DNS jest aktualizowany tylko gdy IP się zmieni.

## Struktura projektu

```
├── main.py              # FastAPI — endpointy HTTP
├── config.py            # Ładowanie konfiguracji (env vars + config.yaml)
├── database.py          # SQLite — tokeny i rekordy
├── ovh_api.py           # Wrapper OVH Python SDK
├── wordlist.py          # Lista ~600 polskich słów, generator slugów
├── Dockerfile
├── docker-compose.yml
├── config.yaml.example  # Szablon konfiguracji
└── .env.example         # Szablon zmiennych środowiskowych
```

## Endpointy

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/` | GET | Strona główna z instrukcją |
| `/token` | GET | Generuje i wyświetla jednorazowy token |
| `/update?token=X` | GET | Wykrywa IP, tworzy lub aktualizuje rekord DNS |
