#!/bin/sh
set -eu
exec "$(dirname "$0")/../start.sh" "$@"
