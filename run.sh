#!/bin/bash -e

if [ -f .venv/bin/activate ]; then
    echo   "Load Python virtualenv from 'my_env/bin/activate'"
    source my_env/bin/activate
fi
exec "$@"
