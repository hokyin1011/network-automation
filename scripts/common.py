import os

import yaml


def load_inventory(path="inventory/hosts.yml"):
    with open(path) as f:
        data = yaml.safe_load(f)
    defaults = data["defaults"]
    for name, dev in data["devices"].items():
        yield name, {
            "device_type": defaults["device_type"],
            "host": dev["host"],
            "username": defaults["username"],
            "password": os.environ["LAB_PASSWORD"],
            "conn_timeout": 15,
        }
