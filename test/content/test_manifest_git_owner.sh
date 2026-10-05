#!/bin/sh
set -eu

echo data > /$PILE/in/file.txt
create_pile_manifest

assert_owner $PILO_USER /"$ADMIN"/manifest/.git
