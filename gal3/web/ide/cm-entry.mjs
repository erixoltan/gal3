// CodeMirror 6 bundle entry for the gal IDE.
// Exposes everything the IDE shell needs on window.CM, including the gal
// language mode. Bundled to vendor/cm-bundle.js by build (see package.json).
import {basicSetup} from "codemirror";
import {EditorView, keymap} from "@codemirror/view";
import {EditorState, Compartment} from "@codemirror/state";
import {indentWithTab} from "@codemirror/commands";
import {StreamLanguage} from "@codemirror/language";
import {oneDark} from "@codemirror/theme-one-dark";

// ---------------------------------------------------------------------------
// gal language mode.
//
// gal facts that matter here:
// - line comments: `#` and `//`
// - SEVEN quote styles: ' " ` and the paired curly/angle quotes.
//   Paired quotes have distinct open/close characters and may span lines;
//   straight quotes end at their character (and, gracefully, at EOL).
//   gal strings process no escapes, so there is no backslash handling.
// - keywords are lowercase words; program element names begin with
//   uppercase / underscore / dollar (Pascal_Case_With_Underscores).
// - wordlike operators: s= sgt d= mod and or not ...
// ---------------------------------------------------------------------------

const QUOTE_PAIRS = new Map([
  ["'", "'"],
  ['"', '"'],
  ["`", "`"],
  ["“", "”"], // “ ”
  ["‘", "’"], // ‘ ’
  ["«", "»"], // « »
  ["‹", "›"], // ‹ ›
]);
const MULTILINE_QUOTES = new Set(["”", "’", "»", "›"]);

const KEYWORDS = new Set([
  // structure
  "module", "class", "is", "set", "property", "properties", "method",
  "constructor", "super", "main", "symbol", "function",
  // declarations
  "string", "strings", "number", "numbers", "integer", "integers", "flag",
  "flags", "object", "objects", "list", "lists", "dictionary",
  "dictionaries", "dict", "variant", "variants", "vars", "void", "copy",
  "global",
  // control flow
  "if", "else", "for", "each", "in", "range", "while", "forever", "break",
  "continue", "return", "forgive", "try", "catch", "iterate", "defined",
  "debug", "error",
  // statements
  "say", "verbose", "verbosity", "comment", "flowerbox", "push", "append",
  "replace", "split", "join", "write", "read", "fread", "to", "file",
  "readline", "increment", "decrement", "shell", "capture", "include",
  // values / references
  "my", "self", "me", "new", "null", "true", "false", "line", "tab",
  "indent", "name",
  // wordlike operators
  "not", "and", "or", "mod", "exists", "contains", "isa", "isnull",
  "llength", "lget", "llast", "lfirst", "dget", "dexists", "substring",
  "length", "index",
  // compiler-dialect vocabulary (so compiler sources highlight too)
  "statement", "operation", "syntax", "argument", "optional", "generate",
  "generator", "dialect", "english", "repeating",
]);

const ATOMS = new Set(["null", "true", "false", "self", "me", "line", "tab", "indent", "return"]);

const WORD_OPERATORS = new Set([
  "s=", "s>", "s<", "sgt", "sge", "slt", "sle", "seq", "sne",
  "d=", "l=", "=", "+", "-", "*", "/", ">", "<", ">=", "<=", "!=",
]);

const galLanguage = StreamLanguage.define({
  name: "gal",
  startState() {
    return {closeQuote: null};
  },
  token(stream, state) {
    // inside a multiline (paired-quote) string
    if (state.closeQuote) {
      while (!stream.eol()) {
        if (stream.next() === state.closeQuote) {
          state.closeQuote = null;
          return "string";
        }
      }
      return "string";
    }
    if (stream.eatSpace()) return null;

    // comments
    if (stream.match("//")) { stream.skipToEnd(); return "comment"; }
    if (stream.peek() === "#") { stream.skipToEnd(); return "comment"; }

    const ch = stream.next();

    // strings
    if (QUOTE_PAIRS.has(ch)) {
      const close = QUOTE_PAIRS.get(ch);
      while (!stream.eol()) {
        if (stream.next() === close) return "string";
      }
      // unterminated at EOL: paired quotes continue on the next line,
      // straight quotes end here (gal straight strings are single-line)
      if (MULTILINE_QUOTES.has(close)) state.closeQuote = close;
      return "string";
    }

    // numbers
    if (/[0-9]/.test(ch)) {
      stream.match(/^[0-9]*\.?[0-9]*/);
      return "number";
    }
    if (ch === "-" && /[0-9]/.test(stream.peek() || "")) {
      stream.match(/^[0-9]*\.?[0-9]*/);
      return "number";
    }

    // brackets and grouping
    if (ch === "[" || ch === "]") return "bracket";
    if (ch === "(" || ch === ")" || ch === "{" || ch === "}") return "bracket";
    if (ch === ";" || ch === ",") return "punctuation";

    // words: keywords are lowercase; element names start upper/_/$
    if (/[A-Za-z_$]/.test(ch)) {
      stream.match(/^[A-Za-z0-9_$]*/);
      const word = stream.current();
      if (/^[a-z]/.test(word)) {
        if (ATOMS.has(word)) return "atom";
        if (KEYWORDS.has(word)) return "keyword";
        if (WORD_OPERATORS.has(word)) return "operator";
        return "keyword"; // unknown lowercase word: dialect verb by convention
      }
      return "variableName";
    }

    // punctuation operators (may glue, e.g. s= handled above as word+=;
    // here catch = + - * / < > ! . : etc.)
    if (/[=+\-*/<>!.:]/.test(ch)) {
      stream.match(/^[=+\-*/<>!]*/);
      return "operator";
    }
    return null;
  },
  languageData: {
    commentTokens: {line: "#"},
    closeBrackets: {brackets: ["(", "[", "{", "'", '"', "`"]},
  },
});

window.CM = {
  basicSetup,
  EditorView,
  EditorState,
  Compartment,
  keymap,
  indentWithTab,
  StreamLanguage,
  oneDark,
  galLanguage,
};
