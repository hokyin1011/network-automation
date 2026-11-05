import argparse
import difflib
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from netmiko import ConnectHandler

from common import load_inventory

RUNNING = Path("configs/running")
BASELINE = Path("configs/baseline")

# Lines that change on their own (timestamps, byte counts) and would show as fake drift
VOLATILE = re.compile(
    r"^(Building configuration|Current configuration :|! Last configuration change"
    r"|! NVRAM config last updated|! No configuration change|ntp clock-period)"
)


def normalize(text):
    lines = [l.rstrip() for l in text.splitlines() if not VOLATILE.match(l.strip())]
    return "\n".join(lines).strip() + "\n"


def pull(item):
    name, params = item
    try:
        with ConnectHandler(**params) as conn:
            cfg = conn.send_command("show running-config", read_timeout=60)
        return name, normalize(cfg), None
    except Exception as e:
        return name, None, f"{type(e).__name__}: {e}"[:120]


def main():
    ap = argparse.ArgumentParser(description="Back up running configs and diff against baseline")
    ap.add_argument("--save-baseline", action="store_true", help="overwrite baseline with current running configs")
    args = ap.parse_args()

    RUNNING.mkdir(parents=True, exist_ok=True)
    BASELINE.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(pull, load_inventory()))

    failed = False
    for name, cfg, err in results:
        if err:
            print(f"ERROR     {name}: {err}")
            failed = True
            continue

        (RUNNING / f"{name}.cfg").write_text(cfg)
        base = BASELINE / f"{name}.cfg"

        if args.save_baseline:
            base.write_text(cfg)
            print(f"BASELINE  {name}")
        elif not base.exists():
            print(f"NO-BASE   {name}  (run with --save-baseline first)")
            failed = True
        else:
            diff = list(difflib.unified_diff(
                base.read_text().splitlines(), cfg.splitlines(),
                fromfile=f"baseline/{name}", tofile=f"running/{name}", lineterm="",
            ))
            if diff:
                print(f"DRIFT     {name}")
                print("\n".join(diff))
                failed = True
            else:
                print(f"OK        {name}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
