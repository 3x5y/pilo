#!/bin/sh
set -e

FILE=test_admission.txt

echo hello world > /tmp/$FILE

system-capture /tmp/$FILE

assert_file_exists /tank/data/active/pile/$FILE
