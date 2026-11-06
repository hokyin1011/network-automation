import time
from pathlib import Path

import pytest
import yaml

INTENT = yaml.safe_load((Path(__file__).resolve().parent.parent / "inventory/intent.yml").read_text())


def cases(section):
    """Parametrize a test with one case per device listed under this intent section."""
    return pytest.mark.parametrize("device,expected", INTENT[section].items(), ids=list(INTENT[section]))


def parsed(conn, device, command):
    rows = conn(device).send_command(command, use_textfsm=True)
    return rows if isinstance(rows, list) else None


def wait_until(check, timeout=0, interval=5):
    """Run check() until it passes or time runs out. timeout=0 means check once."""
    deadline = time.monotonic() + timeout
    while True:
        ok, detail = check()
        if ok or time.monotonic() >= deadline:
            return ok, detail
        time.sleep(interval)
