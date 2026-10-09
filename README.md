# Chaos Blanket Planner

A Django app for planning chaos blankets: a stitch database plus a project
planner that draws random stitches, colors, and row counts. See `SPEC.md`.

## Run locally

Requires Python 3.12.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_dev
.venv/bin/python manage.py runserver
```

`seed_dev` creates the superuser `admin` with password `admin` and some public
development stitches. It is safe to run more than once.

Open <http://127.0.0.1:8000/> and log in as `admin`. To add another user,
create an invite at <http://127.0.0.1:8000/admin/accounts/invite/add/>, save
it, and open the signup link it shows.

## Tests

```sh
.venv/bin/coverage run manage.py test
.venv/bin/coverage report
```

The coverage report fails under 100%.
