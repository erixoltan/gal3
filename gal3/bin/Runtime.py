"""gal3 runtime -- minimal.

Only the helpers that gal-generated Python actually calls. The gal2-era
runtime (LLM synthesis, memory events, ed scripts, shell capture) lived here
too and dragged in ollama/mcp/requests on every compiler process start; gal3
generates Runtime references on demand (Python_Runtime_Include), so this
module must stay import-cheap. History is in git if a helper is ever missed.
"""

import os
import datetime
import random


class Runtime:
    @classmethod
    def Enquote(cls, Text):
        if not "'" in Text:
            return "'" + Text + "'"
        if not '"' in Text:
            return '"' + Text + '"'
        if not '`' in Text:
            return '`' + Text + '`'
        if (not '“' in Text) and (not '”' in Text):  # Curved double quotes
            return '“' + Text + '”'
        if (not '‘' in Text) and (not '’' in Text):  # Curved single quotes
            return '‘' + Text + '’'
        if (not '«' in Text) and (not '»' in Text):  # Double guillemets
            return '«' + Text + '»'
        if (not '‹' in Text) and (not '›' in Text):  # Single guillemets
            return '‹' + Text + '›'
        import pdebug; pdebug.zbreak()

    @classmethod
    def File_Readall(cls, File_Name):
        with open(File_Name, "r", encoding="utf8") as _FH:
            return _FH.read()

    @classmethod
    def File_Dump(cls, File_Text, File_Name):
        with open(File_Name, "w") as _FH:
            _FH.write(File_Text)

    @classmethod
    def File_Append(cls, File_Text, File_Name):
        with open(File_Name, "a") as _FH:
            _FH.write(File_Text)

    @classmethod
    def File_Exists(cls, Path):
        return os.path.exists(Path)

    @classmethod
    def File_Delete(cls, File_Name):
        try:
            os.remove(File_Name)
        except FileNotFoundError:
            pass

    @classmethod
    def Files(cls, Filespec):
        return os.listdir(Filespec).copy()

    @classmethod
    def Rename(cls, From, To):
        os.rename(From, To)

    @classmethod
    def Chr(cls, Number):
        return chr(Number)

    @classmethod
    def Time_String(cls):
        return str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @classmethod
    def Readline(cls):
        return input()

    @classmethod
    def Random_Integer(cls, Values):
        return random.randrange(Values)
