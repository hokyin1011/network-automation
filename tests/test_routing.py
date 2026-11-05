from pathlib import Path

import pytest
import yaml

from helpers import wait_until

INTENT = yaml.safe_load((Path(__file__).resolve().parent.parent / "inventory/intent.yml").read_text())


def cases(section):
    return pytest.mark.parametrize("device,expected", INTENT[section].items(), ids=list(INTENT[section]))


def parsed(conn, device, command):
    rows = conn(device).send_command(command, use_textfsm=True)
    return rows if isinstance(rows, list) else None


@cases("bgp")
def test_bgp_neighbors_established(conn, converge_timeout, device, expected):
    want = set(expected["neighbors"])

    def check():
        rows = parsed(conn, device, "show ip bgp summary")
        if rows is None:
            return False, "no BGP output parsed"
        # Established sessions show a prefix count; anything else shows a state word (Idle, Active)
        up = {r["bgp_neighbor"] for r in rows if r["state_or_prefixes_received"].isdigit()}
        return want <= up, f"not established: {sorted(want - up)}"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device}: {detail}"


@cases("ospf")
def test_ospf_neighbors_full(conn, converge_timeout, device, expected):
    want = set(expected["neighbors"])

    def check():
        rows = parsed(conn, device, "show ip ospf neighbor")
        if rows is None:
            return False, "no OSPF neighbors"
        full = {r["neighbor_id"] for r in rows if r["state"].startswith("FULL")}
        return full == want, f"expected {sorted(want)}, FULL: {sorted(full)}"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device}: {detail}"


@cases("hsrp")
def test_hsrp_roles(conn, converge_timeout, device, expected):
    want = {g: "Active" for g in expected["active"]} | {g: "Standby" for g in expected["standby"]}

    def check():
        rows = parsed(conn, device, "show standby brief")
        if rows is None:
            return False, "no HSRP output parsed"
        roles = {int(r["group"]): r["state"] for r in rows}
        return roles == want, f"expected {want}, got {roles}"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device}: {detail}"
