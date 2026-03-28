import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Project imports ───────────────────────────────────────────────────────────
from config import get_settings

# Import all models so their tables are registered on Base.metadata
import app.infrastructure.database.models  # noqa: F401
from app.infrastructure.database.models.university_model import UniversityModel  # noqa: F401
from app.infrastructure.database.models.internship_model import InternshipModel  # noqa: F401
from app.infrastructure.database.models.internship_recommendation_model import InternshipRecommendationModel  # noqa: F401
from app.infrastructure.database.models.student_profile_model import StudentProfileModel  # noqa: F401
from app.infrastructure.database.models.apartment_model import ApartmentModel  # noqa: F401
from app.infrastructure.database.models.chat_models import ChatRoomModel, ChatRoomMemberModel, ChatMessageModel, ChatRequestModel  # noqa: F401
from app.infrastructure.database.models.forum_model import ForumPostModel, ForumCommentModel, ForumLikeModel, ForumReportModel  # noqa: F401
from app.infrastructure.database.base import Base

# ── Alembic config ────────────────────────────────────────────────────────────
alembic_cfg = context.config

if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

_settings = get_settings()

alembic_cfg.set_main_option("sqlalchemy.url", _settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        alembic_cfg.get_section(alembic_cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
