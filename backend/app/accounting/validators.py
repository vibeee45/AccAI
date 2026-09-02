from decimal import Decimal


def validate_balanced_entry(lines) -> None:

    total_debit = sum(
        (
            line.debit or Decimal("0.00")
            for line in lines
        ),
        Decimal("0.00"),
    )

    total_credit = sum(
        (
            line.credit or Decimal("0.00")
            for line in lines
        ),
        Decimal("0.00"),
    )

    if total_debit != total_credit:
        raise ValueError(
            f"Journal entry is unbalanced: "
            f"debit={total_debit}, "
            f"credit={total_credit}"
        )