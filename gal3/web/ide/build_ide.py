#!/usr/bin/env python3
"""Assemble the standalone gal IDE: one self-contained HTML file.

Inlines: the CodeMirror bundle (vendor/cm-bundle.js — rebuild with
`npm run bundle` after editing cm-entry.mjs), the compiler
(~/.gal3/galweb.js — rebuild with ../../webbuild), the worker protocol,
the stylesheet and the IDE logic, into web/ide/gal-ide.html.

The compiler + protocol ride in a <script type="text/plain"> tag (the
worker is built from its textContent), so neither may contain the
literal "</script".
"""
import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
HOME = os.environ["HOME"]

def read(p):
    return pathlib.Path(p).read_text(encoding="utf-8")

shell = read(HERE / "shell.html")
css = read(HERE / "ide.css")
cm = read(HERE / "vendor/cm-bundle.js")
galweb_installed = pathlib.Path(f"{HOME}/.gal3/galweb.js")
galweb_built = pathlib.Path(f"{HOME}/code/gal3build/galweb.js")
galweb_path = galweb_installed if galweb_installed.exists() else galweb_built
print(f"compiler bundle: {galweb_path}")
galweb = read(galweb_path)
protocol = read(HERE / "worker-protocol.js")
ide_js = read(HERE / "ide.js")

worker_src = galweb + "\n" + protocol
for name, text in [("cm-bundle", cm), ("worker source", worker_src), ("ide.js", ide_js)]:
    if "</script" in text.lower():
        raise SystemExit(f"{name} contains a </script> sequence; cannot inline")

html = (shell
        .replace("__CSS__", css)
        .replace("__CM_BUNDLE__", cm)
        .replace("__WORKER_SRC__", worker_src)
        .replace("__IDE_JS__", ide_js))

out = HERE / "gal-ide.html"
out.write_text(html, encoding="utf-8")
print(f"wrote {out}  ({len(html):,} bytes)")

# artifact variant: hosts that provide their own <!doctype>/<head>/<body>
# skeleton get just the inner content (title + style + body innards)
inner = html
inner = inner.split("<head>", 1)[1]
inner = inner.replace("</head>", "").replace("<body>", "")
inner = inner.replace("</body>", "").replace("</html>", "")
inner = "\n".join(line for line in inner.splitlines()
                  if "<!doctype" not in line.lower() and "<html" not in line.lower()
                  and '<meta charset' not in line and '<meta name="viewport"' not in line)
art = HERE / "gal-ide.artifact.html"
art.write_text(inner, encoding="utf-8")
print(f"wrote {art}  ({len(inner):,} bytes)")
