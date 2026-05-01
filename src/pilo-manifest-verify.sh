#!/bin/sh
set -eu

pile=$PILO_PILE_PATH
manifest=$pile/.manifest

cd "$pile"
[ -s "$manifest" ] || exit 0
sha256sum --quiet --strict -c $manifest
