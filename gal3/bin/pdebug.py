#!/usr/bin/env python3
"""pdebug -- pdb, enhanced.

Unlike ``zdebug`` (a decade-old *fork* of pdb that has since drifted from the
stdlib), ``pdebug`` *subclasses* the current ``pdb.Pdb`` and layers on only the
three things that were ever worth keeping.  Everything pdb has grown in the
meantime -- source colorizing, ``ll``/``longlist``, ``display``, ``interact``,
tab-completion, ``.pdbrc``, async/await at the prompt -- comes along for free.

What pdebug adds on top of pdb
------------------------------

``ppp expr``   Enhances ``pp``: pretty-prints the value *and* then dumps its
               internal structure -- dict keys, list indices, or object
               attributes -- each on its own truncated line.  Great for peering
               into gal element trees.

``zbreak()``   Drop-in replacement for ``pdb.set_trace()``.  Stops in the
               caller's frame under the visual display.  Optional ``watches``
               are pinned to the display so their values follow you as you step:

                   import pdebug; pdebug.zbreak()
                   import pdebug; pdebug.zbreak(watches=['self', 'i', 'node.Kind'])

Visual mode    On a tty, each prompt repaints the screen: a source window around
               the current line (current line in reverse video), a location
               header, and the watch panel.  Ordinary output (``p``, ``pp``,
               ``ppp``, ``!expr``) is left on screen until you navigate again, so
               you never lose what you just printed.  Toggle with ``visual``.

The gal build lowers ``debug;`` to ``zdebug.zbreak()``.  To move the compiler
onto pdebug, point that lowering at ``pdebug.zbreak()`` (same signature).
"""

import os
import sys
import shutil
import pprint
import linecache

import pdb

__all__ = ["Pdebug", "zbreak", "set_trace", "pm", "post_mortem",
           "run", "runeval", "runctx", "runcall", "main"]

# ANSI control sequences (kept identical in spirit to zdebug's).
CLEAR   = "\x1b[2J\x1b[H"   # clear screen, home cursor
REVERSE = "\x1b[7m"         # reverse video (current line highlight)
RESET   = "\x1b[0m"
DIM     = "\x1b[2m"


# --------------------------------------------------------------------------
# Structural dump used by `ppp` and by zbreak() watches.  Ported from zdebug's
# dbg_zw/dbg_zwobj/dbg_line, but every one now takes an `emit` callback so the
# output honours the debugger's stdout (redirection, capture, remote sessions).
# --------------------------------------------------------------------------

def _emit_default(msg):
    print(msg)


def dbg_zw(arg, emit=_emit_default):
    """Dump the internal structure of *arg* one member per line."""
    if isinstance(arg, str):
        emit('string: "%s"' % arg)
        return
    try:
        ordered = sorted(arg.keys())
    except AttributeError:
        if isinstance(arg, (list, tuple)):
            for key in range(len(arg)):
                dbg_line(key, arg[key], emit)
        else:
            dbg_zwobj(arg, emit)
    else:
        for key in ordered:
            dbg_line(key, arg[key], emit)
    emit('')


def dbg_zwobj(arg, emit=_emit_default):
    """Dump the public, non-method attributes of an object."""
    for key in sorted(dir(arg)):
        if key[:2] == '__':
            continue
        try:
            value = getattr(arg, key)
        except Exception:
            continue
        dbg_line(key, value, emit)


def dbg_line(key, value, emit=_emit_default):
    """Emit one `key = value` line, hiding bound methods, truncating long reprs."""
    if "<bound method " in str(value):
        return
    if isinstance(value, str):
        value = "'%s'" % value
    else:
        value = str(value)
    if len(value) > 100:
        value = "%s..." % value[:100]
    emit("   %s = %s" % (key, value))


# --------------------------------------------------------------------------
# The debugger.
# --------------------------------------------------------------------------

class Pdebug(pdb.Pdb):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.prompt = 'pdebug> '
        # Expressions pinned to the visual display (evaluated in the current
        # frame on every repaint).  Seeded by zbreak(watches=...).
        self.watches = []
        # Repaint the source window on the next prompt.  Set by a fresh stop
        # (preloop) and by view-moving commands (up/down); cleared once drawn so
        # that plain output like `p x` survives on screen.
        self.Redisplay = True
        # Full-screen visual mode: only when writing to a real terminal.
        self.visual = getattr(self, 'use_rawinput', True) and _stdout_is_tty()

    # ---- visual redisplay -------------------------------------------------
    # pdb 3.x no longer uses preloop/postcmd, so they are ours to drive the
    # repaint without reimplementing cmd.Cmd.cmdloop.

    def preloop(self):
        super().preloop()
        # A fresh stop (breakpoint / step landing) always repaints.
        self.Redisplay = True

    def postcmd(self, stop, line):
        stop = super().postcmd(stop, line)
        # Repaint right before the next prompt, but not while resuming (stop is
        # truthy -> we're leaving; the next stop's preloop paints instead).
        if not stop and self.Redisplay and self.visual:
            self.ShowContext()
        return stop

    def ShowContext(self):
        """Clear the screen and paint header + source window + watches."""
        if not self.curframe:
            return
        self.Redisplay = False
        frame = self.curframe
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        term = shutil.get_terminal_size((80, 24))
        watch_rows = len(self.watches) + (2 if self.watches else 0)
        window = max(5, term.lines - watch_rows - 4)
        before = window // 2
        first = max(1, lineno - before)
        last = first + window - 1

        breaklist = self.get_file_breaks(filename)
        lines = linecache.getlines(filename, frame.f_globals)

        out = self.stdout
        out.write(CLEAR)
        out.write("%s> %s(%d) %s%s\n" %
                  (DIM, os.path.basename(filename), lineno,
                   frame.f_code.co_name, RESET))
        self._print_lines(lines[first - 1:last], first, breaklist, frame)
        if len(lines) < last:
            self.message('[EOF]')
        self._print_watches(frame)
        out.flush()

    def _print_watches(self, frame):
        if not self.watches:
            return
        self.message("%s-- watches --%s" % (DIM, RESET))
        for expr in self.watches:
            try:
                value = eval(expr, frame.f_globals, frame.f_locals)
                value = repr(value)
            except Exception as exc:
                value = "<%s: %s>" % (type(exc).__name__, exc)
            if len(value) > term_width() - len(expr) - 6:
                value = value[:term_width() - len(expr) - 9] + '...'
            self.message("  %s = %s" % (expr, value))

    def _print_lines(self, lines, start, breaks=(), frame=None):
        """Like pdb's, but the current line is shown in reverse video."""
        if frame:
            current_lineno = frame.f_lineno
            exc_lineno = self.tb_lineno.get(frame, -1)
        else:
            current_lineno = exc_lineno = -1
        for lineno, line in enumerate(lines, start):
            s = str(lineno).rjust(3)
            if len(s) < 4:
                s += ' '
            s += 'B' if lineno in breaks else ' '
            body = line.rstrip()
            if lineno == current_lineno:
                # Reverse video reads clearly regardless of theme; skip
                # colorizing here so the ANSI resets don't fight each other.
                self.message("%s%s\t%s%s" % (REVERSE, s, body, RESET))
            else:
                if getattr(self, 'colorize', False):
                    body = self._colorize_code(line).rstrip()
                self.message("%s\t%s" % (s, body))

    # ---- view-moving commands trigger a repaint ---------------------------
    # (Stepping/continuing repaint via preloop on the next stop; up/down do not
    #  resume, so they must ask for the repaint themselves.)

    def do_up(self, arg):
        retval = super().do_up(arg)
        self.Redisplay = True
        return retval
    do_u = do_up

    def do_down(self, arg):
        retval = super().do_down(arg)
        self.Redisplay = True
        return retval
    do_d = do_down

    def do_visual(self, arg):
        """visual [on|off]
        Toggle the full-screen source window.  With `off`, pdebug behaves like
        plain pdb; with `on`, the screen repaints around the current line.
        """
        arg = arg.strip().lower()
        if arg in ('on', '1', 'true', ''):
            self.visual = _stdout_is_tty()
            if arg == '' and not self.visual:
                self.visual = False
        elif arg in ('off', '0', 'false'):
            self.visual = False
        self.Redisplay = self.visual
        self.message("visual mode %s" % ("on" if self.visual else "off"))

    # ---- ppp: pp, then the structural breakdown ---------------------------

    def do_ppp(self, arg):
        """ppp expression

        Enhanced pp: pretty-print the value of the expression, then dump its
        internal structure -- dict keys, list/tuple indices, or (for objects)
        public attributes -- one truncated `name = value` per line.  Bound
        methods are omitted.  Ideal for inspecting gal element trees.
        """
        if not arg:
            self._print_invalid_arg(arg)
            return
        try:
            value = self._getval(arg)
        except Exception:
            return  # _getval already reported the error
        # The `pp` half.
        self.message(pprint.pformat(value))
        # The structural half.
        dbg_zw(value, self.message)

    complete_ppp = pdb.Pdb._complete_expression

    # ---- watch management -------------------------------------------------

    def do_watch(self, arg):
        """watch [expression]
        Pin an expression to the visual display; its value is re-evaluated in
        the current frame on every repaint and follows you as you step.  With no
        argument, list the current watches.
        """
        arg = arg.strip()
        if not arg:
            if not self.watches:
                self.message("No watches.")
            for expr in self.watches:
                self.message("  %s" % expr)
            return
        if arg not in self.watches:
            self.watches.append(arg)
        self.Redisplay = True

    complete_watch = pdb.Pdb._complete_expression

    def do_unwatch(self, arg):
        """unwatch [expression]
        Remove a watch (or all watches, with no argument).
        """
        arg = arg.strip()
        if not arg:
            self.watches.clear()
        elif arg in self.watches:
            self.watches.remove(arg)
        self.Redisplay = True

    def complete_unwatch(self, text, line, begidx, endidx):
        return [w for w in self.watches if w.startswith(text)]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _stdout_is_tty():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def term_width():
    return shutil.get_terminal_size((80, 24)).columns


# --------------------------------------------------------------------------
# module-level entry points  (mirrors pdb's, but instantiates Pdebug)
# --------------------------------------------------------------------------

def zbreak(watches=None, frame=None, *, header=None, commands=None):
    """Replacement for pdb.set_trace(): stop in the caller's frame.

    watches   list of expressions to pin to the visual display.
    header    optional message printed before stopping.
    commands  optional list of pdb commands run on entry (e.g. ['ll']).
    """
    if frame is None:
        frame = sys._getframe().f_back
    dbg = Pdebug()
    if watches:
        dbg.watches.extend(watches)
    if header is not None:
        dbg.message(header)
    dbg.set_trace(frame, commands=commands)
    return dbg


# Drop-in alias so existing `set_trace()` call sites need no change.
set_trace = zbreak


def post_mortem(t=None):
    if t is None:
        t = sys.exc_info()[2]
    if t is None:
        raise ValueError("A valid traceback must be passed if no "
                         "exception is being handled")
    p = Pdebug()
    p.reset()
    p.interaction(None, t)


def pm():
    post_mortem(sys.last_exc.__traceback__ if hasattr(sys, 'last_exc')
                else sys.last_traceback)


def run(statement, globals=None, locals=None):
    Pdebug().run(statement, globals, locals)


def runeval(expression, globals=None, locals=None):
    return Pdebug().runeval(expression, globals, locals)


def runctx(statement, globals, locals):
    run(statement, globals, locals)


def runcall(*args, **kwds):
    return Pdebug().runcall(*args, **kwds)


def main():
    """`python pdebug.py script.py [args...]` -- run a script under pdebug."""
    import runpy
    if len(sys.argv) < 2:
        print("usage: pdebug.py script.py [args...]", file=sys.stderr)
        sys.exit(2)
    target = sys.argv[1]
    sys.argv = sys.argv[1:]
    dbg = Pdebug()
    dbg._wait_for_mainpyfile = True
    dbg.mainpyfile = dbg.canonic(target)
    sys.path[0] = os.path.dirname(os.path.abspath(target))
    try:
        dbg._run(pdb._ScriptTarget(target))
    except AttributeError:
        # Very old/new pdb without _ScriptTarget: fall back to runpy.
        dbg.run("runpy.run_path(%r, run_name='__main__')" % target,
                {'runpy': runpy})


if __name__ == '__main__':
    main()
