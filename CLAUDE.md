# Chaos Blanket Planner

`SPEC.md` is the source of truth for behavior. Read it before changing features.

## Spec

- When I add or change a requirement, update `SPEC.md` in the same commit as the
  code.
- If the spec doesn't cover something, ask me. Don't fill the gap with a guess.
- The spec can miss things users obviously need. When you notice a gap, raise it
  with me instead of building only what's written.

## UI

- Keep the UI basic, but not unstyled.
- Plain JavaScript is fine where it helps. The spec rules out only a frontend
  framework. Keep pages usable without JavaScript.
- Write UI text in the words crocheters use, not the code's terms. If wording is
  uncertain, propose options and agree on them with me before building.
- Lay out each page around what the user is there to do. The information they
  came for is the most prominent thing on the page. Actions get emphasis by how
  often they're used, so rare actions stay quiet.
- Design for real data volumes, not the seed data. The stitch database will hold
  hundreds of public stitches.
- Passing tests isn't enough for UI work. Look at each changed page in a browser
  at phone and desktop widths, the way a user would.
- Playwright is installed in the global `python3`, not the venv, so you can check
  pages yourself. Keep check scripts in your scratchpad. Don't add Playwright
  tests to the suite.

## Testing

- Coverage stays at 100%, including branches. Don't add `# pragma: no cover` or
  coverage omits unless the code truly can't be tested here, and tell me when
  you do.
- A test client upload sends the real file, so a faked `size` attribute doesn't
  survive the request. To test the 10 MB photo limit through a view, upload a
  real file over 10 MB, such as an uncompressed BMP.
- Don't assert that a short word is absent from a page. Random CSRF tokens can
  contain it. Assert on longer text instead.

## Keeping this file current

- After any change, check whether it made anything in this file inaccurate. If
  it did, update this file in the same commit.
- Only add what isn't documented elsewhere or would take a lot of exploration to
  find out.
