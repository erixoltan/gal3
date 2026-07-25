galrt ; gal3 minimal mumps runtime: object matrix + arity dispatch
    quit
init ; object arena setup; local by default, so objects are transient.
    ; export galmatrix=^X (or any glvn) for persistent objects: kill ^X,
    ; run a program, then examine every object it created retrospectively.
    new %g set %g=$ztrnlnm("galmatrix")
    set:'$data(%matrix) %matrix=$select(%g'="":%g,1:"%mx")
    quit
dispatch0(%o,%m) ; method call, 0 arguments
    new %c set %c=@%o
    new %l set %l=%m_"^"_%c_"(%o)"
    quit:$quit @("$$"_%l)
    do @%l
    quit
dispatch1(%o,%m,%a1) ; method call, 1 argument
    new %c set %c=@%o
    new %l set %l=%m_"^"_%c_"(%o,.%a1)"
    quit:$quit @("$$"_%l)
    do @%l
    quit
dispatch2(%o,%m,%a1,%a2) ; method call, 2 arguments
    new %c set %c=@%o
    new %l set %l=%m_"^"_%c_"(%o,.%a1,.%a2)"
    quit:$quit @("$$"_%l)
    do @%l
    quit
dispatch3(%o,%m,%a1,%a2,%a3) ; method call, 3 arguments
    new %c set %c=@%o
    new %l set %l=%m_"^"_%c_"(%o,.%a1,.%a2,.%a3)"
    quit:$quit @("$$"_%l)
    do @%l
    quit
dispatch4(%o,%m,%a1,%a2,%a3,%a4) ; method call, 4 arguments
    new %c set %c=@%o
    new %l set %l=%m_"^"_%c_"(%o,.%a1,.%a2,.%a3,.%a4)"
    quit:$quit @("$$"_%l)
    do @%l
    quit
repeat(%s,%n) ; the string repeated %n times
    new %r,%i set %r=""
    for %i=1:1:%n set %r=%r_%s
    quit %r
replace(%s,%f,%t) ; every %f in %s becomes %t
    new %r,%p set %r="",%p=1
    for  quit:%p>$length(%s)  do
    .   if $extract(%s,%p,%p+$length(%f)-1)=%f set %r=%r_%t,%p=%p+$length(%f) quit
    .   set %r=%r_$extract(%s,%p),%p=%p+1
    quit %r
llen(%l) ; entries in a list or dict handle: O(1) via the count node
    ; list layout: numeric subscripts hold items, the root holds the
    ; append high-water, and metadata rides at string subscripts ("n"
    ; count, "h" holes-after-shift flag). strings collate after every
    ; number, so ordered walks just stop at the first non-numeric.
    quit +$get(@%l@("n"))
lpush(%l,%v) ; append, keeping the count truthful
    set @%l@($increment(@%l))=%v
    if $increment(@%l@("n"))
    quit
shift(%l) ; remove and return the first entry
    new %i,%v set %i=$order(@%l@(""))
    quit:%i'=+%i ""
    set %v=@%l@(%i) kill @%l@(%i)
    set @%l@("n")=$get(@%l@("n"))-1,@%l@("h")=1
    quit %v
lastsub(%l) ; highest numeric subscript, skipping metadata
    new %i set %i=$order(@%l@(""),-1)
    for  quit:%i=""!(%i=+%i)  set %i=$order(@%l@(%i),-1)
    quit %i
poplast(%l) ; remove and return the last entry
    new %i,%v set %i=$$lastsub(%l)
    quit:%i="" ""
    set %v=@%l@(%i) kill @%l@(%i)
    set @%l@("n")=$get(@%l@("n"))-1
    quit %v
last(%l) ; the last entry
    new %i set %i=$$lastsub(%l)
    quit:%i="" ""
    quit @%l@(%i)
lget(%l,%o) ; zero-based offset fetch: direct while dense, walk past holes
    quit:'$data(@%l@("h"))&($data(@%l@(%o+1))#2) @%l@(%o+1)
    new %i,%n set %i="",%n=-1
    for  set %i=$order(@%l@(%i)) quit:%i'=+%i  set %n=%n+1 quit:%n=%o
    quit:%i'=+%i ""
    quit @%l@(%i)
dset(%d,%k,%v) ; dictionary store, insertion order preserved
    ; layout: @d@("k",key)=value, @d@("o",seq)=key, @d@("x",key)=seq,
    ; @d = insertion counter, @d@("n") = live count. python's dict
    ; contract: iteration follows first insertion, resetting a key
    ; keeps its original position.
    if '$data(@%d@("x",%k)) do
    .   set @%d@("x",%k)=$increment(@%d),@%d@("o",@%d@("x",%k))=%k
    .   if $increment(@%d@("n"))
    set @%d@("k",%k)=%v
    quit
dget(%d,%k) ; dictionary fetch, empty for a missing key
    quit $get(@%d@("k",%k))
dhas(%d,%k) ; does the dictionary hold the key
    quit ''$data(@%d@("k",%k))
dkill(%d,%k) ; remove a key, its value and its order slot
    quit:'$data(@%d@("x",%k))
    kill @%d@("o",@%d@("x",%k)),@%d@("k",%k)
    kill @%d@("x",%k)
    set @%d@("n")=$get(@%d@("n"))-1
    quit
iternext(%l,%c) ; shared for-each cursor: next position, "" at the end
    quit:$data(@%l@("k")) $order(@%l@("o",%c))
    new %i set %i=$order(@%l@(%c))
    quit:%i'=+%i ""
    quit %i
iterval(%l,%c) ; the item at a cursor: dict keys, list values
    quit:$data(@%l@("k")) @%l@("o",%c)
    quit @%l@(%c)
truthy(%v) ; python truthiness, which mumps numeric truth does not match
    ; "" and 0 are false; every other number is true; a collection handle
    ; is true only when it holds something; an object handle and any
    ; other non-empty string are true (mumps would read them as zero).
    quit:%v="" 0
    quit:%v=+%v +%v'=0
    quit:$extract(%v,1,$length(%matrix)+1)'=(%matrix_"(") 1
    quit:@%v'=+@%v 1
    quit $$llen(%v)>0
isa(%o,%c) ; runtime is-a through the ancestors table
    ; a value that is not an object handle is an instance of nothing -
    ; python answers False, so indirecting it (which would raise UNDEF,
    ; or worse, read an unrelated local of that name) must not happen
    quit:%o="" 0
    quit:$extract(%o,1,$length(%matrix)+1)'=(%matrix_"(") 0
    quit:'$data(@%o) 0
    new %k set %k=@%o
    quit ''$data(@%matrix@("%c",%k,%c))
isident(%ch) ; letter, digit or underscore
    quit %ch?1(1A,1N,1"_")
isupper(%s) ; all cased characters upper, at least one
    quit %s'=""&(%s=$zconvert(%s,"U"))&(%s'=$zconvert(%s,"L"))
islower(%s) ; all cased characters lower, at least one
    quit %s'=""&(%s=$zconvert(%s,"L"))&(%s'=$zconvert(%s,"U"))
ispunct(%ch) ; ascii 33..126 minus letters and digits
    new %a set %a=$ascii(%ch)
    quit %a>32&(%a<127)&('(%ch?1(1A,1N)))
join(%l,%d) ; list entries joined by %d
    new %i,%r,%b set %i="",%r="",%b=""
    for  set %i=$order(@%l@(%i)) quit:%i'=+%i  set %r=%r_%b_@%l@(%i),%b=%d
    quit %r
split(%l,%s,%d) ; append the pieces of %s split on %d to list %l
    new %i,%n set %n=$length(%s,%d)
    for %i=1:1:%n do lpush(%l,$piece(%s,%d,%i))
    quit
fileread(%f) ; the whole file as one string with $char(10) line breaks
    new %r,%line,%eof set %r="",%eof=0
    open %f:(readonly:exception="set %eof=1")
    use %f
    for  quit:%eof  read %line quit:%eof  set %r=%r_%line_$char(10)
    close %f
    use $principal
    quit %r
writeto(%f,%t) ; write the string to the file, one record per line
    ; writing the whole string in one WRITE hits the device width at
    ; 32767 (wrapping, or truncating under NOWRAP), so the embedded
    ; newlines become real record terminators - which also reset $x
    new %i,%n
    open %f:(newversion)
    use %f
    set %n=$length(%t,$char(10))
    for %i=1:1:%n  write $piece(%t,$char(10),%i) write:%i<%n !
    set $x=0 ; a nonzero $x at close would append one more newline
    close %f
    use $principal
    quit
fexists(%f) ; does the file exist
    quit $zsearch(%f)'=""
splitnew(%s,%d) ; split into a fresh matrix node, return its handle
    new %l set %l=$name(@%matrix@($increment(@%matrix)))
    set @%l=0
    do split(%l,%s,%d)
    quit %l
create0(%c) ; new instance of a computed class
    new %l set %l="new^"_%c_"()"
    quit @("$$"_%l)
create1(%c,%a1) ; new with one argument
    new %l set %l="new^"_%c_"(.%a1)"
    quit @("$$"_%l)
create2(%c,%a1,%a2) ; new with two arguments
    new %l set %l="new^"_%c_"(.%a1,.%a2)"
    quit @("$$"_%l)
create3(%c,%a1,%a2,%a3) ; new with three arguments
    new %l set %l="new^"_%c_"(.%a1,.%a2,.%a3)"
    quit @("$$"_%l)
len(%x) ; python len for an unknown-typed value: handle walk or $length
    new $etrap,$estack set $etrap="quit:$estack  goto lenstr^galrt"
    quit:'$data(@%x) 0
    quit $$llen(%x)
lenstr ; not a handle: measure the string
    set $ecode="",$zstatus=""
    quit $length(%x)
