#!/bin/sh
set -e

if (echo data > /$PILE/xxx.txt) 2>/dev/null
then
    fail write succeeded on readonly dataset
fi
