/* gal ide — main logic. CodeMirror bits come from window.CM (vendor
   bundle); the compiler lives in a Worker built from the text/plain
   script tag (galweb.js + protocol). */
(function () {
"use strict";
var CM = window.CM;
var $ = function (id) { return document.getElementById(id); };

/* ---------------- editors ---------------- */
var themeCompartment = new CM.Compartment();
var stageThemeCompartment = new CM.Compartment();
var darkMedia = window.matchMedia("(prefers-color-scheme: dark)");
function themeExt(compartment) {
    return compartment.of(darkMedia.matches ? CM.oneDark : []);
}
var sourceView = new CM.EditorView({
    state: CM.EditorState.create({
        doc: "",
        extensions: [
            CM.basicSetup,
            CM.galLanguage,
            CM.keymap.of([
                CM.indentWithTab,
                { key: "Mod-Enter", run: function () { compile(); return true; } },
                { key: "Mod-s", run: function () { save(); return true; }, preventDefault: true },
            ]),
            themeExt(themeCompartment),
            CM.EditorView.updateListener.of(function (u) {
                if (u.docChanged) onSourceEdited();
            }),
        ],
    }),
    parent: $("source-host"),
});
var stageView = new CM.EditorView({
    state: CM.EditorState.create({
        doc: "",
        extensions: [CM.basicSetup, CM.EditorState.readOnly.of(true), themeExt(stageThemeCompartment)],
    }),
    parent: $("stage-host"),
});
darkMedia.addEventListener("change", function () {
    var t = darkMedia.matches ? CM.oneDark : [];
    sourceView.dispatch({ effects: themeCompartment.reconfigure(t) });
    stageView.dispatch({ effects: stageThemeCompartment.reconfigure(t) });
});
function sourceText() { return sourceView.state.doc.toString(); }

/* ---------------- worker ---------------- */
var workerSrc = $("worker-src").textContent;
var worker = null;
var workerReady = false;
var busy = false;      // a compile or run is in flight
var msgId = 0;
var outputs = {};      // gal / atomic / <target> / browser
var pending = {};      // id -> kind

function spawnWorker() {
    if (worker) worker.terminate();
    workerReady = false;
    var blob = new Blob([workerSrc], { type: "text/javascript" });
    worker = new Worker(URL.createObjectURL(blob));
    worker.onmessage = onWorkerMessage;
}
function onWorkerMessage(ev) {
    var m = ev.data;
    if (m.type === "ready") { workerReady = true; return; }
    if (m.type === "stage") {
        var tab = stageToTab(m.stage);
        if (m.state === "start") {
            logLine("dim", m.stage + "…");
        } else if (m.state === "done") {
            logLine("dim", m.stage + " ok (" + m.ms + " ms)");
            if (tab) tabEl(tab).disabled = false;
        } else {
            (m.log || []).forEach(function (l) { logLine("err", m.stage + ": " + l); });
            logLine("err", m.stage + " failed");
            if (tab) { tabEl(tab).disabled = false; tabEl(tab).classList.add("failed"); }
        }
        return;
    }
    if (m.type === "compiled") {
        busy = false; setBusyUi();
        outputs = m.outputs || {};
        if (m.ok) {
            logLine("", "compiled - run to execute, or open the stage tabs.");
            $("run").disabled = !outputs.browser;
        }
        return;
    }
    if (m.type === "ran") {
        busy = false; setBusyUi();
        setOutputTitle("program output");
        setOutputText(m.output, m.ok ? "" : "err");
        if (!m.ok) logLine("err", m.output);
        return;
    }
}
function stageToTab(stage) {
    if (stage === "gal" || stage === "atomic") return stage;
    if (stage === $("target").value) return "target";
    return null; // the extra browser compile backing the run button
}

/* ---------------- output panel ---------------- */
var outEl = $("output");
function logLine(cls, text) {
    var d = document.createElement("div");
    if (cls) d.className = cls;
    d.textContent = text;
    outEl.appendChild(d);
    outEl.scrollTop = outEl.scrollHeight;
    showOutput(true);
}
function clearLog() { outEl.textContent = ""; setOutputTitle("output"); }
function setOutputTitle(t) { $("output-title").textContent = t; }
function setOutputText(text, cls) {
    clearLog();
    var d = document.createElement("div");
    if (cls) d.className = cls;
    d.textContent = text;
    outEl.appendChild(d);
    showOutput(true);
}
function showOutput(show) { document.body.classList.toggle("output-hidden", !show); }
$("out-toggle").addEventListener("click", function () {
    document.body.classList.toggle("output-hidden");
});
$("out-close").addEventListener("click", function () { showOutput(false); });

/* ---------------- stage tabs ---------------- */
function tabEl(stage) { return document.querySelector('.stage-tab[data-stage="' + stage + '"]'); }
var activeTab = "source";
function selectTab(stage) {
    activeTab = stage;
    document.querySelectorAll(".stage-tab").forEach(function (t) {
        if (t.dataset.stage === stage) t.dataset.on = "1"; else delete t.dataset.on;
    });
    if (stage === "source") {
        $("stage-host").hidden = true;
        $("source-host").hidden = false;
        sourceView.focus();
    } else {
        var key = stage === "target" ? $("target").value : stage;
        var text = outputs[key];
        stageView.setState(CM.EditorState.create({
            doc: text !== undefined ? text : "(not produced)",
            extensions: [CM.basicSetup, CM.EditorState.readOnly.of(true),
                stageThemeCompartment.of(darkMedia.matches ? CM.oneDark : []),
                (stage === "gal" || stage === "atomic") ? CM.galLanguage : []],
        }));
        $("source-host").hidden = true;
        $("stage-host").hidden = false;
    }
}
document.querySelectorAll(".stage-tab").forEach(function (t) {
    t.addEventListener("click", function () { if (!t.disabled) selectTab(t.dataset.stage); });
});
function invalidateStages() {
    outputs = {};
    ["gal", "atomic", "target"].forEach(function (s) {
        var t = tabEl(s);
        t.disabled = true; t.classList.remove("failed");
    });
    $("run").disabled = true;
    if (activeTab !== "source") selectTab("source");
}

/* ---------------- compile / run / stop ---------------- */
function setBusyUi() {
    $("compile").disabled = busy;
    $("run").disabled = busy || !outputs.browser;
    $("stop").hidden = !busy;
    $("target").disabled = busy;
}
function compile() {
    if (busy) return;
    invalidateStages();
    clearLog();
    busy = true; setBusyUi();
    if (!worker || !workerReady) spawnWorker();
    worker.postMessage({ cmd: "compile", id: ++msgId, source: sourceText(), target: $("target").value });
}
function run() {
    if (busy || !outputs.browser) return;
    busy = true; setBusyUi();
    setOutputTitle("running…");
    if (!worker || !workerReady) {
        spawnWorker();
    }
    worker.postMessage({ cmd: "run", id: ++msgId, js: outputs.browser });
}
function stop() {
    if (!busy) return;
    spawnWorker(); // terminate + fresh worker
    busy = false; setBusyUi();
    logLine("err", "stopped.");
}
$("compile").addEventListener("click", compile);
$("run").addEventListener("click", run);
$("stop").addEventListener("click", stop);
$("target").addEventListener("change", function () {
    $("target-tab").textContent = $("target").selectedOptions[0].textContent;
    invalidateStages();
});

/* ---------------- storage ---------------- */
/* Provider contract (Phase B adds a Remote provider speaking to the
   generalabstractlanguage.com app server behind the same three calls). */
var LocalProvider = {
    open: function () {
        if (window.showOpenFilePicker) {
            return window.showOpenFilePicker({
                types: [{ description: "gal source", accept: { "text/plain": [".gal", ".txt"] } }],
            }).then(function (handles) {
                var h = handles[0];
                return h.getFile().then(function (f) {
                    return f.text().then(function (text) { return { name: f.name, text: text, handle: h }; });
                });
            });
        }
        return new Promise(function (resolve, reject) {
            var input = document.createElement("input");
            input.type = "file";
            input.accept = ".gal,.txt,text/plain";
            input.onchange = function () {
                var f = input.files[0];
                if (!f) { reject(new Error("cancelled")); return; }
                f.text().then(function (text) { resolve({ name: f.name, text: text, handle: null }); });
            };
            input.click();
        });
    },
    save: function (file) {
        if (file.handle && file.handle.createWritable) {
            return file.handle.createWritable().then(function (w) {
                return w.write(file.text).then(function () { return w.close(); });
            }).then(function () { return file; });
        }
        return LocalProvider.saveAs(file);
    },
    saveAs: function (file) {
        if (window.showSaveFilePicker) {
            return window.showSaveFilePicker({
                suggestedName: file.name,
                types: [{ description: "gal source", accept: { "text/plain": [".gal"] } }],
            }).then(function (h) {
                return h.createWritable().then(function (w) {
                    return w.write(file.text).then(function () { return w.close(); });
                }).then(function () {
                    return h.getFile().then(function (f) { return { name: f.name, text: file.text, handle: h }; });
                });
            });
        }
        // fallback: push a download; the browser decides where it lands
        var blob = new Blob([file.text], { type: "text/plain" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = file.name;
        a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000);
        return Promise.resolve({ name: file.name, text: file.text, handle: null });
    },
};
/* Remote provider (Phase B): files live on the generalabstractlanguage.com
   app server; available when the IDE is served same-origin with /api/. */
function apiFetch(path, options) {
    return fetch(path, options).then(function (r) {
        var kind = r.headers.get("Content-Type") || "";
        var parse = kind.indexOf("json") >= 0 ? r.json() : r.text();
        return parse.then(function (body) { return { status: r.status, body: body }; });
    });
}
var RemoteProvider = {
    open: function () {
        return apiFetch("/api/files").then(function (r) {
            if (r.status !== 200) throw new Error("not signed in");
            return pickServerFile(r.body.Files || []);
        }).then(function (name) {
            return apiFetch("/api/files/" + name).then(function (r) {
                if (r.status !== 200) throw new Error("could not load " + name);
                return { name: name, text: r.body, handle: "remote" };
            });
        });
    },
    save: function (file) {
        if (file.name === "untitled.gal") return RemoteProvider.saveAs(file);
        return apiFetch("/api/files/" + file.name, { method: "PUT", body: file.text })
            .then(function (r) {
                if (r.status !== 200) throw new Error(r.body && r.body.Error || "save failed");
                return { name: file.name, text: file.text, handle: "remote" };
            });
    },
    saveAs: function (file) {
        return askText("save on server as", file.name).then(function (name) {
            return RemoteProvider.save({ name: name, text: file.text, handle: "remote" });
        });
    },
};
var provider = LocalProvider;
var signedIn = null;
function setSignedIn(user) {
    signedIn = user;
    provider = user ? RemoteProvider : LocalProvider;
    $("m-signin").hidden = !!user;
    $("m-signout").hidden = !user;
    $("m-signout").textContent = user ? "sign out (" + user + ")" : "sign out";
    $("drawer-status").innerHTML = user
        ? 'signed in as <span class="mono">' + user + '</span> - files on the server.'
        : 'gal ide 3.1.1<br>the compiler runs in this page.<br><span class="mono">ctrl+enter</span> compile &#183; <span class="mono">ctrl+s</span> save';
}

/* ---- modal machinery ---- */
function openModal(build) {
    var m = $("modal");
    m.innerHTML = "";
    $("modal-scrim").hidden = false;
    m.hidden = false;
    return new Promise(function (resolve, reject) {
        function close(value, ok) {
            m.hidden = true; $("modal-scrim").hidden = true; m.innerHTML = "";
            $("modal-scrim").onclick = null;
            if (ok) resolve(value); else reject(new Error("cancelled"));
        }
        $("modal-scrim").onclick = function () { close(null, false); };
        build(m, close);
    });
}
function askText(title, initial) {
    return openModal(function (m, close) {
        var h = document.createElement("h2"); h.textContent = title;
        var input = document.createElement("input");
        input.value = initial || ""; input.spellcheck = false;
        var err = document.createElement("div"); err.className = "modal-err";
        var row = document.createElement("div"); row.className = "modal-row";
        var cancel = document.createElement("button"); cancel.className = "act plain"; cancel.textContent = "cancel";
        var ok = document.createElement("button"); ok.className = "act"; ok.textContent = "ok";
        cancel.onclick = function () { close(null, false); };
        function submit() {
            var v = input.value.trim();
            if (!v) { err.textContent = "name required"; return; }
            close(v, true);
        }
        ok.onclick = submit;
        input.onkeydown = function (e) { if (e.key === "Enter") submit(); if (e.key === "Escape") close(null, false); };
        row.appendChild(cancel); row.appendChild(ok);
        m.appendChild(h); m.appendChild(input); m.appendChild(err); m.appendChild(row);
        input.focus(); input.select();
    });
}
function pickServerFile(files) {
    return openModal(function (m, close) {
        var h = document.createElement("h2"); h.textContent = "your files";
        m.appendChild(h);
        var list = document.createElement("div"); list.className = "file-list";
        if (!files.length) {
            var none = document.createElement("div"); none.className = "modal-err";
            none.textContent = "no files yet - save one first.";
            m.appendChild(none);
        }
        files.forEach(function (f) {
            var b = document.createElement("button"); b.className = "file-item";
            var n = document.createElement("span"); n.textContent = f.Name;
            var sz = document.createElement("span"); sz.className = "dim"; sz.textContent = f.Size + " b";
            b.appendChild(n); b.appendChild(sz);
            b.onclick = function () { close(f.Name, true); };
            list.appendChild(b);
        });
        m.appendChild(list);
        var row = document.createElement("div"); row.className = "modal-row";
        var cancel = document.createElement("button"); cancel.className = "act plain"; cancel.textContent = "cancel";
        cancel.onclick = function () { close(null, false); };
        row.appendChild(cancel);
        m.appendChild(row);
    });
}
function signInDialog() {
    return openModal(function (m, close) {
        var h = document.createElement("h2"); h.textContent = "sign in";
        var user = document.createElement("input"); user.placeholder = "user"; user.autocapitalize = "none";
        var pass = document.createElement("input"); pass.placeholder = "password"; pass.type = "password";
        var err = document.createElement("div"); err.className = "modal-err";
        var row = document.createElement("div"); row.className = "modal-row";
        var cancel = document.createElement("button"); cancel.className = "act plain"; cancel.textContent = "cancel";
        var ok = document.createElement("button"); ok.className = "act"; ok.textContent = "sign in";
        cancel.onclick = function () { close(null, false); };
        function submit() {
            apiFetch("/api/login", { method: "POST", body: JSON.stringify({ User: user.value.trim(), Password: pass.value }) })
                .then(function (r) {
                    if (r.status === 200) { close(r.body.User, true); }
                    else { err.textContent = (r.body && r.body.Error) || "sign in failed"; }
                })
                .catch(function () { err.textContent = "no server here - open the ide from the gal site to use server files."; });
        }
        ok.onclick = submit;
        pass.onkeydown = function (e) { if (e.key === "Enter") submit(); };
        row.appendChild(cancel); row.appendChild(ok);
        m.appendChild(h); m.appendChild(user); m.appendChild(pass); m.appendChild(err); m.appendChild(row);
        user.focus();
    });
}
$("m-signin").addEventListener("click", function () {
    toggleDrawer(false);
    signInDialog().then(function (user) { setSignedIn(user); }).catch(function () {});
});
$("m-signout").addEventListener("click", function () {
    toggleDrawer(false);
    apiFetch("/api/logout", { method: "POST" }).catch(function () {}).then(function () { setSignedIn(null); });
});
/* boot-time session probe: only meaningful when served from the site */
apiFetch("/api/session").then(function (r) {
    if (r.status === 200 && r.body && r.body.User) setSignedIn(r.body.User);
}).catch(function () {});

var current = { name: "untitled.gal", handle: null, savedText: "" };
function setDirtyUi() {
    var dirty = sourceText() !== current.savedText;
    $("filename").textContent = current.name;
    $("filename").classList.toggle("dirty", dirty);
    return dirty;
}
function loadIntoEditor(name, text, handle, savedText) {
    current = { name: name, handle: handle, savedText: savedText };
    sourceView.setState(CM.EditorState.create({
        doc: text,
        extensions: [
            CM.basicSetup, CM.galLanguage,
            CM.keymap.of([
                CM.indentWithTab,
                { key: "Mod-Enter", run: function () { compile(); return true; } },
                { key: "Mod-s", run: function () { save(); return true; }, preventDefault: true },
            ]),
            themeCompartment.of(darkMedia.matches ? CM.oneDark : []),
            CM.EditorView.updateListener.of(function (u) { if (u.docChanged) onSourceEdited(); }),
        ],
    }));
    invalidateStages();
    selectTab("source");
    setDirtyUi();
}
function newFile() {
    if (setDirtyUi() && !window.confirm("discard unsaved changes?")) return;
    loadIntoEditor("untitled.gal", "", null, "");
    localStorage.removeItem(AUTOSAVE_KEY);
    clearLog();
}
function openFile() {
    if (setDirtyUi() && !window.confirm("discard unsaved changes?")) return;
    provider.open().then(function (f) {
        loadIntoEditor(f.name, f.text, f.handle, f.text);
    }).catch(function () {});
}
function save() {
    var file = { name: current.name, text: sourceText(), handle: current.handle };
    provider.save(file).then(function (f) {
        current.name = f.name; current.handle = f.handle; current.savedText = f.text;
        setDirtyUi();
    }).catch(function () {});
}
function saveAs() {
    var file = { name: current.name, text: sourceText(), handle: null };
    provider.saveAs(file).then(function (f) {
        current.name = f.name; current.handle = f.handle; current.savedText = f.text;
        setDirtyUi();
    }).catch(function () {});
}

/* autosave: the editor never loses work between visits */
var AUTOSAVE_KEY = "gal-ide:autosave";
var autosaveTimer = null;
function onSourceEdited() {
    invalidateStages();
    setDirtyUi();
    if (autosaveTimer) clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(function () {
        try {
            localStorage.setItem(AUTOSAVE_KEY, JSON.stringify({ name: current.name, text: sourceText() }));
        } catch (e) {}
    }, 400);
}
window.addEventListener("beforeunload", function (e) {
    if (setDirtyUi()) { e.preventDefault(); e.returnValue = ""; }
});

/* ---------------- drawer ---------------- */
function toggleDrawer(open) {
    var d = $("drawer");
    var show = open !== undefined ? open : d.hidden;
    if (show) {
        var r = $("menu-btn").getBoundingClientRect();
        d.style.top = (r.bottom + 4) + "px";
        d.style.left = Math.max(6, r.left) + "px";
    }
    d.hidden = !show;
    $("scrim").hidden = !show;
    $("menu-btn").setAttribute("aria-expanded", show ? "true" : "false");
}
window.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !$("drawer").hidden) toggleDrawer(false);
});
$("menu-btn").addEventListener("click", function () { toggleDrawer(); });
$("scrim").addEventListener("click", function () { toggleDrawer(false); });
$("m-new").addEventListener("click", function () { toggleDrawer(false); newFile(); });
$("m-open").addEventListener("click", function () { toggleDrawer(false); openFile(); });
$("m-save").addEventListener("click", function () { toggleDrawer(false); save(); });
$("m-saveas").addEventListener("click", function () { toggleDrawer(false); saveAs(); });

/* ---------------- boot ---------------- */
spawnWorker();
showOutput(false);
var restored = null;
try { restored = JSON.parse(localStorage.getItem(AUTOSAVE_KEY) || "null"); } catch (e) {}
if (restored && restored.text) {
    loadIntoEditor(restored.name || "untitled.gal", restored.text, null, "");
    setDirtyUi();
} else {
    loadIntoEditor("untitled.gal", "", null, "");
}
$("target-tab").textContent = $("target").selectedOptions[0].textContent;
})();
