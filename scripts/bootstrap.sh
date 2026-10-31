#!/bin/sh
set -eu
mode="$1"
shift
if [ "$(uname -s)" != Darwin ]; then
    echo 'This launcher currently supports macOS only.' >&2
    exit 1
fi
umask 077
mkdir -p "$STUDYFLUX_RUNTIME"
export UV_PYTHON_INSTALL_DIR="$STUDYFLUX_RUNTIME/python"
export UV_CACHE_DIR="$STUDYFLUX_RUNTIME/cache"
export PYTHONDONTWRITEBYTECODE=1
uv_version=0.13.6
if [ ! -x "$STUDYFLUX_RUNTIME/bin/uv" ] || [ "$("$STUDYFLUX_RUNTIME/bin/uv" --version | cut -d ' ' -f 2)" != "$uv_version" ]; then
    echo "Installing uv $uv_version from Astral…"
    curl --fail --location --silent --show-error "https://astral.sh/uv/$uv_version/install.sh" -o "$STUDYFLUX_RUNTIME/install-uv.sh"
    UV_INSTALL_DIR="$STUDYFLUX_RUNTIME/bin" UV_NO_MODIFY_PATH=1 sh "$STUDYFLUX_RUNTIME/install-uv.sh"
fi
if [ ! -x "$STUDYFLUX_RUNTIME/venv/bin/python" ]; then
    "$STUDYFLUX_RUNTIME/bin/uv" venv --managed-python --python 3.9.25 "$STUDYFLUX_RUNTIME/venv"
fi
if ! cmp -s requirements-local.lock.txt "$STUDYFLUX_RUNTIME/requirements-installed.txt"; then
    "$STUDYFLUX_RUNTIME/bin/uv" pip sync --python "$STUDYFLUX_RUNTIME/venv/bin/python" requirements-local.lock.txt
    cp requirements-local.lock.txt "$STUDYFLUX_RUNTIME/requirements-installed.txt"
fi
exec "$STUDYFLUX_RUNTIME/venv/bin/python" "scripts/start-$mode.py" "$@"
