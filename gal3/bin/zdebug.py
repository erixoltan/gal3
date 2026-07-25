"""zdebug -- compatibility shim.

The gal3 debugger is now ``pdebug`` (pdb, subclassed and enhanced -- see
``pdebug.py``).  The gal3 language, its Runtime, and every gal3-generated
artifact import ``pdebug`` directly.

This shim exists only for the **gal2 bootstrap step**: the frozen gal2 compiler
(``~/.goalspell/goalspell``) still emits a top-level ``import zdebug`` into the
plain (non-``_3``) artifacts that ``./selfbuild`` executes.  Forwarding the old
name to pdebug keeps that bootstrap working without rebuilding gal2.

Once gal2 is retired (or rebuilt to emit ``pdebug``), this file can be deleted.
"""

from pdebug import *          # noqa: F401,F403  (zbreak, set_trace, pm, ...)
from pdebug import (          # explicit, for `zdebug.<name>` attribute access
    Pdebug,
    zbreak,
    set_trace,
    pm,
    post_mortem,
    run,
    runeval,
    runctx,
    runcall,
)

# Historical alias: old code/tools referred to the class as `Zdebug`.
Zdebug = Pdebug
