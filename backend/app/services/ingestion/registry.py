from app.core.config import Settings
from app.services.ingestion.base import SourceConnector
from app.services.ingestion.connectors.egazette import EGazetteConnector
from app.services.ingestion.connectors.gujarat_gr import GujaratGRConnector
from app.services.ingestion.connectors.india_code import IndiaCodeConnector

_CONNECTOR_CLASSES: dict[str, type[SourceConnector]] = {
    "SOURCE_INDIA_CODE": IndiaCodeConnector,
    "SOURCE_EGAZETTE": EGazetteConnector,
    "SOURCE_GUJARAT_GR": GujaratGRConnector,
}


def get_enabled_connectors(settings: Settings) -> list[SourceConnector]:
    """New sources are added by registering one connector class here (or
    via a plugin entry point later) — never by touching pipeline code."""
    return [
        _CONNECTOR_CLASSES[name](settings)
        for name in settings.enabled_ingestion_sources
        if name in _CONNECTOR_CLASSES
    ]
