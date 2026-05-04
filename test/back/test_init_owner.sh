#!/bin/sh
set -eu

assert_owner $PILO_USER $PILO_ADMIN_PATH
assert_owner $PILO_USER $PILO_INTAKE_PATH
assert_owner $PILO_USER $PILO_PILE_PATH/in
assert_owner $PILO_USER $PILO_PILE_PATH/out
assert_owner $PILO_USER $PILO_PILE_PATH/sort
assert_owner $PILO_USER $PILO_STATIC_PATH/collection
