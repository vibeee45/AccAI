from uuid import UUID

from sqlalchemy.orm import Session

from app.models.company import Company, CompanyUser
from app.models.enums import CompanyRole
from app.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyUserCreate,
)


class CompanyService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = CompanyRepository(db)

    def get_company(self, company_id: UUID) -> Company:
        company = self.repository.get_by_id(company_id)

        if company is None:
            raise ValueError("Company not found")

        return company

    def list_companies(self) -> list[Company]:
        return self.repository.list_all()

    def create_company(
        self,
        data: CompanyCreate,
        owner_user_id: UUID,
    ) -> Company:

        existing = self.repository.get_by_name(data.name)

        if existing is not None:
            raise ValueError(
                "A company with this name already exists"
            )

        user = self.db.get(User, owner_user_id)

        if user is None:
            raise ValueError("Owner user not found")

        company = Company(
            name=data.name,
            legal_name=data.legal_name,
            currency=data.currency,
            financial_year_start=data.financial_year_start,
        )

        self.repository.create(company)

        membership = CompanyUser(
            company_id=company.id,
            user_id=owner_user_id,
            role=CompanyRole.OWNER,
        )

        self.repository.add_user(membership)

        self.db.commit()
        self.db.refresh(company)

        return company

    def update_company(
        self,
        company_id: UUID,
        data: CompanyUpdate,
    ) -> Company:

        company = self.get_company(company_id)

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(company, field, value)

        self.db.commit()
        self.db.refresh(company)

        return company

    def add_user(
        self,
        company_id: UUID,
        data: CompanyUserCreate,
    ) -> CompanyUser:

        self.get_company(company_id)

        user = self.db.get(User, data.user_id)

        if user is None:
            raise ValueError("User not found")

        existing = self.repository.get_membership(
            company_id,
            data.user_id,
        )

        if existing is not None:
            raise ValueError(
                "User is already a member of this company"
            )

        membership = CompanyUser(
            company_id=company_id,
            user_id=data.user_id,
            role=data.role,
        )

        self.repository.add_user(membership)

        self.db.commit()
        self.db.refresh(membership)

        return membership

    def list_members(
        self,
        company_id: UUID,
    ) -> list[CompanyUser]:

        self.get_company(company_id)

        return self.repository.list_members(company_id)