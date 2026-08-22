#!/usr/bin/env python3
"""Network-free tests for per-entry process isolation (#356)."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from pathlib import Path

from entry_sandbox import EntrySandbox

PASSED = 0


def check(label, got, want):
    global PASSED
    if got != want:
        print(f"FAIL  {label}: got {got!r}, want {want!r}")
        sys.exit(1)
    PASSED += 1
    print(f"PASS  {label}")


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    first = EntrySandbox(root, "1AAA")
    second = EntrySandbox(root, "2BBB")
    code = (
        "from pathlib import Path; import os; "
        "Path('same-name.txt').write_text(os.getcwd())"
    )
    result_a = first.run_logged([sys.executable, "-c", code], "run.log")
    result_b = second.run_logged([sys.executable, "-c", code], "run.log")
    check("normal isolated launch succeeds", result_a.returncode, 0)
    check("start_new_session makes pid the recorded pgid",
          result_a.pid, result_a.pgid)
    check("sequential entries receive distinct process groups",
          result_a.pgid != result_b.pgid, True)
    check("same output name stays in each entry directory",
          ((first.child("same-name.txt").exists()
            and second.child("same-name.txt").exists())), True)
    check("the child really ran with the entry sandbox as cwd",
          first.child("same-name.txt").read_text(), str(first.path))
    check("inventory is relative to the entry, never the shared root",
          first.inventory(), ["run.log", "same-name.txt"])

    for unsafe in ("../sibling.txt", str(root / "absolute.txt")):
        try:
            first.child(unsafe)
        except ValueError:
            refused = True
        else:
            refused = False
        check(f"escaping path is refused: {unsafe}", refused, True)

    # The child installs a TERM handler while its parent remains the process
    # tracked by EntrySandbox.  A PGID-scoped timeout reaches both; killing
    # only the parent would never create child-term.json.
    timed = EntrySandbox(root, "3CCC")
    child_code = (
        "import json,signal,time; from pathlib import Path; "
        "signal.signal(signal.SIGTERM, lambda *_: "
        "(Path('child-term.json').write_text(json.dumps({'signal':'TERM'})), "
        "exit(0))); time.sleep(30)"
    )
    parent_code = (
        "import subprocess,sys,time; from pathlib import Path; "
        f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}]); "
        "Path('child-pid.txt').write_text(str(p.pid)); time.sleep(30)"
    )
    timeout_result = timed.run_logged(
        [sys.executable, "-c", parent_code], "timeout.log",
        timeout=0.5, terminate_grace=1.0,
    )
    deadline = time.monotonic() + 2.0
    while not timed.child("child-term.json").exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    check("timeout is recorded", timeout_result.timed_out, True)
    check("timeout terminates the tracked group by signal",
          timeout_result.termination_signal is not None, True)
    check("PGID cleanup reaches a spawned descendant",
          json.loads(timed.child("child-term.json").read_text())["signal"],
          "TERM")

    concurrent = EntrySandbox(root, "4DDD")
    result_box = []
    thread = threading.Thread(
        target=lambda: result_box.append(concurrent.run_logged(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            "concurrent.log", timeout=60,
        ))
    )
    thread.start()
    deadline = time.monotonic() + 2.0
    while not EntrySandbox.active_pgids() and time.monotonic() < deadline:
        time.sleep(0.02)
    active = EntrySandbox.active_pgids()
    EntrySandbox.terminate_all_active(terminate_grace=1.0)
    thread.join(timeout=2.0)
    check("concurrent driver can enumerate only its active PGIDs",
          len(active), 1)
    check("concurrent cancellation lets the worker finish", thread.is_alive(), False)
    check("concurrent cancellation records signal termination",
          result_box[0].termination_signal is not None, True)
    check("active registry is empty after worker cleanup",
          EntrySandbox.active_pgids(), [])

print(f"\n{PASSED} checks passed")
