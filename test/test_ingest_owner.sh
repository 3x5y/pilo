#!/bin/sh
set -eu

dir=stuff
file="$dir/file.txt"

# simulate user capture

sudo -u $PILO_USER mkdir $PILO_INTAKE_PATH/stuff
sudo -u $PILO_USER sh -c "echo data > '$PILO_INTAKE_PATH/stuff/file.txt'"

pilo ingest-pile

dir=$PILO_PILE_PATH/in/stuff
file=$dir/file.txt

assert_file_exists "$file"

assert_owner $PILO_USER $file
assert_owner $PILO_USER $dir
