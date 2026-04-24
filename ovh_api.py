import ovh
import config as cfg


def _client(with_ck: bool = True) -> ovh.Client:
    conf = cfg.load()["ovh"]
    kwargs = {
        "endpoint": conf["endpoint"],
        "application_key": conf["application_key"],
        "application_secret": conf["application_secret"],
    }
    if with_ck:
        kwargs["consumer_key"] = conf["consumer_key"]
    return ovh.Client(**kwargs)


def create_record(zone: str, subdomain: str, ip: str, ttl: int) -> str:
    client = _client()
    result = client.post(
        f"/domain/zone/{zone}/record",
        fieldType="A",
        subDomain=subdomain,
        target=ip,
        ttl=ttl,
    )
    return str(result["id"])


def update_record(zone: str, record_id: str, ip: str, ttl: int) -> None:
    client = _client()
    client.put(
        f"/domain/zone/{zone}/record/{record_id}",
        target=ip,
        ttl=ttl,
    )


def refresh_zone(zone: str) -> None:
    client = _client()
    client.post(f"/domain/zone/{zone}/refresh")


def request_consumer_key() -> dict:
    """Returns dict with 'consumerKey' and 'validationUrl'."""
    client = _client(with_ck=False)
    access_rules = [
        {"method": "GET",    "path": "/domain/zone/*"},
        {"method": "POST",   "path": "/domain/zone/*"},
        {"method": "PUT",    "path": "/domain/zone/*"},
        {"method": "DELETE", "path": "/domain/zone/*"},
    ]
    return client.request_consumerkey(access_rules)
