from app.config import SAMPLE_APP_PATH
from app.ingestion.chunker import chunk_repository


def test_chunk_repository_produces_expected_types():
    chunks = chunk_repository(SAMPLE_APP_PATH)
    by_type = {}
    for c in chunks:
        by_type[c.chunk_type] = by_type.get(c.chunk_type, 0) + 1

    assert by_type.get("class", 0) > 0
    assert by_type.get("method", 0) > 0
    assert by_type.get("sql_procedure", 0) == 4  # ApprovalProcedures.sql defines 4 procs
    assert by_type.get("doc_section", 0) > 0


def test_chunk_ids_are_unique():
    chunks = chunk_repository(SAMPLE_APP_PATH)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_sql_procedure_names_captured():
    chunks = chunk_repository(SAMPLE_APP_PATH)
    proc_names = {c.symbol for c in chunks if c.chunk_type == "sql_procedure"}
    assert "dbo.sp_UpdateOrderStatus" in proc_names
    assert "dbo.sp_GetOrderById" in proc_names


def test_every_chunk_has_nonempty_text():
    chunks = chunk_repository(SAMPLE_APP_PATH)
    assert len(chunks) > 0
    assert all(c.text.strip() for c in chunks)
