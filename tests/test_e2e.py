import re

import pytest

from helpers import INTENT, wait_until

PROBES = [(dev, p) for dev, probes in INTENT["e2e"].items() for p in probes]


@pytest.mark.parametrize("device,probe", PROBES, ids=[f"{d}->{p['dst']}" for d, p in PROBES])
def test_end_to_end_ping(conn, converge_timeout, device, probe):
    def check():
        out = conn(device).send_command(
            f"ping {probe['dst']} source {probe['src']} repeat 5", read_timeout=30
        )
        m = re.search(r"Success rate is (\d+) percent", out)
        rate = int(m.group(1)) if m else 0
        return rate >= 80, f"success rate {rate}%"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device} -> {probe['dst']}: {detail}"
