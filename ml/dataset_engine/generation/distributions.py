from __future__ import annotations

import random
from decimal import Decimal


def generate_amount(
    rng: random.Random,
    minimum: Decimal,
    maximum: Decimal,
) -> Decimal:
    value = rng.uniform(float(minimum), float(maximum))
    return Decimal(str(round(value, 2)))


def generate_date(
    rng: random.Random,
    start_date,
    end_date,
):
    day_range = (end_date - start_date).days

    if day_range == 0:
        return start_date

    return start_date.fromordinal(
        start_date.toordinal() + rng.randint(0, day_range)
    )
