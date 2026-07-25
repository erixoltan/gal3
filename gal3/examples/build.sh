#!/bin/bash

BUILD="$HOME/Desktop/examples/$1"
rm -f $BUILD/* &> /dev/null
mkdir -p "$BUILD"
mkdir -p bin

function compile
{
    rm -f "$3" &> /dev/null
    python3 $HOME/.gal3/$1.py "$2" "$3"
    if [ ! -f "$3" ]; then
        echo "$1 could not create $3. Aborting!"
        exit 1
    fi
}

function gal
{
    compile gal "$1" "$2"
}

function fallback
{
    compile fallback "$1" "$2"
}

function galpy
{
    compile galpy "$1" "$2"
}

gal "$1.txt" "$BUILD/$1.gal"
fallback "$BUILD/$1.gal" "$BUILD/$1.fb0"
fallback "$BUILD/$1.fb0" "$BUILD/$1.fb1"
fallback "$BUILD/$1.fb1" "$BUILD/$1.fb2"
galpy "$BUILD/$1.fb2" "$BUILD/$1.py"
mv $BUILD/$1.py bin/

