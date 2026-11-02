import os
import sys
from concurrent.futures import ThreadPoolExecutor

import yaml
from netmiko import ConnectHandler


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


def check(item):
    name, params = item
    try:
        with ConnectHandler(**params) as conn:
            actual = conn.find_prompt().rstrip("#>")
        ok = actual == name
        return name, params["host"], ok, actual if ok else f"MISMATCH: device says {actual}"
    except Exception as e:
        return name, params["host"], False, f"{type(e).__name__}: {e}"[:120]


def main():
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(check, load_inventory()))
    for name, host, ok, detail in results:
        print(f"{'OK  ' if ok else 'FAIL'}  {name:<10} {host:<14} {detail}")
    sys.exit(0 if all(r[2] for r in results) else 1)


if __name__ == "__main__":
    main()
