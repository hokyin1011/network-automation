from helpers import cases, parsed, wait_until


@cases("interfaces")
def test_interfaces_up(conn, converge_timeout, device, expected):
    def check():
        rows = parsed(conn, device, "show ip interface brief")
        if rows is None:
            return False, "no output parsed"
        state = {r["interface"]: (r["status"], r["proto"]) for r in rows}
        bad = {i: state.get(i, "missing") for i in expected if state.get(i) != ("up", "up")}
        return not bad, f"not up/up: {bad}"

    ok, detail = wait_until(check, timeout=converge_timeout)
    assert ok, f"{device}: {detail}"
