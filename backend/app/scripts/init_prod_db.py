import asyncio
import logging
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import engine
from app.models import Base  # Loads all models onto Base.metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_prod_db")


async def init_prod_db():
    """
    Initialize missing production database tables non-destructively.
    This function will NEVER call drop_all() or delete existing data.
    It is safe to execute multiple times against a production database.
    """
    logger.info("Initializing production database schema (NON-DESTRUCTIVE)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Production database tables verified/created successfully.")


if __name__ == "__main__":
    asyncio.run(init_prod_db())
