#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
# Each checkout gets its own environment and database, outside cloud-synced Documents.
checkout_id=$(printf '%s' "$PWD" | shasum -a 256 | cut -c1-16)
export STUDYFLUX_RUNTIME="${STUDYFLUX_RUNTIME:-$HOME/Library/Application Support/StudyFlux/local/$checkout_id}"
exec sh scripts/bootstrap.sh local "$@"
