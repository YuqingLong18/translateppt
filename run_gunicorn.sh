#!/bin/bash
source /www/server/panel/pyenv/translate/bin/activate
exec gunicorn 'backend.app:create_app()' \
  --bind 127.0.0.1:9003 \
  --workers 3 --threads 4 --timeout 120 \
  --chdir /www/wwwroot/translateppt/backend