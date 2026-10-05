#!/bin/sh
set -eu

runuser mkdir /$PILE/out/collection/dirx
echo data > /$PILE/out/collection/dirx/file.txt
create_pile_manifest

pilo content-promote

assert_owner $PILO_USER /"$STATIC"/collection/dirx
