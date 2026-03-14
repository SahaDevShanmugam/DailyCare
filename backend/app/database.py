from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=False,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def _add_conditions_not_to_take_column(sync_conn):
    try:
        sync_conn.execute(text(
            "ALTER TABLE medications ADD COLUMN conditions_not_to_take TEXT DEFAULT ''"
        ))
    except Exception:
        pass  # Column already exists


def _add_patient_age_sex_columns(sync_conn):
    for col, spec in [("age", "INTEGER"), ("sex", "VARCHAR(10)")]:
        try:
            sync_conn.execute(text(
                f"ALTER TABLE patients ADD COLUMN {col} {spec}"
            ))
        except Exception:
            pass  # Column already exists


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_add_conditions_not_to_take_column)
        await conn.run_sync(_add_patient_age_sex_columns)
