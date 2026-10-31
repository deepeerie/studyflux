#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
# Preserve the runtime used by the original two-Mac launcher.
export STUDYFLUX_RUNTIME="${STUDYFLUX_RUNTIME:-$HOME/Library/Application Support/StudyFlux}"
exec sh scripts/bootstrap.sh cloud "$@"
