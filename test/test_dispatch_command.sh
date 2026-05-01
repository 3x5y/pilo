#!/bin/sh
set -eu

capture_status pilo status pile

assert_command_ok
