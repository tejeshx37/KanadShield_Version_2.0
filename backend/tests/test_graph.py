import pytest

from app.services.relationship_extraction import extract_relationships
from app.services.graph_service import extract_and_persist_relationships, get_entity_graph
from app.models.document import Document
from app.models.enums import DocumentType, Jurisdiction


def test_extract_relationships_finds_amends_and_citation():
    text = (
        "This Order amends the Gujarat Panchayats Act, 1993 in exercise of the "
        "powers conferred by section 12 of the Gujarat Panchayats Act, 1993. "
        "See also AIR 2019 SC 456 for the relevant precedent."
    )
    results = extract_relationships(text)
    types = {r.relationship_type.value for r in results}
    assert "AMENDS" in types
    assert "IMPLEMENTS" in types
    assert "CITES" in types


@pytest.mark.asyncio
async def test_persist_and_query_entity_graph(db_session):
    doc = Document(
        source="test_source",
        source_document_id="GRAPH-1",
        title="Gujarat Panchayats Amendment Order 2021",
        document_type=DocumentType.ORDER,
        jurisdiction=Jurisdiction.STATE,
        state="Gujarat",
        source_language="en",
        extracted_text="This Order amends the Gujarat Panchayats Act, 1993 substantially.",
        content_hash="y" * 64,
    )
    db_session.add(doc)
    await db_session.flush()

    relationships = await extract_and_persist_relationships(db_session, doc)
    await db_session.commit()
    assert len(relationships) >= 1

    source_entity_id = relationships[0].source_entity_id
    graph = await get_entity_graph(db_session, source_entity_id)
    assert len(graph["nodes"]) >= 2
    assert len(graph["edges"]) >= 1
    assert graph["edges"][0]["type"] == "AMENDS"
