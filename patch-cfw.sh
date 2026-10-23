#!/bin/sh
# POSIX sh: Linux, macOS, WSL and Git Bash. Requires Python 3, no pip packages.
set -eu
script_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
if [ -n "${PYTHON:-}" ]; then
    python_command=$PYTHON
elif command -v python3 >/dev/null 2>&1; then
    python_command=python3
elif command -v python >/dev/null 2>&1; then
    python_command=python
else
    printf '%s\n' 'Python 3 is required. Install Python or set PYTHON to its executable path.' >&2
    exit 2
fi
exec "$python_command" "$script_dir/native-cfw/patch.py" "$@"
