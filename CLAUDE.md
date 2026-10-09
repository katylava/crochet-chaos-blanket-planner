# Chaos Blanket Planner

A Django app for planning crocheted chaos blankets. `SPEC.md` is the source of
truth for behavior. Read it before changing features.

## Spec

- When I add or change a requirement, update `SPEC.md` in the same commit as the
  code.
- If the spec doesn't cover something, ask me. Don't fill the gap with a guess.

## Keeping this file current

- After any change, check whether it made anything in this file inaccurate,
  such as commands, app layout, testing rules, or data rules. If it did, update
  this file in the same commit.

## Stack

- Django with server-rendered templates, SQLite, and Django's auth and admin.
- No JavaScript frontend framework.
- Styling is Pico's classless stylesheet from the jsdelivr CDN, pinned to an
  exact version in `templates/base.html`, plus a small `<style>` block there.
  Keep the UI basic, but not unstyled.
- Templates live in the top-level `templates/` directory, not in the apps.

## Apps

- `accounts`: invite-only signup. The site owner creates single-use invites in
  the admin.
- `stitches`: the stitch database, stitch pages, photo handling
  (`stitches/photos.py`), and the `seed_dev` command.
- `planner`: projects, draws, the repeat rule and fit check
  (`planner/rules.py`), the size guide, the diary, and sharing.

## Commands

- Run tests with coverage: `.venv/bin/coverage run manage.py test` then
  `.venv/bin/coverage report`.
- Run the server: `.venv/bin/python manage.py runserver`.
- Seed dev data: `.venv/bin/python manage.py seed_dev`. It creates the superuser
  `admin` with password `admin` and public stitches with instructions. It's safe
  to rerun, and it keeps instructions I've edited.

## Testing

- Coverage must stay at 100%, including branches. `.coveragerc` enforces it.
  Don't add `# pragma: no cover` or omit entries unless the code truly can't be
  tested here, and tell me when you do.
- Follow red-green TDD: one failing test, then the minimum code to pass it.
- Tests that save photos must override `MEDIA_ROOT` with a temp directory and
  clean it up. Follow the existing photo tests.
- A test client upload sends the real file, so a faked `size` attribute doesn't
  survive the request. To test the 10 MB limit through a view, upload a real
  file over 10 MB, such as an uncompressed BMP.
- Don't assert that a short word is absent from a page. Random CSRF tokens can
  contain it. Assert on longer text instead.
- Playwright is installed so you can check the running app yourself. Use it to
  look at pages after UI changes. Don't add Playwright tests to the suite. Put
  check scripts in your scratchpad, not the repo.

## Data rules

- A stitch's `source` is the URL the stitch data came from. It isn't for photo
  attribution.
- A stitch's `photo_credit` holds the photo's author and license.
- Photos are resized to 1200 px wide JPEGs on upload. Only the resized file is
  kept.
- The shared project page shows only what `SPEC.md` lists. Never add stitch
  details, instructions, or photos to it.
