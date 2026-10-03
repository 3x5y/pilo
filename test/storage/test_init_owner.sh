#!/bin/sh
set -eu

assert_owner $PILO_USER $PILO_PATH/admin
assert_owner $PILO_USER $PILO_PATH/intake
assert_owner $PILO_USER $PILO_PATH/pile/in
assert_owner $PILO_USER $PILO_PATH/pile/sort
assert_owner $PILO_USER $PILO_PATH/pile/out/collection
assert_owner $PILO_USER $PILO_PATH/static/collection
