#!/usr/bin/env bash
# Render build step for the PharmaDesk backend. Installs deps, gathers static
# files (Django admin + DRF — the React UI is hosted separately on Vercel),
# applies migrations, and ensures the shared login exists.
set -o errexit

pip install -r requirements-prod.txt

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py ensure_login
