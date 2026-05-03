#!/bin/sh
set -eu

pilo manifest-update

assert_file_exists "$PILO_ADMIN_PATH/manifest/pile.manifest"
assert_owner $PILO_USER "$PILO_ADMIN_PATH/manifest/pile.manifest"
