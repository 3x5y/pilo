#!/bin/sh

export PATH=$(dirname $0)/system:$PATH

echo PATH=$PATH
sh setup_env.sh && sh test.sh

RESULT=$?

sh teardown_env.sh

exit $RESULT
