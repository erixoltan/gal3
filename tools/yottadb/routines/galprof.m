galprof ; line-level profile of a gal compiler run hosted in mumps.
    ; usage: mumps -run galprof <in> <out>, then mumps -run report^galprof
    ; (or read ^trc directly). VIEW TRACE records calls and cpu per line.
    kill ^trc
    view "TRACE":1:"^trc"
    do CompilerProgram^CompilerProgram
    view "TRACE":0:"^trc"
    quit
report ; the hottest lines, most cpu first
    new r,l,o,d,n,c,u,out
    set r=""
    for  set r=$order(^trc(r)) quit:r=""  do
    .   set l=""
    .   for  set l=$order(^trc(r,l)) quit:l=""  do
    .   .   set o=""
    .   .   for  set o=$order(^trc(r,l,o)) quit:o=""  do
    .   .   .   set d=^trc(r,l,o),c=$piece(d,":",1),u=$piece(d,":",2)
    .   .   .   quit:u'>0
    .   .   .   set out(-u,r_" "_l_"+"_o)=c_" calls, "_u_" usec"
    set n=0,u=""
    for  set u=$order(out(u)) quit:u=""!(n>25)  do
    .   set l=""
    .   for  set l=$order(out(u,l)) quit:l=""  set n=n+1 write l,": ",out(u,l),!
    quit
