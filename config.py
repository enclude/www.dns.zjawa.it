import os
import yaml


def load() -> dict:
    data_dir = os.environ.get("DATA_DIR", "/app/data")
    config_path = os.path.join(data_dir, "config.yaml")

    conf = {
        "ovh": {
            "endpoint": "ovh-eu",
            "application_key": "",
            "application_secret": "",
            "consumer_key": "",
        },
        "domains": [],
        "settings": {
            "ttl": 60,
            "token_expiry_days": 30,
        },
    }

    if os.path.exists(config_path):
        with open(config_path) as f:
            from_file = yaml.safe_load(f) or {}
        for section, values in from_file.items():
            if isinstance(values, dict) and section in conf:
                conf[section].update(values)
            else:
                conf[section] = values

    ovh = conf["ovh"]
    for env_key, conf_key in [
        ("OVH_ENDPOINT", "endpoint"),
        ("OVH_APPLICATION_KEY", "application_key"),
        ("OVH_APPLICATION_SECRET", "application_secret"),
        ("OVH_CONSUMER_KEY", "consumer_key"),
    ]:
        if v := os.environ.get(env_key):
            ovh[conf_key] = v

    return conf
