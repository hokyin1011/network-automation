import sys
from pathlib import Path

import pytest
from netmiko import ConnectHandler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import load_inventory  # noqa: E402


@pytest.fixture(scope="session")
def conn():
    devices = dict(load_inventory(str(ROOT / "inventory/hosts.yml")))
    cache = {}

    def get(name):
        if name not in cache:
            cache[name] = ConnectHandler(**devices[name])
        return cache[name]

    yield get
    for c in cache.values():
        c.disconnect()


def pytest_addoption(parser):
    parser.addoption(
        "--converge-timeout", type=int, default=0,
        help="seconds to keep retrying a failing check (use after a config change)",
    )


@pytest.fixture(scope="session")
def converge_timeout(request):
    return request.config.getoption("--converge-timeout")
