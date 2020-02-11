#!/usr/bin/env bash

set -e

cmd="$@"

DO_MIGRATION=${DO_MIGRATION:-n}
DO_STATIC=${DO_STATIC:-n}

if [[ $DO_MIGRATION = y ]]; then
    python /app/manage.py migrate
fi

if [[ $DO_STATIC = y ]]; then
    python /app/manage.py collectstatic
fi

echo "[ * ] Starting app"
exec $cmd
