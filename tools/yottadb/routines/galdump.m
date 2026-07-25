galdump ; retrospective census of the object matrix
    new %i,%c,%k,%n
    set %n=+$get(^X)
    write "objects allocated: ",%n,!
    set %i=""
    for  set %i=$order(^X(%i)) quit:%i=""  do
    .   set %c=$get(^X(%i))
    .   quit:%c=""
    .   quit:%c=+%c
    .   set %k(%c)=$get(%k(%c))+1
    set %c=""
    for  set %c=$order(%k(%c)) quit:%c=""  write %c,": ",%k(%c),!
    quit
parser ; the parser object's state
    new %i,%c,%p
    set %i=""
    for  set %i=$order(^X(%i)) quit:%i=""  if $get(^X(%i))="GalParser" do  quit
    .   write "parser is object ",%i,!
    .   set %p=""
    .   for  set %p=$order(^X(%i,%p)) quit:%p=""  do
    .   .   if $data(^X(%i,%p))#2 write "  ",%p,"=",$extract(^X(%i,%p),1,60),!
    .   .   else  write "  ",%p," (subtree)",!
    quit
wipe ; clear the retrospective database
    kill ^X
    quit
node ; dump the subtree of ^X(n) for the n in $zcmdline
    new %i,%n
    set %n=$zcmdline
    write "^X(",%n,")=",$get(^X(%n)),!
    set %i=""
    for  set %i=$order(^X(%n,%i)) quit:%i=""  do
    .   if $data(^X(%n,%i))#2 write "  (",%i,")=",$extract(^X(%n,%i),1,70),!
    .   else  write "  (",%i,") subtree",!
    quit
find ; dump all objects of the class named in $zcmdline
    new %i,%c,%p,%t
    set %t=$zcmdline
    set %i=""
    for  set %i=$order(^X(%i)) quit:%i=""  do
    .   quit:$get(^X(%i))'=%t
    .   write "object ",%i," (",%t,")",!
    .   set %p=""
    .   for  set %p=$order(^X(%i,%p)) quit:%p=""  do
    .   .   if $data(^X(%i,%p))#2 write "  ",%p,"=",$extract(^X(%i,%p),1,50),!
    .   .   else  write "  ",%p," (subtree ",$$llen^galrt("^X("_%i_","""_%p_""")")," entries)",!
    quit
