import time


def wait_until(check, timeout=90, interval=5):
    """Retry check() until it passes or time runs out. Protocols need time to converge."""
    deadline = time.monotonic() + timeout
    while True:
        ok, detail = check()
        if ok or time.monotonic() >= deadline:
            return ok, detail
        time.sleep(interval)
