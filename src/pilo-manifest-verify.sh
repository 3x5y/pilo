#!/bin/sh
set -eu

pile=$PILO_PILE_PATH
manifest="$PILO_ADMIN_PATH/manifest/pile.manifest"

[ -s "$manifest" ] || exit 0
cd "$pile"
sha256sum --quiet --strict -c $manifest
