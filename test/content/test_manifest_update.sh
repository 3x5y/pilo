#!/bin/sh
set -e

echo data > /$PILE/in/file1.txt
echo another > /$PILE/in/file2.txt
create_pile_manifest

assert_manifest_valid pile /$PILE
