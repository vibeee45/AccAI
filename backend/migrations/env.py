from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.core.database import Base

# Import every SQLAlchemy model so that they are registered
# in Base.metadata before Alembic compares the schema.
from app.models import (  # noqa: F401
    User,
    Company,
    CompanyUser,
    FinancialPeriod,
    ChartOfAccount,
    Transaction,
    JournalEntry,
    JournalLine,
    AIPrediction,
    AICorrection,
    Anomaly,
    AuditLog,
)


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def get_database_url() -> str:
    """
    Get the database URL from ACCAI settings.

    This allows Alembic to use the same DATABASE_URL
    as the FastAPI application.
    """
    return settings.database_url


def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations using a live database connection.
    """
    configuration = config.get_section(config.config_ini_section)

    if configuration is None:
        configuration = {}

    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()