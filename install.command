#!/bin/sh
# Double-click this in Finder to run the UI+ installer in Terminal (the first time: right-click it, Open).
# It needs python3, which macOS offers to install with its command line developer tools on first use.
cd "$(dirname "$0")" || exit 1
exec /usr/bin/env python3 install.py "$@"
