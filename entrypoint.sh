#!/bin/bash -l

PYTHON=$(which python3.11)
echo "PYTHON=${PYTHON}"

$PYTHON /tools/action.py
