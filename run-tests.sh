#!/bin/sh

export PATH=$(realpath ${0%/*})/system:$PATH

sh env_setup.sh && sh test.sh

RESULT=$?

sh env_teardown.sh

exit $RESULT
