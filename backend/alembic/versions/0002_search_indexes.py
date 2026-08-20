"""search indexes: FTS tsvector + pgvector HNSW

Revision ID: 0002_search_indexes
Revises: 506b5252b57b
Create Date: 2026-08-20 02:10:00.000000
"""
from alembic import op

revision = "0002_search_indexes"
down_revision = "506b5252b57b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Generated tsvector column driven by source_language via a language-aware
    # trigger, defaulting to 'english' config and falling back per-row at
    # query time in search.py for gu/hi (see LEXICAL_SEARCH_CONFIGS).
    op.execute(
        """
        ALTER TABLE documents ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(subject, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(extracted_text, '')), 'C')
        ) STORED;
        """
    )
    op.execute("CREATE INDEX ix_documents_search_vector ON documents USING GIN (search_vector);")

    op.execute(
        """
        ALTER TABLE document_chunks ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED;
        """
    )
    op.execute("CREATE INDEX ix_document_chunks_search_vector ON document_chunks USING GIN (search_vector);")

    # HNSW ANN index for semantic search over chunk embeddings (cosine distance).
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops);"
    )

    op.execute("CREATE INDEX ix_documents_title_trgm ON documents USING GIN (title gin_trgm_ops);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_documents_title_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw;")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_search_vector;")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS search_vector;")
    op.execute("DROP INDEX IF EXISTS ix_documents_search_vector;")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS search_vector;")
