from helpers import cases, parsed, wait_until


@cases("lacp")
def test_lacp_bundle(conn, converge_timeout, device, expected):
    def check():
        rows = parsed(conn, device, "show etherchannel summary")
        if rows is None:
            return False, "no port-channels parsed"
        po = next((r for r in rows if r["bundle_name"] == expected["bundle"]), None)
        if po is None:
            return False, f"{expected['bundle']} not found"
        members = dict(zip(po["member_interface"], po["member_interface_status"]))
        # P = bundled in the port-channel; U in the bundle status = in use
        bad = {m: members.get(m, "missing") for m in expected["members"] if members.get(m) != "P"}
        return "U" in po["bundle_status"] and not bad, f"bundle {po['bundle_status']}, not bundled: {bad}"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device}: {detail}"


@cases("stp_root")
def test_stp_root_bridge(conn, converge_timeout, device, expected):
    def check():
        rows = parsed(conn, device, "show spanning-tree root")
        if rows is None:
            return False, "no output parsed"
        # Root cost 0 = this switch is the root bridge for that VLAN
        cost = {int(r["vlan_id"].removeprefix("VLAN")): int(r["root_cost"]) for r in rows}
        wrong = [v for v in expected["root"] if cost.get(v) != 0]
        wrong += [v for v in expected["not_root"] if cost.get(v, 0) == 0]
        return not wrong, f"wrong root role for VLANs {wrong}; root cost per VLAN: {cost}"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device}: {detail}"


@cases("stp_blocked")
def test_stp_blocked_port(conn, converge_timeout, device, expected):
    want = {(int(v), port) for v, port in expected.items()}
    vlans = {v for v, _ in want}

    def check():
        rows = parsed(conn, device, "show spanning-tree")
        if rows is None:
            return False, "no output parsed"
        blocked = {(int(r["vlan_id"]), r["interface"]) for r in rows
                   if r["status"] == "BLK" and int(r["vlan_id"]) in vlans}
        return blocked == want, f"expected blocked {sorted(want)}, got {sorted(blocked)}"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device}: {detail}"
