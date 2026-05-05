#!/bin/sh
set -e

pilo init
pilo init

assert_command_ok "init should be idempotent"
