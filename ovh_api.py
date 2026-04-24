import ovh
import config as cfg


def _client() -> ovh.Client:
    conf = cfg.load()["ovh"]
    return ovh.Client(
        endpoint=conf["endpoint"],
        application_key=conf["application_key"],
        application_secret=conf["application_secret"],
        consumer_key=conf["consumer_key"],
    )


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
