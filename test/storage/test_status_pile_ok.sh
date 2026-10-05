#!/bin/sh
set -e

echo data > /$PILE/in/file.txt

capture_status pilo status pile

assert_command_ok expected no pile age warning
