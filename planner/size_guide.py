"""Blanket sizes for choosing a stitch count per row, assuming weight 4 yarn.

Each range is width x 2.75 to width x 3.5 stitches, which is 11 to 14 single
crochet per 4 inches, rounded half up to whole stitches.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

LOW_PER_INCH = Decimal("2.75")
HIGH_PER_INCH = Decimal("3.5")


def round_half_up(value):
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Size:
    name: str
    width: int
    note: str = ""

    @property
    def low(self):
        return round_half_up(self.width * LOW_PER_INCH)

    @property
    def high(self):
        return round_half_up(self.width * HIGH_PER_INCH)


PRACTICE_NOTE = (
    "Try all your stitches at practice size with scrap yarn, not your project yarn. "
    "Use it to experiment with padding, turning chains, and matching tension. "
    "Some stitches might need a different hook size to match the others."
)

GUIDE_TEXT = (
    "Different yarns and stitches go into a chaos blanket, so there's no easy way to tell "
    "where yours will fall in this range. Pick a number and embrace the chaos."
)

SIZES = [
    Size("Practice", 18, PRACTICE_NOTE),
    Size("Baby", 36),
    Size("Lap", 36),
    Size("Throw", 50),
    Size("Twin", 66),
    Size("Full", 80),
    Size("Queen", 90),
    Size("King", 108),
]
