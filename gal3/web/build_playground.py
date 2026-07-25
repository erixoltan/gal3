#!/usr/bin/env python3
"""Assemble a self-contained gal3 browser playground.

Inlines the browser compiler bundle (~/.gal3/galweb.js, produced by
./webbuild) and a handful of example programs into one standalone HTML
file. No server, no external resources: open the result with a browser
(double-click or file://) and the compiler runs in the page.

Rebuild the bundle first if the compiler changed:  ./webbuild
Then:  python3 web/build_playground.py
Output: web/gal-playground.html
"""
import json
import os
import pathlib

HOME = os.environ["HOME"]
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
EXAMPLES = REPO / "examples"

BUNDLE = pathlib.Path(f"{HOME}/.gal3/galweb.js").read_text(encoding="utf-8")
if "</script" in BUNDLE.lower():
    raise SystemExit("bundle contains a </script> sequence; cannot inline safely")

# Ordered so the demo opens on something with visible output.
EXAMPLE_FILES = [
    ("hello", EXAMPLES / "example.txt"),
    ("fizzbuzz", EXAMPLES / "fizzbuzz.txt"),
    ("bank", EXAMPLES / "bank.txt"),
    ("animals — classes & super", EXAMPLES / "animals.txt"),
    ("receipt", EXAMPLES / "receipt.txt"),
]
examples = {name: path.read_text(encoding="utf-8") for name, path in EXAMPLE_FILES}
EXAMPLES_JSON = json.dumps(examples)
if "</script" in EXAMPLES_JSON.lower():
    raise SystemExit("an example contains a </script> sequence; cannot inline safely")

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>gal playground</title>
<style>
:root {
  --paper: #f4f6f8; --pane: #ffffff; --ink: #22272e; --muted: #5b6672;
  --line: #d7dde3; --accent: #0f766e; --accent-ink: #ffffff;
  --run: #b45309; --run-ink: #ffffff; --fail: #b3352b; --chip: #e8ecef;
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #14181c; --pane: #1b2127; --ink: #d6dde3; --muted: #8b97a3;
    --line: #2c343d; --accent: #2dd4bf; --accent-ink: #0c2b27;
    --run: #f5a524; --run-ink: #2b1c03; --fail: #f0776d; --chip: #242c34;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; }
body {
  background: var(--paper); color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 15px; line-height: 1.5; min-height: 100vh;
  display: flex; flex-direction: column;
}
code, pre, textarea, .mono { font-family: ui-monospace, "Cascadia Code", "JetBrains Mono", Menlo, Consolas, monospace; }
header { display: flex; align-items: baseline; gap: 14px; padding: 18px 22px 10px; flex-wrap: wrap; }
.wordmark { font-family: ui-monospace, "Cascadia Code", Menlo, Consolas, monospace; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }
.wordmark .cursor { color: var(--accent); }
.tagline { color: var(--muted); font-size: 14px; }
.strip { display: flex; align-items: center; gap: 6px; padding: 6px 22px 14px; flex-wrap: wrap; }
.chip {
  font-family: ui-monospace, "Cascadia Code", Menlo, Consolas, monospace;
  font-size: 13px; letter-spacing: 0.2px; padding: 5px 12px;
  border: 1px solid var(--line); border-radius: 3px; background: var(--chip);
  color: var(--muted); cursor: pointer;
}
.chip[data-state="done"] { border-color: var(--accent); color: var(--ink); }
.chip[data-state="active"] { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
.chip[data-state="working"] { border-color: var(--accent); color: var(--accent); }
.chip[data-state="failed"] { border-color: var(--fail); color: var(--fail); }
.chip:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.arrow { color: var(--muted); font-size: 12px; user-select: none; }
main { flex: 1; display: grid; grid-template-columns: minmax(320px, 42%) 1fr; gap: 14px; padding: 0 22px 14px; min-height: 0; }
@media (max-width: 860px) { main { grid-template-columns: 1fr; } }
.pane { background: var(--pane); border: 1px solid var(--line); border-radius: 4px; display: flex; flex-direction: column; min-height: 380px; }
.pane-head { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-bottom: 1px solid var(--line); font-size: 13px; color: var(--muted); }
.pane-head select { background: var(--chip); color: var(--ink); border: 1px solid var(--line); border-radius: 3px; padding: 3px 6px; font: inherit; }
.pane-head .spacer { flex: 1; }
button.action {
  font-family: ui-monospace, "Cascadia Code", Menlo, Consolas, monospace;
  font-size: 13px; padding: 5px 14px; border-radius: 3px;
  border: 1px solid var(--accent); background: var(--accent); color: var(--accent-ink); cursor: pointer;
}
button.action.run { border-color: var(--run); background: var(--run); color: var(--run-ink); }
button.action:disabled { opacity: 0.45; cursor: default; }
button.action:focus-visible { outline: 2px solid var(--ink); outline-offset: 1px; }
textarea { flex: 1; width: 100%; border: 0; resize: none; padding: 12px; background: transparent; color: var(--ink); font-size: 13px; line-height: 1.55; min-height: 320px; }
textarea:focus { outline: none; }
pre.out { flex: 1; margin: 0; padding: 12px; overflow: auto; font-size: 12.5px; line-height: 1.5; white-space: pre; }
.log { border-top: 1px solid var(--line); padding: 6px 12px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; color: var(--muted); max-height: 110px; overflow: auto; white-space: pre-wrap; }
.log .err { color: var(--fail); }
footer { padding: 10px 22px 16px; color: var(--muted); font-size: 12.5px; border-top: 1px solid var(--line); }
footer .mono { font-size: 12px; }
@media (prefers-reduced-motion: no-preference) { .chip { transition: background 0.18s, border-color 0.18s, color 0.18s; } }
</style>
</head>
<body>

<header>
  <div class="wordmark">gal<span class="cursor">_</span></div>
  <div class="tagline">the general abstract language &#8212; self-hosting compiler 3.1, running entirely in this page</div>
</header>

<div class="strip" role="tablist" aria-label="pipeline stages">
  <button class="chip" data-stage="source" data-state="active">source</button>
  <span class="arrow">&#8594;</span>
  <button class="chip" data-stage="gal" data-state="">gal</button>
  <span class="arrow">&#8594;</span>
  <button class="chip" data-stage="atomic" data-state="">atomic</button>
  <span class="arrow">&#8594;</span>
  <button class="chip" data-stage="python" data-state="">python</button>
  <button class="chip" data-stage="javascript" data-state="">javascript</button>
  <button class="chip" data-stage="browser" data-state="">browser</button>
  <span class="arrow">&#8594;</span>
  <button class="chip" data-stage="output" data-state="">program output</button>
</div>

<main>
  <section class="pane">
    <div class="pane-head">
      <label for="example">example</label>
      <select id="example"></select>
      <span class="spacer"></span>
      <button class="action" id="compile">compile</button>
      <button class="action run" id="run" disabled>run</button>
    </div>
    <textarea id="editor" spellcheck="false" aria-label="gal source"></textarea>
  </section>
  <section class="pane">
    <div class="pane-head"><span id="pane-title" class="mono">source</span><span class="spacer"></span><span id="pane-meta" class="mono"></span></div>
    <pre class="out" id="out">compile to see each pipeline stage.</pre>
    <div class="log" id="log">the compiler is the ~480&#8202;KB script inlined in this page &#8212; the same bytes node runs. no server, no wasm, no transpiler: gal3 compiled itself to browser JavaScript.</div>
  </section>
</main>

<footer>
  pipeline: gal &#8594; fallback (to fixpoint) &#8594; atomic &#8594; target. every stage this page produces is byte-identical
  to the Python edition&#8217;s output &#8212; the <span class="mono">jsself</span> contract. the <span class="mono">browser</span> target
  is what the <span class="mono">run</span> button executes, right here.
</footer>

<script>
__BUNDLE__
</script>
<script>
"use strict";
var EXAMPLES = __EXAMPLES__;
var $ = function (id) { return document.getElementById(id); };
var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
var stageOrder = ["gal", "atomic", "python", "javascript", "browser"];
var outputs = {};
var logLines = [];

var sel = $("example");
Object.keys(EXAMPLES).forEach(function (name) {
  var o = document.createElement("option");
  o.value = name; o.textContent = name;
  sel.appendChild(o);
});
sel.value = "bank";
$("editor").value = EXAMPLES["bank"];
sel.addEventListener("change", function () {
  $("editor").value = EXAMPLES[sel.value];
  resetStages(); showPane("source");
});
$("editor").addEventListener("input", function () { resetStages(); });

function chip(stage) { return chips.find(function (c) { return c.dataset.stage === stage; }); }
function setState(stage, state) { chip(stage).dataset.state = state; }
function resetStages() {
  outputs = {}; logLines = [];
  stageOrder.concat(["output"]).forEach(function (s) { setState(s, ""); });
  $("run").disabled = true; renderLog();
}
function showPane(stage) {
  chips.forEach(function (c) {
    if (c.dataset.state === "active") {
      c.dataset.state = (outputs[c.dataset.stage] !== undefined || c.dataset.stage === "source") ? "done" : "";
    }
  });
  var c = chip(stage);
  if (c) c.dataset.state = "active";
  $("pane-title").textContent = stage;
  if (stage === "source") {
    $("out").textContent = "compile to see each pipeline stage.";
    $("pane-meta").textContent = "";
  } else {
    var text = outputs[stage];
    $("out").textContent = text !== undefined ? text : "(not produced)";
    $("pane-meta").textContent = text !== undefined ? text.length + " bytes" : "";
  }
}
chips.forEach(function (c) { c.addEventListener("click", function () { showPane(c.dataset.stage); }); });

function renderLog() {
  var el = $("log"); el.innerHTML = "";
  if (!logLines.length) { el.textContent = "ready."; return; }
  logLines.forEach(function (pair) {
    var d = document.createElement("div");
    if (pair[0] === "err") d.className = "err";
    d.textContent = pair[1];
    el.appendChild(d);
  });
  el.scrollTop = el.scrollHeight;
}
function log(kind, text) { logLines.push([kind, text]); renderLog(); }

function captureConsole(fn) {
  var saved = console.log;
  var lines = [];
  console.log = function () { lines.push(Array.prototype.join.call(arguments, " ")); };
  try { fn(); } finally { console.log = saved; }
  return lines;
}

function compileStage(stage, src, tgt) {
  var t0 = performance.now();
  var said = captureConsole(function () { globalThis.Gal_Main(stage, src, tgt); });
  var ms = Math.round(performance.now() - t0);
  said.forEach(function (line) { log("err", stage + ": " + line); });
  if (!globalThis.Gal_Files.has(tgt)) throw new Error(stage + " stage produced no output");
  return ms;
}

$("compile").addEventListener("click", function () {
  resetStages();
  $("compile").disabled = true;
  globalThis.Gal_Files = new Map();
  globalThis.Gal_Files.set("program.txt", $("editor").value);
  var steps = [];
  steps.push(["gal", function () {
    var ms = compileStage("gal", "program.txt", "out.gal");
    outputs.gal = globalThis.Gal_Files.get("out.gal");
    return ms;
  }]);
  steps.push(["atomic", function () {
    var prev = "out.gal", total = 0;
    for (var i = 0; i < 6; i++) {
      var nx = "out.fb" + i;
      total += compileStage("fallback", prev, nx);
      if (globalThis.Gal_Files.get(nx) === globalThis.Gal_Files.get(prev)) { prev = nx; break; }
      prev = nx;
    }
    outputs.atomic = globalThis.Gal_Files.get(prev);
    globalThis.Gal_Files.set("out.atomic", outputs.atomic);
    return total;
  }]);
  ["python", "javascript", "browser"].forEach(function (target) {
    steps.push([target, function () {
      var ms = compileStage(target, "out.atomic", "out." + target);
      outputs[target] = globalThis.Gal_Files.get("out." + target);
      return ms;
    }]);
  });
  var i = 0;
  function next() {
    if (i >= steps.length) {
      $("compile").disabled = false;
      $("run").disabled = false;
      log("info", "pipeline complete — press run to execute the browser target.");
      showPane("browser");
      return;
    }
    var pair = steps[i++];
    var stage = pair[0], fn = pair[1];
    setState(stage, "working");
    setTimeout(function () {
      try {
        var ms = fn();
        setState(stage, "done");
        log("info", stage + " ok (" + ms + " ms)");
        next();
      } catch (e) {
        setState(stage, "failed");
        log("err", stage + " failed: " + e.message);
        $("compile").disabled = false;
        showPane(stage);
      }
    }, 30);
  }
  next();
});

$("run").addEventListener("click", function () {
  var js = outputs.browser;
  if (!js) return;
  var compilerMain = globalThis.Gal_Main;
  try {
    var lines = captureConsole(function () {
      new Function(js)();
      var programMain = globalThis.Gal_Main;
      programMain();
    });
    outputs.output = lines.join("\n") || "(no output)";
    setState("output", "done");
    log("info", "program ran: " + lines.length + " line(s)");
  } catch (e) {
    outputs.output = "runtime error: " + e.message;
    setState("output", "failed");
    log("err", "run failed: " + e.message);
  } finally {
    globalThis.Gal_Main = compilerMain;
  }
  showPane("output");
});

showPane("source");
</script>
</body>
</html>
"""

html = PAGE.replace("__BUNDLE__", BUNDLE).replace("__EXAMPLES__", EXAMPLES_JSON)
out = HERE / "gal-playground.html"
out.write_text(html, encoding="utf-8")
print(f"wrote {out}  ({len(html):,} bytes, bundle {len(BUNDLE):,})")
