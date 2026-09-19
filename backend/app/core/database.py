from typing import Tuple, Dict, Any
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


def prepare_database_config(raw_url: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parses and normalizes a database URL for SQLAlchemy async engines.
    
    1. SQLite:
       - Converts scheme to sqlite+aiosqlite
       - Sets connect_args = {"check_same_thread": False}
       
    2. PostgreSQL (including Neon, Supabase, Render Postgres):
       - Converts postgresql:// or postgres:// scheme to postgresql+asyncpg://
       - Extracts and strips 'sslmode' query parameter (e.g., sslmode=require) from query parameters
         to prevent asyncpg throwing TypeError: connect() got an unexpected keyword argument 'sslmode'
       - Strips asyncpg-incompatible libpq query parameters (e.g. channel_binding, gssencmode, sslcompression)
         to prevent asyncpg throwing TypeError: connect() got an unexpected keyword argument 'channel_binding'
       - Translates 'sslmode' into asyncpg-compatible connect_args["ssl"] = 'require' / 'verify-full' / etc.
         so TLS security remains active.
    """
    try:
        url = make_url(raw_url)
    except Exception:
        if raw_url.startswith("sqlite://"):
            return raw_url.replace("sqlite://", "sqlite+aiosqlite://"), {"check_same_thread": False}
        elif raw_url.startswith("postgresql://"):
            return raw_url.replace("postgresql://", "postgresql+asyncpg://"), {}
        elif raw_url.startswith("postgres://"):
            return raw_url.replace("postgres://", "postgresql+asyncpg://"), {}
        return raw_url, {}

    connect_args: Dict[str, Any] = {}

    if url.drivername.startswith("sqlite"):
        drivername = "sqlite+aiosqlite"
        connect_args["check_same_thread"] = False
        new_url = url.set(drivername=drivername)
        return new_url.render_as_string(hide_password=False), connect_args

    if url.drivername.startswith("postgres"):
        drivername = "postgresql+asyncpg"
        query_dict = dict(url.query)
        
        # Check and extract sslmode from URL query params if present
        sslmode = query_dict.pop("sslmode", None)
        if sslmode:
            sslmode_lower = sslmode.lower()
            if sslmode_lower in ("require", "verify-ca", "verify-full", "prefer", "allow"):
                connect_args["ssl"] = sslmode_lower
            elif sslmode_lower in ("disable", "false", "off", "0"):
                connect_args["ssl"] = False
            else:
                connect_args["ssl"] = "require"

        # Remove asyncpg-incompatible libpq parameters from URL query dict
        incompatible_params = [
            "channel_binding",
            "gssencmode",
            "sslcompression",
            "sslcert",
            "sslkey",
            "sslrootcert",
            "sslcrl",
        ]
        for param in incompatible_params:
            query_dict.pop(param, None)
        
        new_url = url.set(drivername=drivername, query=query_dict)
        return new_url.render_as_string(hide_password=False), connect_args

    return raw_url, connect_args


db_url, connect_args = prepare_database_config(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    echo=False,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

