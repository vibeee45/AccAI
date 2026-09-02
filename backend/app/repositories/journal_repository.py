from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.journal import JournalEntry, JournalLine
from app.models.enums import JournalStatus


class JournalRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_entry_by_id(
        self,
        entry_id: UUID,
    ) -> JournalEntry | None:

        return self.db.get(
            JournalEntry,
            entry_id,
        )

    def get_entry_with_lines(
        self,
        entry_id: UUID,
    ) -> JournalEntry | None:

        statement = (
            select(JournalEntry)
            .where(JournalEntry.id == entry_id)
        )

        return self.db.scalar(statement)

    def get_next_entry_number(
        self,
        company_id: UUID,
    ) -> int:

        statement = select(
            JournalEntry.entry_number
        ).where(
            JournalEntry.company_id == company_id
        ).order_by(
            JournalEntry.entry_number.desc()
        ).limit(1)

        last_number = self.db.scalar(statement)

        return (last_number or 0) + 1

    def list_by_company(
        self,
        company_id: UUID,
        status: JournalStatus | None = None,
    ) -> list[JournalEntry]:

        statement = select(JournalEntry).where(
            JournalEntry.company_id == company_id
        )

        if status is not None:
            statement = statement.where(
                JournalEntry.status == status
            )

        statement = statement.order_by(
            JournalEntry.entry_date,
            JournalEntry.entry_number,
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create_entry(
        self,
        entry: JournalEntry,
    ) -> JournalEntry:

        self.db.add(entry)
        self.db.flush()

        return entry

    def create_line(
        self,
        line: JournalLine,
    ) -> JournalLine:

        self.db.add(line)
        self.db.flush()

        return line

    def create_entry_with_lines(
        self,
        entry: JournalEntry,
        lines: list[JournalLine],
    ) -> JournalEntry:

        self.db.add(entry)

        for line in lines:
            entry.lines.append(line)

        self.db.flush()

        return entry