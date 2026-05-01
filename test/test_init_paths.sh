#!/bin/sh
set -e

unset PILO_ADMIN_PATH
unset PILO_INTAKE_PATH
unset PILO_PILE_PATH
unset PILO_STATIC_PATH

pilo init

[ -d "$PILO_PATH/active/admin" ] || fail "default admin path missing"
[ -d "$PILO_PATH/active/pile-intake" ] || fail "default intake path missing"
