#!/bin/sh

SCRIPT_PATH=$(dirname $(readlink -f $0))

cd "${SCRIPT_PATH}" && /usr/bin/python3 ./run.py
