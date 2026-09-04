from __future__ import annotations

from .config import DebitCreditConfig
from .rules import (
    accounts_can_form_pair,
    get_normal_balance,
    get_reason,
    get_transaction_direction,
)
from .schemas import (
    DebitCredit,
    DebitCreditPairPrediction,
    DebitCreditPrediction,
)


class DebitCreditPredictor:
    """
    Predict debit/credit direction for accounting accounts.

    Transaction-specific rules are preferred when a transaction class
    is available. Otherwise, the account's normal balance is used.

    Unknown accounts receive a low-confidence debit fallback and are
    always marked for human review.
    """

    def __init__(
        self,
        config: DebitCreditConfig | None = None,
    ) -> None:
        self.config = config or DebitCreditConfig()

    @staticmethod
    def _validate_string(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return value

    def _requires_review(
        self,
        confidence: float,
    ) -> bool:
        return confidence < self.config.confidence_threshold

    def predict(
        self,
        account_id: str,
        account_name: str,
        transaction_class: str | None = None,
    ) -> DebitCreditPrediction:
        """
        Predict the accounting direction for one account.
        """

        account_id = self._validate_string(
            account_id,
            "account_id",
        )

        account_name = self._validate_string(
            account_name,
            "account_name",
        )

        if transaction_class is not None:
            transaction_class = self._validate_string(
                transaction_class,
                "transaction_class",
            ).lower()

        normalized_account_id = account_id.lower()

        # ---------------------------------------------------------
        # Transaction-specific rule
        # ---------------------------------------------------------
        if transaction_class is not None:
            transaction_direction = get_transaction_direction(
                transaction_class,
                normalized_account_id,
            )

            if transaction_direction is not None:
                reason = (
                    f"{account_name} is {transaction_direction.value} "
                    f"for the '{transaction_class}' transaction class."
                )

                confidence = self.config.rule_confidence

                return DebitCreditPrediction(
                    account_id=account_id,
                    account_name=account_name,
                    direction=transaction_direction,
                    confidence=confidence,
                    reason=reason,
                    requires_review=self._requires_review(
                        confidence
                    ),
                )

        # ---------------------------------------------------------
        # Explicit account rule / normal balance
        # ---------------------------------------------------------
        normal_balance = get_normal_balance(
            normalized_account_id
        )

        if normal_balance is not None:
            reason = get_reason(
                normalized_account_id
            )

            confidence = self.config.rule_confidence

            return DebitCreditPrediction(
                account_id=account_id,
                account_name=account_name,
                direction=normal_balance,
                confidence=confidence,
                reason=reason,
                requires_review=self._requires_review(
                    confidence
                ),
            )

        # ---------------------------------------------------------
        # Unknown account fallback
        # ---------------------------------------------------------
        confidence = self.config.fallback_confidence

        return DebitCreditPrediction(
            account_id=account_id,
            account_name=account_name,
            direction=DebitCredit.DEBIT,
            confidence=confidence,
            reason=(
                "No explicit accounting rule found for this account. "
                "A default debit direction is being used and human "
                "review is required."
            ),
            requires_review=True,
        )

    def predict_pair(
        self,
        debit_account_id: str,
        debit_account_name: str,
        credit_account_id: str,
        credit_account_name: str,
        transaction_class: str | None = None,
    ) -> DebitCreditPairPrediction:
        """
        Validate and predict a debit/credit account pair.
        """

        debit_account_id = self._validate_string(
            debit_account_id,
            "debit_account_id",
        )

        debit_account_name = self._validate_string(
            debit_account_name,
            "debit_account_name",
        )

        credit_account_id = self._validate_string(
            credit_account_id,
            "credit_account_id",
        )

        credit_account_name = self._validate_string(
            credit_account_name,
            "credit_account_name",
        )

        debit_id = debit_account_id.lower()
        credit_id = credit_account_id.lower()

        # Debit and credit accounts must be different.
        if debit_id == credit_id:
            raise ValueError(
                "Debit and credit accounts must be different."
            )

        # Transaction-specific validation.
        if transaction_class is not None:
            transaction_class = self._validate_string(
                transaction_class,
                "transaction_class",
            ).lower()

            if not accounts_can_form_pair(
                transaction_class,
                debit_id,
                credit_id,
            ):
                raise ValueError(
                    f"Invalid debit/credit pair for transaction "
                    f"class '{transaction_class}'."
                )

        # Generic pair validation.
        else:
            debit_direction = get_normal_balance(debit_id)
            credit_direction = get_normal_balance(credit_id)

            # A credit-normal account cannot be proposed as debit.
            if debit_direction == DebitCredit.CREDIT:
                raise ValueError(
                    f"The proposed debit account "
                    f"'{debit_account_id}' normally has a "
                    "credit balance."
                )

            # Unknown debit account cannot form a trusted pair.
            if debit_direction is None:
                raise ValueError(
                    f"No explicit accounting rule found for "
                    f"debit account '{debit_account_id}'."
                )

            # Cash is not accepted as a generic credit-side
            # account by this predictor API. Bank is allowed
            # because it is commonly used as the payment-side
            # account for expenses.
            if (
                credit_direction == DebitCredit.DEBIT
                and credit_id == "cash"
            ):
                raise ValueError(
                    f"The proposed credit account "
                    f"'{credit_account_id}' is not valid for "
                    "the generic credit-side role."
                )

            # Unknown credit account cannot form a trusted pair.
            if credit_direction is None:
                raise ValueError(
                    f"No explicit accounting rule found for "
                    f"credit account '{credit_account_id}'."
                )

        debit_prediction = self.predict(
            debit_id,
            debit_account_name,
            transaction_class,
        )

        credit_prediction = self.predict(
            credit_id,
            credit_account_name,
            transaction_class,
        )

        confidence = min(
            debit_prediction.confidence,
            credit_prediction.confidence,
        )

        requires_review = (
            debit_prediction.requires_review
            or credit_prediction.requires_review
        )

        return DebitCreditPairPrediction(
            debit_account_id=debit_account_id,
            debit_account_name=debit_account_name,
            credit_account_id=credit_account_id,
            credit_account_name=credit_account_name,
            confidence=confidence,
            requires_review=requires_review,
        )

    def predict_many(
        self,
        accounts,
        transaction_class: str | None = None,
    ) -> list[DebitCreditPrediction]:
        """
        Predict directions for multiple accounts.

        Supports the existing project input format:

            [
                ("cash", "Cash"),
                ("sales", "Sales"),
            ]

        and also dictionaries:

            [
                {
                    "account_id": "cash",
                    "account_name": "Cash",
                }
            ]
        """

        if not accounts:
            raise ValueError(
                "accounts cannot be empty."
            )

        predictions: list[DebitCreditPrediction] = []

        for account in accounts:

            if isinstance(account, dict):
                account_id = account["account_id"]
                account_name = account["account_name"]

            elif (
                isinstance(account, (tuple, list))
                and len(account) == 2
            ):
                account_id = account[0]
                account_name = account[1]

            else:
                raise TypeError(
                    "Each account must be a "
                    "(account_id, account_name) pair "
                    "or a dictionary."
                )

            predictions.append(
                self.predict(
                    account_id=account_id,
                    account_name=account_name,
                    transaction_class=transaction_class,
                )
            )

        return predictions

    def is_ready(self) -> bool:
        """
        Return whether the predictor is configured and ready.
        """

        return self.config is not None

