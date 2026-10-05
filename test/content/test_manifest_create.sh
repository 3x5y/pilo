#!/bin/sh
set -e

file=test.txt
echo hello > /$PILE/in/$file
create_pile_manifest

assert_manifest_valid pile /$PILE
