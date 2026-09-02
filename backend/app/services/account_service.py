from uuid import UUID

from sqlalchemy.orm import Session

from app.models.account import ChartOfAccount
from app.repositories.account_repository import AccountRepository
from app.repositories.company_repository import CompanyRepository
from app.schemas.account import AccountCreate, AccountUpdate


class AccountService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = AccountRepository(db)
        self.company_repository = CompanyRepository(db)

    def get_account(
        self,
        account_id: UUID,
    ) -> ChartOfAccount:

        account = self.repository.get_by_id(account_id)

        if account is None:
            raise ValueError("Account not found")

        return account

    def list_accounts(
        self,
        company_id: UUID,
        active_only: bool = False,
    ) -> list[ChartOfAccount]:

        company = self.company_repository.get_by_id(company_id)

        if company is None:
            raise ValueError("Company not found")

        return self.repository.list_by_company(
            company_id,
            active_only=active_only,
        )

    def create_account(
        self,
        data: AccountCreate,
    ) -> ChartOfAccount:

        company = self.company_repository.get_by_id(
            data.company_id
        )

        if company is None:
            raise ValueError("Company not found")

        existing = self.repository.get_by_company_and_code(
            data.company_id,
            data.code,
        )

        if existing is not None:
            raise ValueError(
                f"Account code '{data.code}' already exists"
            )

        if data.parent_id is not None:
            parent = self.repository.get_parent(
                data.parent_id
            )

            if parent is None:
                raise ValueError(
                    "Parent account not found"
                )

            if parent.company_id != data.company_id:
                raise ValueError(
                    "Parent account must belong to the same company"
                )

        account = ChartOfAccount(
            company_id=data.company_id,
            parent_id=data.parent_id,
            code=data.code,
            name=data.name,
            account_type=data.account_type,
            normal_balance=data.normal_balance,
            is_active=data.is_active,
        )

        self.repository.create(account)

        self.db.commit()
        self.db.refresh(account)

        return account

    def update_account(
        self,
        account_id: UUID,
        data: AccountUpdate,
    ) -> ChartOfAccount:

        account = self.get_account(account_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        if "code" in update_data:
            existing = self.repository.get_by_company_and_code(
                account.company_id,
                update_data["code"],
            )

            if (
                existing is not None
                and existing.id != account.id
            ):
                raise ValueError(
                    f"Account code '{update_data['code']}' already exists"
                )

        if "parent_id" in update_data:
            parent_id = update_data["parent_id"]

            if parent_id is not None:
                parent = self.repository.get_parent(
                    parent_id
                )

                if parent is None:
                    raise ValueError(
                        "Parent account not found"
                    )

                if parent.company_id != account.company_id:
                    raise ValueError(
                        "Parent account must belong to the same company"
                    )

                if parent.id == account.id:
                    raise ValueError(
                        "An account cannot be its own parent"
                    )

        for field, value in update_data.items():
            setattr(account, field, value)

        self.db.commit()
        self.db.refresh(account)

        return account