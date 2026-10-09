# Chaos Blanket Planner: MVP spec

_Written by Claude from a requirements conversation with the user. The user did
not author this text._

This spec is for the Claude session that builds the MVP. No code exists yet.
Every requirement below was confirmed with the user unless it says otherwise.

## What the app does

A chaos blanket is a crocheted blanket built from a sequence of random draws.
Each draw picks a stitch, one or two colors, and a number of rows. The crocheter
works those rows, then draws again. The app has two parts:

- **Stitch database:** crochet stitches and the numbers the planner needs about
  each one.
- **Project planner:** a project is a set of chosen stitches and colors plus
  draw settings. The planner does the draws, keeps their history, and tells the
  crocheter how many padding stitches each draw needs.

## Stack

- Django, with server-rendered templates. Django's auth covers accounts, and its
  admin site covers the owner's management of public stitches.
- SQLite. The data is small and has few concurrent writers.
- The app runs on the user's own server.

Don't add a JavaScript frontend framework. The UI is forms, lists, and a draw
button, so server-rendered pages cover it.

## Users and stitch visibility

Signing up requires an invite from the site owner during the beta, which
includes the MVP. The owner creates invites through the admin site. Each user
has their own projects.

| Stitch kind | Who can add it                             | Who can see it      |
| ----------- | ------------------------------------------ | ------------------- |
| Public      | Only the site owner, through the admin site | Every user          |
| Private     | Any user, through the app's stitch form     | Only the user who added it |

The site owner is the user who commissioned this app. Before user feedback, they
will add stitches by copying data from other websites. They will keep that data
private to avoid copyright infringement.

## Stitch database

| Field         | Required | Default | Meaning                                                                                       |
| ------------- | -------- | ------- | --------------------------------------------------------------------------------------------- |
| name          | yes      |         | The stitch's name.                                                                            |
| multiple      | yes      |         | `N` in "multiple of N + M": the number of stitches in one repeat.                            |
| edge stitches | no       | 0       | `M` in "multiple of N + M", counting only stitches that appear in every row.                 |
| colors        | no       | 1       | 1 or 2. A two-color stitch needs two different colors per draw.                              |
| instructions  | no       |         | How to work the stitch, as plain text. Line breaks are kept when shown.                      |
| source        | no       |         | The URL the stitch data came from.                                                           |
| photo         | no       |         | An uploaded image of the stitch. See the photo storage rules below the table.                |

Each stitch also has an owner and a public or private flag.

Each stitch has a page that shows its photo, numbers, source, and instructions.
The stitch list, a project's stitch list, and each draw in a project's history
link to it. The shared project page doesn't.

**Photo storage:**

- Reject uploads over 10 MB. The limit is high so that unedited phone photos
  fit.
- Resize every upload to 1200 px wide and save it as JPEG. Keep only the
  resized file. A resized photo is roughly 100 to 300 KB, which is Claude's
  estimate, not a measurement.
- Store photos on the server's local disk through Django's storage API. Moving
  to bucket storage later is then a settings change using django-storages.
- Accept HEIC, because iPhones save photos as HEIC by default. Pillow reads HEIC
  only with the pillow-heif plugin.

**Turning chains never count as stitches in this app.** Printed patterns often
fold turning chains into their "+ M", so a pattern's printed M can be larger
than the edge-stitch count stored here. The stitch form must tell users to enter
only the extra stitches that appear in every row. The padding math below depends
on this convention.

Seed the database with common stitches for development. Include at least one
two-color stitch, and stitches with different multiples and edge-stitch counts,
so that padding is nonzero for some of them. The seed values are for
development, not authoritative.

After development and before user feedback, the site owner fills the database
with real stitches by researching them online and entering them through the
admin site.

## Projects

A project holds:

- a name
- the stitches chosen from the database
- the colors chosen by the user, entered as names (for example "rust", "cream")
- the stitch count per row, entered by the user
- notes: optional free text about the project. The form's help text suggests
  recording the hook size, so the crocheter doesn't forget which hook they used.
- the minimum and maximum rows per draw
- `N`, the number of draws before a drawn stitch or color can be drawn again
- the draw history

Don't add a row-repeat field to stitches or round drawn row counts. The
crocheter decides how a drawn row count applies to a stitch whose motif spans
several rows.

All yarn is assumed to be weight 4 (worsted) in the MVP.

### Deactivating stitches and colors

The user can deactivate any of a project's stitches or colors, for example when
they run out of a yarn or tire of a stitch. Deactivation applies only to that
project. New draws and rerolls skip deactivated stitches and colors. Existing
draws keep them. The user can reactivate them.

### Usage counts

The project shows, for each of its stitches and colors, the number of draws that
used it and the total rows across those draws. Both colors of a two-color draw
count. The counts help the user decide what to deactivate.

### Diary

A project has a diary. Each entry has a date and time, text, and at most one progress
photo. An entry needs text or a photo, and can have both. Progress photos follow
the same storage rules as stitch photos.

When a project's diary is empty, the diary prompts the user to make the first
entry a photo of all the yarns for the project.

### Public sharing

The user can turn on public sharing for a project. Sharing gives the project a short,
unguessable link. The link's token is 10 random characters from letters and
digits, generated with Python's `secrets` module. That gives about 60 bits of
randomness, which is too many combinations to guess, and keeps the URL short.
Anyone with the link can view the shared page without an
account. The project is not listed anywhere. Turning sharing off makes the link
stop working. Turning it back on restores the same link, so the token is
generated once and kept.

The shared page is read-only and shows only:

- the project name and stitch count per row
- stitch names, with no other stitch data and no stitch photos. Private stitches
  hold data copied from other websites, so only their names are public.
- the colors
- the draw history, as a simple list of each draw's stitch, colors, and row
  count, without padding or the owner's controls
- the progress photos from the diary, without the diary text

### Size guide for the stitch count

When the user sets the stitch count per row, show this guide. Each range is the
width times 2.75 to the width times 3.5, rounded to whole stitches. That is 11
to 14 single crochet per 4 inches, the gauge range for weight 4 yarn. The user
confirmed this range across several sources.

| Size     | Width (inches) | Stitch count range |
| -------- | -------------- | ------------------ |
| Practice | 18             | 50 to 63           |
| Baby     | 36             | 99 to 126          |
| Lap      | 36             | 99 to 126          |
| Throw    | 50             | 138 to 175         |
| Twin     | 66             | 182 to 231         |
| Full     | 80             | 220 to 280         |
| Queen    | 90             | 248 to 315         |
| King     | 108            | 297 to 378         |

Show this text with the guide:

> Different yarns and stitches go into a chaos blanket, so there's no easy way
> to tell where yours will fall in this range. Pick a number and embrace the
> chaos.

Show this text next to the practice size:

> Try all your stitches at practice size with scrap yarn, not your project
> yarn. Use it to experiment with padding, turning chains, and matching
> tension. Some stitches might need a different hook size to match the others.

Lap, throw, twin, full, queen, and king use the widths most size charts agree
on, checked against Oombawka Design, A Crocheted Simplicity, You Should Craft,
Ned & Mimi, and Sarah Maker. Baby sizes vary from about 30 to 40 inches across
those charts, so 36 is a middle value.

## Draws

Each draw picks:

1. One stitch from the project's stitches.
2. One color, or two different colors if the stitch needs two.
3. A row count between the project's minimum and maximum, inclusive.

**Repeat rule:** a stitch or color that appears in any of the last `N` draws
can't be drawn. One `N` applies to both stitches and colors. Both colors of a
two-color draw count. With `N` = 2:

| Draw | Colors      | Colors blocked for this draw |
| ---- | ----------- | ---------------------------- |
| 1    | red         | none                         |
| 2    | blue, cream | red                          |
| 3    | green       | red, blue, cream             |
| 4    | red         | blue, cream, green           |

Check that `N` fits the project when the user saves its settings, and when they
deactivate a stitch or color. If it doesn't fit, block the change and show an
error that says whether stitches or colors are too few. Chaos blankets use many
stitches and colors, so this only fails when a project is configured wrong.
`N` fits when:

- active stitches > `N`
- active colors ≥ `N` + 1 if no active stitch needs two colors
- active colors ≥ 2`N` + 2 if any active stitch needs two colors, because the
  last `N` draws can block up to 2`N` colors and the next draw can need 2 more

### Padding

Each draw shows how many padding stitches the crocheter adds at the row ends,
so the stitch fits the row:

```
padding = (stitch count per row − edge stitches) mod multiple
```

For example, with 150 stitches per row and a stitch with multiple 6 and 1 edge
stitch, padding is `149 mod 6` = 5. Padding means simple stitches, such as
single crochet, split between the start and end of the row. The app shows the
split. When padding is odd, the start gets the extra stitch, so 5 shows as 3 at
the start and 2 at the end, and 1 shows as 1 at the start. The extra goes at the
start to balance the row, on the assumption that a stitch's edge stitches sit
at the end of the row. The user got this
method from a crocheter who makes chaos blankets.

Because padding absorbs any mismatch, every stitch count per row works with
every stitch.

### Draw history

The project lists its draws in order. For any draw, the user can:

- **Delete it:** for draws the user rejected.
- **Edit it:** change the stitch, colors, or row count by hand, for when the
  crocheter changed something while working. Manual edits are not checked
  against the repeat rule.
- **Reroll it:** replace its stitch, colors, and row count with a new random
  draw that follows the repeat rule against the current history.

The repeat rule reads the draws currently in the history. A deleted draw is
gone, so it doesn't count. An edited draw counts with its edited values.

A reroll checks the `N` draws before the rerolled draw, the same as a new
draw.

## Planned after the MVP

- Yarn weights other than 4.

## Not planned

- Tracking which row the crocheter is on. The user declined this feature. The
  draw history and diary are the record of progress.
