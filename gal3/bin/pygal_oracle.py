#!/usr/bin/env python3
"""pygal behavioral oracle.

A python program and its pygal translation must produce byte-identical
stdout. Per file:

  1. CPython runs the original            -> expected output
  2. pygal.py translates it to gal3       -> prog.gal3
  3. gal.py normalizes                    -> prog.gal
  4. fallback.py iterates to fixpoint     -> prog.atomic
  5. galpy.py generates python            -> prog.py
  6. CPython runs the generated program   -> actual output
  7. expected == actual, byte for byte

Usage: pygal_oracle.py [file.py ...]   (default: examples/pysmall.py)
Work files are kept in /tmp/pygal_oracle/<basename>/ for inspection.
"""

import os
import subprocess
import sys

GAL3 = os.path.expanduser("~/.gal3")
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = [os.path.join(HERE, "..", "examples", "pysmall.py")]
MAX_FALLBACK = 8


def run(cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def stage(binname, src, dst):
    if os.path.exists(dst):
        os.unlink(dst)
    r = run([sys.executable, os.path.join(GAL3, binname), src, dst])
    if not os.path.exists(dst):
        print(f"  FAIL: {binname} produced no output file")
        tail = (r.stdout + r.stderr).strip().splitlines()[-12:]
        for line in tail:
            print(f"    {line}")
        return False
    return True


def oracle(pyfile, generation=1):
    name = os.path.splitext(os.path.basename(pyfile))[0]
    work = os.path.join("/tmp", "pygal_oracle", name + (f".gen{generation}" if generation > 1 else ""))
    os.makedirs(work, exist_ok=True)

    expected = run([sys.executable, pyfile], env=dict(os.environ, PYTHONPATH=GAL3))
    if expected.returncode != 0:
        print(f"  FAIL: CPython rejects the original: {expected.stderr.strip()}")
        return False

    g3 = os.path.join(work, "prog.gal3")
    gal = os.path.join(work, "prog.gal")
    if not stage("pygal.py", pyfile, g3):
        return False
    if not stage("gal.py", g3, gal):
        return False

    prev = gal
    atomic = None
    for i in range(MAX_FALLBACK):
        nxt = os.path.join(work, f"prog.fb{i}")
        if not stage("fallback.py", prev, nxt):
            return False
        with open(prev) as a, open(nxt) as b:
            if a.read() == b.read():
                atomic = nxt
                break
        prev = nxt
    if atomic is None:
        print("  FAIL: fallback did not reach a fixpoint")
        return False

    py = os.path.join(work, "prog.py")
    if not stage("galpy.py", atomic, py):
        return False

    env = dict(os.environ, PYTHONPATH=GAL3)
    actual = run([sys.executable, py], env=env)
    if actual.returncode != 0:
        print(f"  FAIL: generated program crashed: {actual.stderr.strip().splitlines()[-1] if actual.stderr.strip() else '?'}")
        print(f"        work files in {work}")
        return False

    if actual.stdout != expected.stdout:
        print("  FAIL: output differs")
        print("  --- expected (CPython on original) ---")
        sys.stdout.write(expected.stdout)
        print("  --- actual (gal3 chain) ---")
        sys.stdout.write(actual.stdout)
        print(f"        work files in {work}")
        return False

    lines = expected.stdout.count("\n")
    print(f"  OK: {lines} lines of output, byte-identical ({work})")

    if generation == 1:
        # self-application: the generated program is itself gal3-generated
        # python, so the translator must be able to eat its own output
        print(f"{os.path.basename(pyfile)} (self-application):")
        return oracle(py, generation=2)
    return True


def main():
    files = sys.argv[1:] or DEFAULT
    failures = 0
    for f in files:
        print(f"{os.path.basename(f)}:")
        if not oracle(f):
            failures += 1
    if failures:
        print(f"{failures} of {len(files)} FAILED")
        sys.exit(1)
    print(f"all {len(files)} passed")


if __name__ == "__main__":
    main()
