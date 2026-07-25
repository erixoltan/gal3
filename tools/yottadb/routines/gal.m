gal ; gal runtime library
    use $principal:nowrap
    set %matrix="^X"
    do Setup^%debug
    do init()
    quit

class(%classname) ; return class id
    quit %classname

init(%dir) ; initialize all classes in %dir.
    set %dir=$get(%dir,"/tmp/ramdisk/m/")
    new %ZR,%rtn,%d,%count,%verbose
    set %verbose=0
    set %count=0
    do SILENT^%RSEL("*")
    set %rtn=""
    for  set %rtn=$order(%ZR(%rtn)) quit:%rtn=""  do
    .   set %d=%ZR(%rtn)
    .   quit:%d'=%dir
    .   write:%verbose "init ",%rtn,!
    .   set ^Classes(%rtn)=%rtn
    .   do @("%init^"_%rtn_"(%rtn)")
    .   set %count=%count+1
    write:%verbose "initialized ",%count," classes",!
    quit

wipe(%dir) ; wipe ^X and all globals of classes in %dir.
    kill ^Classes
    set %dir=$get(%dir,"/tmp/ramdisk/m/")
    new %ZR,%rtn,%d,%glo,%count,%verbose
    set %verbose=0
    set %count=0
    do SILENT^%RSEL("*")
    set %rtn=""
    for  set %rtn=$order(%ZR(%rtn)) quit:%rtn=""  do
    .   set %d=%ZR(%rtn)
    .   quit:%d'=%dir
    .   set %glo="^%"_%rtn
    .   kill @%glo
    .   write:%verbose "kill ",%glo,!
    .   set %count=%count+1
    kill ^X,^BIE,^BIO,^Op,^O,^F,^C
    write:%verbose "kill ^X,^BIE,^BIO,^Op,^O,^F,^C",!
    write:%verbose "wiped ",%count," classes",!
    quit


new(%classname) ; new instance of class.
    new %c set %c=$$class(%classname)
    new %o set %o=$increment(^o)
    set ^o(%o)=%c
    quit $name(^o(%c))

dispatch0(%oid,%method) ; method 0 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch1(%oid,%method,%a1) ; method 1 argument
    ;set %remembery=$get(%remembery)_" | "_%oid
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch2(%oid,%method,%a1,%a2) ; method 2 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch3(%oid,%method,%a1,%a2,%a3) ; method 3 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2,%a3)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch4(%oid,%method,%a1,%a2,%a3,%a4) ; method 4 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2,%a3,%a4)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch5(%oid,%method,%a1,%a2,%a3,%a4,%a5) ; method 5 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2,%a3,%a4,%a5)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch6(%oid,%method,%a1,%a2,%a3,%a4,%a5,%a6) ; method 6 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2,%a3,%a4,%a5,%a6)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch7(%oid,%method,%a1,%a2,%a3,%a4,%a5,%a6,%a7) ; method 7 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2,%a3,%a4,%a5,%a6,%a7)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch8(%oid,%method,%a1,%a2,%a3,%a4,%a5,%a6,%a7,%a8) ; method 8 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2,%a3,%a4,%a5,%a6,%a7,%a8)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

dispatch9(%oid,%method,%a1,%a2,%a3,%a4,%a5,%a6,%a7,%a8,%a9) ; method 9 arguments
    new %c set %c=@%oid
    new %l set %l=%method_"^"_%c_"(%oid,%a1,%a2,%a3,%a4,%a5,%a6,%a7,%a8,%a9)"
    quit:$quit @("$$"_%l)
    do @%l
    quit

listlast(%list) ; return last element.
    new %sub set %sub=$order(@%list@(""),-1)
    quit:%sub="" ""
    quit @%list@(%sub)

upper(%text) ; return uppercase
    quit $translate(%text,"abcdefghijklmnopqrstuvwxyz","ABCDEFGJIJKLMNOPQRSTUVWXYZ")

lower(%text) ; return lowercase
    quit $translate(%text,"ABCDEFGJIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")

isuppercase(%text) ; return t/f
    quit:%text="" 0
    quit $translate(%text,"ABCDEFGHIJKLMNOPQRSTUVWXYZ")=""

islowercase(%text) ; return t/f
    quit:%text="" 0
    quit $translate(%text,"abcdefghijklmnopqrstuvwxyz")=""

titlecase(%text) ; convert to title case
    new %result set %result=""
    new %c,%p
    new %mode set %mode=1
    for %p=1:1:$length(%text) do
    .   set %c=$extract(%text,%p)
    .   set:%mode %c=$$upper(%c),%mode=0
    .   set %result=%result_%c
    .   set:%c?1p %mode=1
    quit %result

isnumber(%text) ; return t/f
    quit +%text=%text

ispunct(%text) ; return t/f
    quit %text?1.p

isstring(%text) ; return t/f
    quit 1

isws(%text) ; return t/f
    quit:%text="" 0
    quit $translate(%text,$char(32,9,10,13))=""

split(%string,%delim) ; return list reference.
    new %o set %o=$increment(%l)
    new %list set %list=$name(%l(%o))
    new %len set %len=$length(%string,%delim)
    new %i
    for %i=1:1:%len set @%list@(%i)=$piece(%string,%delim,%i)
    quit %list

substring2(%string,%start) ; return string
    quit $extract(%string,%start+1,$length(%string))

substring3(%string,%start,%length) ; return string
    quit $extract(%string,%start+1,%start+%length)

pop(%list) ; remove and return
    new %sub set %sub=$order(@%list@(""),-1)
    if %sub="" quit:$quit "" quit
    new %value set %value=@%list@(%sub)
    kill @%list@(%sub)
    set @%list=@%list-1
    quit:$quit %value quit

shift(%list) ; remove and return
    new %sub set %sub=$order(@%list@(""))
    if %sub="" quit:$quit "" quit
    new %value set %value=@%list@(%sub)
    kill @%list@(%sub)
    set @%list=@%list-1
    quit:$quit %value quit

    ; dispatch table for evolver.
CompileSynthesis do ^gal,^Evolver("CompileSynthesis") quit
Startup do ^gal,^Evolver("Startup") quit
Synthesize do ^gal,^Evolver("Synthesize") quit
CompileImplementers do ^gal,^Evolver("CompileImplementers") quit
Analyze do ^gal,^Evolver("Analyze") quit
CompileOutcomes do ^gal,^Evolver("CompileOutcomes") quit
Hindsight do ^gal,^Evolver("Hindsight") quit

Begin ; Start cycle
    do wipe
    do gal
    do CompileSynthesis
    ; Exiting here to avoid zlink error
    quit

Continue ; Continue processing the cycle
    do Startup
    do Synthesize
    do CompileImplementers
    quit

fileopenread(%file) ; returns 1/0
    new $etrap,$estack
    set $etrap="quit:$estack  goto fopenCatch"
    open %file:readonly
    quit 1
fopenCatch ; Error handler.
    set %ecode=$zstatus,$ecode="",$zstatus=""
    quit 0

fileexists(%file) ; returns 1/0
    new $etrap,$estack
    set $etrap="quit:$estack  goto fexistsCatch"
    open %file:readonly
    close %file
    quit 1
fexistsCatch ; Error handler.
    set %ecode=$zstatus,$ecode="",$zstatus=""
    quit 0

filereadall(%file) ; returns file text
    quit:'$$fileopenread(%file) ""
    new %inputvar
    new %filetext set %filetext=""
    new %io set %io=$io
    new $etrap,$estack
    set $etrap="quit:$estack  goto freadCatch"
    use %file
freadNext ; loop continue
    read %inputvar
    set %filetext=%filetext_%inputvar_$char(10)
    goto freadNext
freadCatch ; Error handler.
    set %ecode=$zstatus,$ecode="",$zstatus=""
    close %file
    quit %filetext

filereadline(%file) ; returns line text
    new %inputvar
    new %filetext set %filetext=""
    use %file
    read %inputvar
    set %filetext=%inputvar_$char(10)
    quit %filetext

filereadlist(%file,%list) ; returns file text
    kill @%list
    set @%list=0
    quit:'$$fileopenread(%file) ""
    new %filetext set %filetext=""
    new %io set %io=$io
    new $etrap,$estack
    set $etrap="quit:$estack  goto fcatchList"
freadList ; loop continue
    use %file read %inputvar use %io
    set %inputvar=%inputvar_$char(10)
    set %filetext=%filetext_%inputvar
    set @%list@($increment(@%list))=%inputvar
    goto freadList
fcatchList ; Error handler.
    set %ecode=$zstatus,$ecode="",$zstatus=""
    close %file
    quit %filetext

guid() ; guaranteed unique identifier.
    set ^guid=$increment(^guid)
    quit "gal"_^guid

X   ; dump ^X global
    do ZW^%debug($name(^X))
    quit

repeat(%string,%count) ; copies of string.
    new %result
    set $piece(%result,%string,%count+1)=""
    quit %result
