#!/usr/bin/env python3
"""Compare a pylex token dump against CPython's tokenize module.

Usage: pylex_oracle.py <source.py> <pylex-dump.txt>

Collapses 3.12+ FSTRING_START/MIDDLE/END sequences into one STRING token so
the reference matches the 3.11-pinned opaque-string model. Kind-only
comparison for NEWLINE/NL/INDENT/DEDENT/ENDMARKER; exact-text comparison for
NAME/NUMBER/STRING/OP/COMMENT.
"""
import sys, tokenize, token as tokmod

KIND_MAP = {
    'Py_Name': 'NAME', 'Py_Number': 'NUMBER', 'Py_String': 'STRING',
    'Py_Op': 'OP', 'Py_Newline': 'NEWLINE', 'Py_Nl': 'NL',
    'Py_Comment': 'COMMENT', 'Py_Indent': 'INDENT', 'Py_Dedent': 'DEDENT',
    'Py_Endmarker': 'ENDMARKER',
}
SKIP_OURS = {'Py_Ws', 'Py_Linejoin'}
TEXT_STRICT = {'NAME', 'NUMBER', 'STRING', 'OP', 'COMMENT'}

def unescape(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            c = s[i+1]
            out.append({'n': '\n', 't': '\t', '\\': '\\'}.get(c, '\\' + c))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)

def load_ours(path):
    toks = []
    for line in open(path, encoding='utf-8').read().splitlines():
        if not line: continue
        kind, _, text = line.partition('\t')
        if kind in SKIP_OURS: continue
        toks.append((KIND_MAP.get(kind, kind), unescape(text)))
    return toks

def source_slice(lines, start, end):
    (r1, c1), (r2, c2) = start, end
    if r1 == r2:
        return lines[r1-1][c1:c2]
    parts = [lines[r1-1][c1:]]
    for r in range(r1+1, r2):
        parts.append(lines[r-1])
    parts.append(lines[r2-1][:c2])
    return ''.join(parts)

def load_reference(path):
    ref = []
    src_lines = open(path, encoding='utf-8').read().splitlines(keepends=True)
    with open(path, 'rb') as f:
        it = tokenize.tokenize(f.readline)
        fstring_depth = 0
        fstring_start = None
        for tok in it:
            name = tokmod.tok_name[tok.type]
            if name == 'ENCODING':
                continue
            if name == 'FSTRING_START':
                if fstring_depth == 0:
                    fstring_start = tok.start
                fstring_depth += 1
                continue
            if fstring_depth:
                if name == 'FSTRING_END':
                    fstring_depth -= 1
                    if fstring_depth == 0:
                        ref.append(('STRING', source_slice(src_lines, fstring_start, tok.end)))
                continue
            ref.append((name, tok.string))
    return ref

def main():
    src, dump = sys.argv[1], sys.argv[2]
    ours, ref = load_ours(dump), load_reference(src)
    n = max(len(ours), len(ref))
    mismatches = 0
    for i in range(n):
        o = ours[i] if i < len(ours) else ('<missing>', '')
        r = ref[i] if i < len(ref) else ('<missing>', '')
        ok = o[0] == r[0] and (o[0] not in TEXT_STRICT or o[1] == r[1])
        if not ok:
            if mismatches == 0:
                print(f"FIRST MISMATCH at token {i}:")
                for j in range(max(0, i-3), min(n, i+4)):
                    oo = ours[j] if j < len(ours) else ('<missing>', '')
                    rr = ref[j] if j < len(ref) else ('<missing>', '')
                    mark = ' <<<' if j == i else ''
                    print(f"  [{j}] ours={oo!r}  ref={rr!r}{mark}")
            mismatches += 1
    if mismatches:
        print(f"TOTAL: {mismatches} mismatches over {n} tokens ({src})")
        sys.exit(1)
    print(f"ORACLE MATCH: {len(ours)} tokens identical to CPython tokenize ({src})")

if __name__ == '__main__':
    main()
