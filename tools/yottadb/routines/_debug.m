%debug ; Erik ; 20160116 ; 20240331 ; gtm %debug
    if '$data(%debugnext) do %startup
    do Shell
    quit

Main ; Called from metapsell script.
    new %debugnext
    do %startup
    quit

%startup ; 
    set %debugnext=0
    set %debugstep=0
    set %fallback=0
    use $principal:width=0
    do Setup
    quit

Prompt(%start,%end,%from,%to) ; Debug prompt.
    new %input,%word,%x,%target,%where,%label,%offset,%routine,%start,%end
PromptAgain ; Prompt the user again.
    set %where=$stack($stack-1,"PLACE")
    do Rdisp(%where,"Debugger at "_%where)
    if $data(%watch) do ZW(%watch)
    write:$x !
    read "metaspell>",%input,!
    if %input=""!(%input="n") set %debugnext=1,%debugstep=0 quit
    if %input="s" set %debugnext=1,%debugstep=1 quit
    if %input="c" set %debugnext=0,%debugstep=0 quit
    if %input="q" halt
    if %input="stack" do Stack goto PromptAgain
    set %word=$piece(%input," ")
    if %word="show" do  goto PromptAgain
    .   for %x=2:1:$length(%input," ") do
    .   .   set %target=$piece(%input," ",%x)
    .   .   xecute "do Show("_%target_")"
    xecute %input
    goto PromptAgain

Web ; Web site entry point.
    do Startup0^privateSystem
    do Init0^privateWeb
    do Request0^privateWeb(%tWeb)
    quit

Stack ; Dump stack to output device.
    write:$x ! write !
    new s
    for s=$stack-1:-1:0 do
    .   write $justify(s,2),") "
    .   write $stack(s),": ",$stack(s,"PLACE")," - ",$stack(s,"ECODE"),!
    .   write ?5,$stack(s,"MCODE"),!
    write $stack-1," levels total",!
    quit

Show(%entity) ; Show an entity in the current matrix.
    new %arg,%prefix
    set %prefix=$$DomainCode
    set %arg="Show1^"_%domain_"Main(%"_%prefix_"Main,%entity)"
    do @%arg
    quit

ShowProp(Entity,PropName) ; Show an entity's property (by name).
    new %arg,%lookup,%prefix
    set %prefix=$$DomainCode
    set %lookup="$$Lookup1^"_%domain_"Symbol(%"_%prefix_"Symbol,PropName)"
    set %arg="ShowProp2^"_%domain_"Main(%"_%prefix_"Main,Entity,"_%lookup_")"
    do @%arg
    quit

Text(Where) ; Dump debugging text.
    new DomainCode,Invocation,Symbol
    set DomainCode=$$DomainCode
    set Symbol="JsonTokens"
    set Invocation="DumpLocation1^"_%domain_Symbol_"(%"_DomainCode_Symbol_",Where)"
    do @Invocation ; Dump debugging text.
    quit

DomainCode() ; Return the current domain code.
    if '$data(%domain) do Startup0^persistentSystem
    if %domain="private" quit "t"
    if %domain="persistent" quit "g"
    if %domain="shared" quit "s"
    if %domain="distributed" quit "d"
    quit  ; invalid domain, no such domain code.

DomainRoot() ; Return the current domain matrix root.
    if %domain="private" quit $name(P)
    if %domain="persistent" quit $name(^P)
    if %domain="shared" quit $name(^S)
    if %domain="distributed" quit $name(^D)
    quit  ; invalid domain, no such domain code.

Strip(String,From) ; Remove all instances of substring.
    new Result,Num
    set Result=""
    for Num=1:1:$length(String,From) set Result=Result_$piece(String,From,Num)
    quit Result

Replace(String,From,To) ; Search and Replace.
    quit:From="" String
    if To="" quit $$Strip(String,From)
    new Result,Num
    set Result=""
    for Num=$length(String,From):-1:1 set $piece(Result,To,Num)=$piece(String,From,Num)
    quit Result

Watch(%syms) ; Add these watches.
    new P,S,L
    for P=1:1:$length($get(%watch),",") set S=$piece($get(%watch),",",P) set:S'="" L(S)=""
    for P=1:1:$length(%syms,",") set S=$piece(%syms,",",P) set:S'="" L(S)=""
    set S="",%watch=""
    for P=1:1 set S=$order(L(S)) quit:S=""  set $piece(%watch,",",P)=S
    quit

Shell ; Run an interactive Debug shell.
    new %running set %running=1
    if '$data(%domain) set %domain="persistent",%persistent=$get(%persistent,1)
    new $etrap
    do Setup()
    ; You can run any do command here.
    break %debug
    do Teardown()
    quit

gd(%prefix) ; global directory
    set %prefix=$get(%prefix,"^")
    new %g set %g=%prefix
    if %g="^" set %g="^%"
    if $data(@%g) write %g,!
    for  set %g=$order(@%g) quit:%g=""  quit:$extract(%g,1,$length(%prefix))'=%prefix  write %g,!
    quit

Break(Entryref) ; Add a breakpoint
    zbreak @(Entryref_":%debug")
    quit

Cancel(Entryref) ; Remove a breakpoint
    zbreak @("-"_Entryref)
    quit

Trap()  ; Trap an error condition.
    use $principal:width=0
    ;write "A typical application handles unpredictable errors by logging as much information about the error as the designer considers useful, then terminating or restarting the application from a known point.",!
    write !!,"Error Trap ",$ecode,!
    write $zstatus,!
    new printline
    set printline=$piece($zstatus,",",2)
    if printline'="" zprint @printline
    else  zwrite printline
    write "Error trap at $H=",$horolog,!
    write "Stack Levels: ",$stack,!
    new %level
    for %level=1:1:$stack-1 do
    .   write %level,?3,"Place: ",$stack(%level,"PLACE")," Error code: ",$stack(%level,"ECODE"),!
    .   write ?5,$stack(%level,"MCODE"),!
    write "Error Code: ",$ecode,!
    for %level=1:1:$length($ecode,",") do
    .   new ecode
    .   set ecode=$piece($ecode,",",%level)
    .   if ecode="" quit
    .   if +ecode'=ecode quit
    .   new emesg
    .   set emesg=$zmessage(ecode)
    .   write ecode,": ",emesg,!
    write "zstatus: ",$zstatus,!
    do Setup()
    break %debug
    do:'$get(%running) Teardown()
    quit

Rdisp(%loc,header) ; print location for debugging.
    write #,$get(header),!
    new %above,%below set %above=10,%below=10
    if $get(%loc)="" quit
    new %rtn,%off,%lab,%pfx
    set %rtn=$piece(%loc,"^",2)
    set %pfx=$piece(%loc,"^")
    set %lab=$piece(%pfx,"+",1)
    set %off=$piece(%pfx,"+",2)
    if %off'="" zprint @(%lab_"+"_(%off-%above)_"^"_%rtn_":"_%lab_"+"_(%off-1))
    write *27,"[7m"
    zprint @%loc
    write *27,"[0m"
    if %off'="" zprint @(%lab_"+"_(%off+1)_"^"_%rtn_":"_%lab_"+"_(%off+%below))
    quit

ZW(%glvn) ; correct zwrite
    if '$data(%glvn) set %glvn=$zcmdline
    use $principal
    write:$x !
    set %glvn=$name(@%glvn)
    new %root set %root=%glvn
    new %ql set %ql=$qlength(%glvn)
    if "11"[$data(@%glvn) write %glvn,"=",@%glvn,!
    for  set %glvn=$query(@%glvn) quit:%glvn=""  quit:$name(@%glvn,%ql)'=%root  write %glvn,"=",@%glvn,!
    quit

OLDZW(%glvn) ; Zwrite working properly.
    set %glvn=$translate(%glvn,"$","%")
    ;use 0
    write:$x !
    new %2
    for %2=1:1:$length(%glvn,",") do
    .   new %3
    .   set %3=$piece(%glvn,",",%2)
    .   if %3="" quit
    .   if %3'?.1"^"1(1a,1"%",1"$").an write %3," <ILLEGAL ZW^%debug VARIABLE NAME: """_%3_""">",! quit
    .   if $extract(%3)="$" write %3," = """,@%3,"""",! quit
    .   if '$data(@%3) quit
    .   if $data(@%3)#2=1 write %3," = """,@%3,"""",!
    .   for  set %3=$query(@%3) quit:%3=""  write %3," = """,@%3,"""",!
    quit

SubTree(Root,Name,Indent) ; Display subtree.
    set Name="%"_$get(Name,"A")
    set Indent=$get(Indent,4)
    new %watch set %watch="Root,Name,Indent,Node"
    new @Name
    merge @Name=@Root
    new Node
    set Node=Name
    set Indent=Indent*4
    if $data(@Node)#2=1 write ?Indent,$extract(Node,2,$length(Node))," = """,@Node,"""",!
    for  set Node=$query(@Node) quit:Node=""  write ?Indent,$extract(Node,2,$length(Node))," = """,@Node,"""",!
    quit

Setup() ; Called from routine toplevel.
    set $ecode="" ; Clear error code on repeat invocations.
    set $etrap="do Trap^%debug()"
    new %d
    set %d="new %d"
    set %d=%d_" set %d=$test"
    set %d=%d_" set $zprompt=""yotta>"""
    set %d=%d_" do Rdisp^%debug($zpos,""break at ""_$zpos)"
    set %d=%d_" do:$data(%watch) ZW^%debug(%watch)"
    set %d=%d_" write:$zstatus'="""" !,$zstatus,!"
    set %d=%d_" zprint:$piece($zstatus,"","",2)'="""" @$piece($zstatus,"","",2)"
    set %d=%d_" write !"
    set %d=%d_" if %d"
    set %debug=%d
    new %z
    set %z="new %d"
    set %z=%z_" set %d=$test"
    set %z=%z_" write:$x !"
    set %z=%z_" write !"
    set %z=%z_" xecute:$data(%debug) $get(%debug)"
    set %z=%z_" xecute ""if $get(%d)"" break"
    set $zstep=%z
    set $zprompt="yotta>"
    quit

Teardown() ; Tear down the debugger.
    set $zprompt="yotta>"
    quit

TermInit() ; Initialize Terminal.
    use $principal:nowrap
    quit

Init() ; Init from command line.
    new x,y
    do Setup()
    do Teardown()
    quit

    ; Experimental multi process logic
MainLoop ; main process loop.
    lock +^Main:0
    else  write "Already Running!",! quit
    write "Starting Up Main Loop"
    kill ^Terminate
    new MaxWait,Job,Exit,Timeout,Count
    set Timeout=1/3 ; Minimum useful GTM timeout, in seconds.
    set MaxWait=Timeout/2*1000000 ; Half the timeout, in microseconds.
    set MaxJobs=10
    for Job=1:1:MaxJobs do
    .   write "."
    .   job JobLoop
    write !
    hang Timeout
    write "Entering Monitoring Loop",!
    set Exit=0
    for  do  quit:Exit
    .   lock +^Job:0
    .   if  do  quit
    .   .   write "No Job Locks remaining",!
    .   .   set ^Terminate=$job
    .   .   set Exit=1
    .   .   lock -^Job
    .   if '$data(^Job) do  quit
    .   .   write "No Job Nodes remaining",!
    .   .   set ^Terminate=$job
    .   .   set Exit=1
    .   set Job=""
    .   for Count=0:1 set Job=$order(^Job(Job)) quit:Job=""  do
    .   .   set Interval=$zut-^Job(Job)
    .   .   quit:Interval'>MaxWait
    .   .   write "Terminating Rogue Process ",Job,!
    .   .   zsystem "kill -9 "_Job
    .   .   kill ^Job(Job)
    .   .   if $data(^Terminate) write "Not restarting",! quit
    .   .   write "Starting Replacement Job",!
    .   .   job JobLoop
    .   write Count," jobs running",!
    .   for Job=Count+1:1:MaxJobs do
    .   .   write "Starting a job",!
    .   .   job JobLoop
    .   if 'Count set Exit=1 quit
    .   if $data(^Terminate) set Exit=1 quit
    .   hang Timeout
    ; Shutting down...
    write "Shutting Down",!
    set ^Terminate=$job ; Signal termination condition.
    lock +^Job:Timeout
    set Job=""
    for  set Job=$order(^Job(Job)) quit:Job=""  do
    .   write "Signaling ",Job,!
    .   kill ^Job(Job)
    hang Timeout
    for  set Job=$order(^Job(Job)) quit:Job=""  do
    .   write "Terminating ",Job,!
    .   zsystem "kill -9 "_Job
    lock -^Job
    lock -^Main
    kill ^Job
    kill ^Terminate
    write "Shutdown Complete",!
    quit

JobLoop ; Job iterative processing logic.
    new Exit
    set Exit=0
    lock +^Job($job):0
    else  quit
    set $etrap="quit:$estack  set $ecode="""""
    for  do  quit:Exit
    .   new $estack
    .   if $data(^Terminate) set Exit=1 quit
    .   set ^Job($job)=$zut
    .   do Cycle
    .   if '$data(^Job($job)) set Exit=1 quit
    kill ^Job($job)
    lock -^Job($job)
    quit

Cycle ; Local Array Scalability Test.
    new Cycle,Iter,Size,Then,Span,Average
    write !,"Cy Array Size Avg $zut",!
    write "-- ---------- ------",!
    for Cycle=1:1:24 do
    .   new Array
    .   set Size=2**Cycle
    .   set Then=$zut
    .   for Iter=1:1:Size set Array(Iter)=Iter
    .   set Span=$zut-Then
    .   set Average=Span/Size
    .   write $justify(Cycle,2)," ",$justify($fnumber(Size,","),10)," ",$justify(Average,6,3),!
    quit

Indirect ; Indirect Reference Performance.
    new %watch set %watch="Iter,Pointer,Index,Now,Then,Before,After,Nothing,Max,Direct,Indirect,Ratio"
    use $principal
    new Iter,Array,Pointer,Index,Now,Then,Before,After,Nothing,Max
    write "Pw Iterations    Direct $zut  Indir. $zut    Ratio",!
    write "-- ------------ ------------ ------------ --------",!
    for Power=1:1:9 do
    .   set Max=10**Power
    .   for Index=1:17:Max set Array(Index)=$random(1234567)
    .   set Nothing=0
    .   set Before=$zut
    .   for Index=1:1:Max set Nothing=Nothing+$get(Array(Index),0)
    .   set After=$zut
    .   set Nothing=0
    .   set Pointer="Array(Index)"
    .   set Then=$zut
    .   for Index=1:1:Max set Nothing=Nothing+$get(@Pointer)
    .   set Now=$zut
    .   set Direct=After-Before
    .   set Indirect=Now-Then
    .   set Ratio=Indirect/Direct
    .   write $justify(Power,2)," "
    .   write $justify($fnumber(Max,","),12)," "
    .   write $justify($fnumber(Direct,","),12)," "
    .   write $justify($fnumber(Indirect,","),12)," "
    .   write $justify($fnumber(Ratio,",",4),8)," "
    .   write !
    quit

JobTest ; Test some job parameters.
    kill ^ZZJ
    new JN
    write "Starting Jobs..."
    for JN=1:1:10 job NewJob write JN," "
    hang 1
    write !,"Locking. "
    lock +^ZZJ
    lock -^ZZJ
    write "Success.",!
    quit

NewJob ; Test some job stuff.
    lock +^ZZJ($job)
    set ^ZZJ($job)=1
    hang 5
    lock -^ZZJ($job)
    quit

Float(Number) ; Return a float from C.
    new Float
    set %watch="Number,Float"
    ;set Float=$&.NslFloat(Number)
    quit Float

FloatTest ; Test C float function.
    new N1,F1
    set N1=10/3
    write "N1: ",N1,!
    set F1=$$Float(N1)
    write "F1: ",F1,!
    quit

Handleprivate3(SymbolId,Entity,%machine) ; Handle private dispatch.
    goto handlegoto

Handleprivate2(SymbolId,Entity) ; Handle private dispatch.
handlegoto ; Goto label.
    new %watch,Method,Method2,Routine,Eref,Eref2,Class,Class2,Fallback
    set %watch="%machine,%ecode,SymbolId,Entity,SymbolId,Method,Routine,Eref,Class,Fallback,Method2,Class2,Eref2"
    set Class=$$Get1^privateCanonical(%tCanonical,Entity)
    break:Class="" %debug
    quit:Class=""
    set Method=$$Get1^privateCanonicalMethod(%tCanonicalMethod,Class)
    ;break:Method="StmtGroup" %debug
    quit:Method=""
    set Routine=$$Get1^privateSymbolRoutine(%tSymbolRoutine,SymbolId)
    break:Routine="" %debug
    quit:Routine=""
    set Eref=Method_"1^"_Routine_"(SymbolId,Entity)"
    if Routine["Process" do @Eref quit
    if '%fallback do @Eref quit
    if $$Atomic1^privateMspPrototype(%tMspPrototype,Entity) do @Eref quit
    quit:$$HandleTry(Eref)
    ;break %debug
    set Fallback=$$Get1^privateMspFallback(%tMspFallback,Entity)
    if 'Fallback write "ERROR: ",Eref," returned error code ",%ecode,! quit
    set Class2=$$Get1^privateCanonical(%tCanonical,Fallback)
    break:Class2="" %debug
    quit:Class2=""
    set Method2=$$Get1^privateCanonicalMethod(%tCanonicalMethod,Class2)
    break:Method2="" %debug
    quit:Method2=""
    set Eref2=Method2_"1^"_Routine_"(SymbolId,Fallback)"
    ;break %debug
    quit:$$HandleTry2(Eref2)
    ;write "Fallback Trapped: ",Eref,!?5,Eref2,!
    ;break %debug
    quit
HandleTry(Eref) ; Try Scope.
    new $etrap,$estack
    set $etrap="quit:$estack  goto HandleCatch"
    do @Eref
    quit 1
HandleCatch ; Catch an error.
    set %ecode=$zstatus,$ecode="",$zstatus="" do Watch^%debug("%ecode")
    ;write "Falling back. ",%ecode,!
    quit 0
HandleTry2(Eref2) ; Try Scope.
    ;new $etrap,$estack
    ;set $etrap="quit:$estack  goto HandleCatch2"
    do @Eref2
    quit 1
HandleCatch2 ; Catch an error.
    set %ecode=$zstatus,$ecode="",$zstatus="" do Watch^%debug("%ecode")
    write "Error in fallback ",Fallback," call ",Eref2,!?5,%ecode,!
    quit 0

fwrite(file,str1,str2,str3,str4,str5,str6,str7,str8,str9,str10) ; fwrite statement
    new %io set %io=$io
    new $etrap,$estack
    set $etrap="quit:$estack  goto fwriteCatch"
    use file
    write str1_$get(str2)_$get(str3)_$get(str4)_$get(str5)_$get(str6)_$get(str7)_$get(str8)_$get(str9)_$get(str10)
fwriteCatch ; Error handler.
    use %io
    quit

fread(file,inputvar) ; Read some input.
    new %io set %io=$io
    new $etrap,$estack
    set $etrap="quit:$estack  goto freadCatch"
    use file
    read inputvar:%timeout
    use %io
    ;else  set $ecode="U:fread.timeout"
    quit
freadCatch ; Error handler.
    set %ecode=$zstatus,$ecode="",$zstatus=""
    use %io
    ;do Watch^%debug("%ecode")
    quit


