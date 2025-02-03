#!/bin/sh

DEFAULT_PY_MINOR_VER=12

_usage() {
    cat <<__EOF__
Usage: $0 [PY-MINOR-VERSION] <PY-FILE>

Run the <PY-FILE> using the specified version of Python. By default it uses
Python 3.${DEFAULT_PY_MINOR_VER}.
__EOF__
}

test $# -eq 1 -o $# -eq 2 || {
    _usage
    exit 1
}

if [ $# -eq 1 ]; then
    PY_MINOR_VER="${DEFAULT_PY_MINOR_VER}"
    PY_FILE="$1"
else
    PY_MINOR_VER="$1"
    PY_FILE="$2"
fi

docker run \
  -it --rm \
  --name my-running-script \
  -v "$PWD":/usr/src/myapp \
  -w /usr/src/myapp \
  "python:3.${PY_MINOR_VER}" \
  python "${PY_FILE}"
