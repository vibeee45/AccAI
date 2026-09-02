from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company, CompanyUser


class CompanyRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, company_id: UUID) -> Company | None:
        return self.db.get(Company, company_id)

    def get_by_name(self, name: str) -> Company | None:
        statement = select(Company).where(
            Company.name == name
        )

        return self.db.scalars(statement).first()

    def list_all(self) -> list[Company]:
        statement = (
            select(Company)
            .order_by(Company.name)
        )

        return list(self.db.scalars(statement).all())

    def create(self, company: Company) -> Company:
        self.db.add(company)
        self.db.flush()

        return company

    def delete(self, company: Company) -> None:
        self.db.delete(company)

    def add_user(
        self,
        company_user: CompanyUser,
    ) -> CompanyUser:
        self.db.add(company_user)
        self.db.flush()

        return company_user

    def get_membership(
        self,
        company_id: UUID,
        user_id: UUID,
    ) -> CompanyUser | None:

        statement = select(CompanyUser).where(
            CompanyUser.company_id == company_id,
            CompanyUser.user_id == user_id,
        )

        return self.db.scalars(statement).first()

    def list_members(
        self,
        company_id: UUID,
    ) -> list[CompanyUser]:

        statement = (
            select(CompanyUser)
            .where(CompanyUser.company_id == company_id)
            .order_by(CompanyUser.created_at)
        )

        return list(self.db.scalars(statement).all())