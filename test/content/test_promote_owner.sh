#!/bin/sh
set -eu

echo data > /$PILE/out/collection/file.txt
create_pile_manifest

pilo content-promote

assert_owner $PILO_USER /"$STATIC"/collection/file.txt
