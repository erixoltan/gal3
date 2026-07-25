Runtime ; erik ; gal 3 ; Copyright (c) 2024 Erik Zoltan
    if '$data(%matrix) do ^gal
    quit
    ;
%RandomInteger(%class,%max) ; $random
    set:$get(%max)<1 %max=1
    quit $random(%max)
    ;
%FileDump(%class,%text,%filename) ; File Dump
    ; write "dumping text ",%text," to file ",%filename,!
    ; zsystem "pwd";
    open %filename:newversion
    use %filename:nowrap
    write %text
    close %filename
    ; zsystem "ls -l "_%filename
    quit
    ;
%FileAppend(%class,%code,%filename) ; File Append
    use %filename:nowrap
    write %code
    quit
    ;
