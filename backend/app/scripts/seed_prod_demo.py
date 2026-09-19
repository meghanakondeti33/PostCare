import asyncio
import logging
import os
import sys
from sqlalchemy import select

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import AsyncSessionLocal
from app.models.domain import Hospital
from app.scripts.seed_data import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_prod_demo")


async def seed_prod_demo():
    """
    Safely seed initial demo data for production deployment.
    This script is 100% NON-DESTRUCTIVE:
    - NEVER calls drop_all()
    - Idempotent: Checks if Hospital data already exists before seeding
    - Safe to run on deployed instance startup or build steps
    """
    logger.info("Checking production database for existing records...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Hospital).limit(1))
        existing_hospital = result.scalars().first()
        if existing_hospital:
            logger.info(
                f"Production database already contains data (found hospital '{existing_hospital.name}'). "
                "Skipping seed to preserve production state."
            )
            return

    logger.info("Database is empty. Populating initial production demo dataset (NON-DESTRUCTIVE)...")
    await seed_database(drop_existing=False)
    logger.info("Production demo dataset seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed_prod_demo())
