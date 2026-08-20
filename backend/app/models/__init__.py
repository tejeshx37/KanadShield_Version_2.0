"""Import every model module so Alembic autogenerate and Base.metadata see
the full schema."""
from app.models.document import (  # noqa: F401
    Act,
    Circular,
    Document,
    DocumentChunk,
    DocumentTranslation,
    DocumentVersion,
    GR,
    Gazette,
    Judgment,
    Notification,
    Scheme,
    Section,
)
from app.models.ingestion import (  # noqa: F401
    ChangeRadarReport,
    IngestionDeadLetter,
    IngestionRun,
)
from app.models.organizations import Court, Department, Judge, Ministry  # noqa: F401
from app.models.relationships import Citation, LegalEntity, LegalRelationship  # noqa: F401
from app.models.users import (  # noqa: F401
    Alert,
    Annotation,
    AuditLog,
    Bookmark,
    CitizenProfile,
    Collection,
    CollectionItem,
    DocumentView,
    RefreshToken,
    SavedSearch,
    SearchHistory,
    User,
)
