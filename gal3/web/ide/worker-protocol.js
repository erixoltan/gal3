// gal IDE compile/run worker protocol.
// This file is appended AFTER galweb.js inside the worker source blob, so
// globalThis.Gal_Main and Gal_Files come from the compiler bundle above.
// The worker is STATELESS between messages: 'run' carries the program text
// with it, so the main thread can terminate a hung worker and respawn
// without losing anything.
// CAUTION: the compiler bundle lexically shadows several built-ins for all
// later code in this scope (its sources declare String, Number, Symbol and
// Date classes) — always reach built-ins through globalThis here.
(function () {
    "use strict";
    function capture(fn) {
        var saved = console.log;
        var lines = [];
        console.log = function () { lines.push(Array.prototype.join.call(arguments, " ")); };
        try { fn(); } finally { console.log = saved; }
        return lines;
    }

    function stage(id, name, fn) {
        self.postMessage({ type: "stage", id: id, stage: name, state: "start" });
        var t0 = globalThis.Date.now();
        var said = [];
        try {
            said = fn();
            self.postMessage({ type: "stage", id: id, stage: name, state: "done", ms: globalThis.Date.now() - t0, log: said });
            return true;
        } catch (e) {
            self.postMessage({ type: "stage", id: id, stage: name, state: "failed", ms: globalThis.Date.now() - t0, log: said.concat([globalThis.String(e && e.message ? e.message : e)]) });
            return false;
        }
    }

    function compileOne(target, src, tgt) {
        var said = capture(function () { globalThis.Gal_Main(target, src, tgt); });
        if (!globalThis.Gal_Files.has(tgt)) {
            throw new Error(said.length ? said.join("; ") : target + " produced no output");
        }
        return said;
    }

    self.onmessage = function (ev) {
        var m = ev.data;
        if (m.cmd === "compile") {
            var outputs = {};
            globalThis.Gal_Files = new Map();
            globalThis.Gal_Files.set("program.txt", m.source);

            var ok = stage(m.id, "gal", function () {
                var said = compileOne("gal", "program.txt", "out.gal");
                outputs.gal = globalThis.Gal_Files.get("out.gal");
                return said;
            });
            ok = ok && stage(m.id, "atomic", function () {
                var said = [];
                var prev = "out.gal";
                for (var i = 0; i < 6; i++) {
                    var nx = "out.fb" + i;
                    said = said.concat(compileOne("fallback", prev, nx));
                    if (globalThis.Gal_Files.get(nx) === globalThis.Gal_Files.get(prev)) { prev = nx; break; }
                    prev = nx;
                }
                outputs.atomic = globalThis.Gal_Files.get(prev);
                globalThis.Gal_Files.set("out.atomic", outputs.atomic);
                return said;
            });
            // the selected target for display, plus browser for the run button
            var targets = m.target === "browser" ? ["browser"] : [m.target, "browser"];
            for (var t = 0; ok && t < targets.length; t++) {
                (function (target) {
                    ok = stage(m.id, target, function () {
                        var said = compileOne(target, "out.atomic", "out." + target);
                        outputs[target] = globalThis.Gal_Files.get("out." + target);
                        return said;
                    });
                })(targets[t]);
            }
            self.postMessage({ type: "compiled", id: m.id, ok: ok, outputs: outputs });
        }
        else if (m.cmd === "run") {
            var compilerMain = globalThis.Gal_Main;
            try {
                var lines = capture(function () {
                    new Function(m.js)();
                    var programMain = globalThis.Gal_Main;
                    programMain();
                });
                self.postMessage({ type: "ran", id: m.id, ok: true, output: lines.join("\n") });
            } catch (e) {
                self.postMessage({ type: "ran", id: m.id, ok: false, output: "runtime error: " + (e && e.message ? e.message : e) });
            } finally {
                globalThis.Gal_Main = compilerMain;
            }
        }
    };
    self.postMessage({ type: "ready" });
})();
