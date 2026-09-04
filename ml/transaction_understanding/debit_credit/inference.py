from .config import DebitCreditConfig
from .predictor import DebitCreditPredictor
from .schemas import (
    DebitCreditPairPrediction,
    DebitCreditPrediction,
)


class DebitCreditService:
    """
    Application-facing debit/credit prediction service.
    """

    def __init__(
        self,
        predictor: DebitCreditPredictor | None = None,
    ) -> None:
        self.predictor = (
            predictor
            or DebitCreditPredictor(
                DebitCreditConfig()
            )
        )

    def predict(
        self,
        account_id: str,
        account_name: str,
    ) -> DebitCreditPrediction:
        return self.predictor.predict(
            account_id,
            account_name,
        )

    def predict_pair(
        self,
        debit_account_id: str,
        debit_account_name: str,
        credit_account_id: str,
        credit_account_name: str,
    ) -> DebitCreditPairPrediction:
        return self.predictor.predict_pair(
            debit_account_id,
            debit_account_name,
            credit_account_id,
            credit_account_name,
        )

    def predict_many(
        self,
        accounts: list[tuple[str, str]],
    ) -> list[DebitCreditPrediction]:
        return self.predictor.predict_many(
            accounts
        )

    @property
    def ready(self) -> bool:
        return True
