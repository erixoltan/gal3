#!/usr/bin/env python3
"""Oracle for the normalized Python generator (pygen).

Usage: pygen_oracle.py <pygen-binary> <source.py> [source2.py ...]

For each source file, three mechanical checks:
  1. ast:      ast.dump of original == ast.dump of normalized (meaning unchanged)
  2. comments: every comment survives, as a multiset, trailing whitespace trimmed
  3. idem:     normalizing the normalized output reproduces it byte for byte
"""
import ast, subprocess, sys, tempfile, tokenize, os
from collections import Counter

def comments(path):
    out = []
    with open(path, 'rb') as f:
        for t in tokenize.tokenize(f.readline):
            if tokenize.tok_name[t.type] == 'COMMENT':
                out.append(t.string.rstrip())
    return Counter(out)

def run(pygen, src, dst):
    r = subprocess.run([sys.executable, pygen, src, dst],
                       capture_output=True, text=True, timeout=600)
    return os.path.exists(dst) and os.path.getsize(dst) > 0

def main():
    pygen, files = sys.argv[1], sys.argv[2:]
    ok = bad = 0
    for f in files:
        with tempfile.TemporaryDirectory() as d:
            n1, n2 = os.path.join(d, 'n1.py'), os.path.join(d, 'n2.py')
            if not run(pygen, f, n1):
                print(f"FAIL(gen)      {f}"); bad += 1; continue
            try:
                if ast.dump(ast.parse(open(f).read())) != ast.dump(ast.parse(open(n1).read())):
                    print(f"FAIL(ast)      {f}"); bad += 1; continue
            except SyntaxError:
                print(f"FAIL(syntax)   {f}"); bad += 1; continue
            if comments(f) != comments(n1):
                print(f"FAIL(comments) {f}"); bad += 1; continue
            if not run(pygen, n1, n2) or open(n1).read() != open(n2).read():
                print(f"FAIL(idem)     {f}"); bad += 1; continue
            ok += 1
    print(f"ORACLE: PASS={ok} FAIL={bad}")
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
