import pytest
from app.core.database import prepare_database_config


def test_sqlite_url_conversion():
    url, connect_args = prepare_database_config("sqlite:///./test.db")
    assert url == "sqlite+aiosqlite:///./test.db"
    assert connect_args == {"check_same_thread": False}

    url_async, connect_args_async = prepare_database_config("sqlite+aiosqlite:///./test.db")
    assert url_async == "sqlite+aiosqlite:///./test.db"
    assert connect_args_async == {"check_same_thread": False}


def test_postgres_url_without_sslmode():
    url, connect_args = prepare_database_config("postgresql://user:secretpass@localhost:5432/postcare")
    assert url == "postgresql+asyncpg://user:secretpass@localhost:5432/postcare"
    assert "ssl" not in connect_args
    assert "sslmode" not in url
    assert "channel_binding" not in url


def test_neon_postgres_url_with_sslmode_require():
    raw = "postgresql://user:secretpass@ep-xyz.neon.tech/postcare?sslmode=require"
    url, connect_args = prepare_database_config(raw)

    # 1. Scheme normalized to postgresql+asyncpg
    assert url.startswith("postgresql+asyncpg://")
    # 2. sslmode stripped from URL query to prevent asyncpg unexpected keyword argument error
    assert "sslmode" not in url
    # 3. SSL translated into asyncpg connect_args["ssl"] = "require"
    assert connect_args.get("ssl") == "require"


def test_neon_postgres_url_with_channel_binding():
    raw = "postgresql://user:secretpass@ep-xyz.neon.tech/postcare?channel_binding=require"
    url, connect_args = prepare_database_config(raw)

    assert url.startswith("postgresql+asyncpg://")
    assert "channel_binding" not in url


def test_neon_postgres_url_with_sslmode_and_channel_binding():
    raw = "postgresql://user:secretpass@ep-xyz.neon.tech/postcare?sslmode=require&channel_binding=require&application_name=postcare_prod"
    url, connect_args = prepare_database_config(raw)

    assert url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in url
    assert "channel_binding" not in url
    assert "application_name=postcare_prod" in url
    assert connect_args.get("ssl") == "require"


def test_postgres_url_with_other_sslmodes():
    # verify-full
    url_vf, connect_args_vf = prepare_database_config(
        "postgresql+asyncpg://user:pass@ep-xyz.neon.tech/postcare?sslmode=verify-full&channel_binding=require"
    )
    assert "sslmode" not in url_vf
    assert "channel_binding" not in url_vf
    assert connect_args_vf.get("ssl") == "verify-full"

    # disable
    url_dis, connect_args_dis = prepare_database_config(
        "postgres://user:pass@localhost:5432/db?sslmode=disable"
    )
    assert "sslmode" not in url_dis
    assert connect_args_dis.get("ssl") is False


@pytest.mark.asyncio
async def test_knowledge_document_chunk_foreign_key_ingestion(seed_test_data):
    """Regression test ensuring parent KnowledgeDocument is committed before child KnowledgeChunk records."""
    from app.rag.protocol_rag import ProtocolRAGService
    from app.models.domain import KnowledgeDocument, KnowledgeChunk
    from tests.conftest import TestingSessionLocal
    from sqlalchemy import select

    async with TestingSessionLocal() as db_session:
        rag = ProtocolRAGService(db_session, "hosp-metro-1")
        doc_id = await rag.ingest_protocol_document(
            title="FK Order Ingestion Test Standard",
            category="Test Category",
            content="Paragraph one test.\n\nParagraph two test content.",
            version="1.0.0"
        )
        await db_session.commit()

        res_doc = await db_session.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
        doc = res_doc.scalar_one_or_none()
        assert doc is not None
        assert doc.title == "FK Order Ingestion Test Standard"

        res_chunks = await db_session.execute(select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id))
        chunks = res_chunks.scalars().all()
        assert len(chunks) == 2
