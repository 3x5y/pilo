#!/bin/sh
set -eu

verify_manifest() {
    subset=$1
    dir=$2
    manifest="$PILO_ADMIN_PATH/manifest/$subset.manifest"
    [ -s "$manifest" ] || return 0
    (cd "$dir" && sha256sum --quiet --strict -c $manifest)
}

verify_manifest pile "$PILO_PILE_PATH"
verify_manifest collection "$PILO_STATIC_PATH"/collection
verify_manifest filing "$PILO_STATIC_PATH"/filing
