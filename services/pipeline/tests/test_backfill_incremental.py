from services.pipeline.src.pipeline.transform.increment import increment_load
from unittest.mock import MagicMock, patch

def test_incremental():
    raw_records = [
    {"station_id": "101", "collected_at": "08:00", "bikes": 5},
    {"station_id": "101", "collected_at": "08:05", "bikes": 7},
    {"station_id": "102", "collected_at": "08:00", "bikes": 3},
]
    expected_records = [
    {"station_id": "101", "collected_at": "08:05", "bikes": 7},
    {"station_id": "102", "collected_at": "08:00", "bikes": 3},
]
    
    enriched_records = [
    {"station_id": "101", "collected_at": "08:00", "bikes": 5},
]
    
    fake_supabase = MagicMock()
    fake_supabase.schema.return_value.table.return_value.select.return_value.execute.return_value.data = enriched_records
    result = increment_load(fake_supabase, raw_records)
    assert len(result) == 2
    assert result == expected_records

def test_incremental_after_backfill():
    backfilled_records = [
        {"station_id": "101", "collected_at": "08:00", "bikes": 5},
        {"station_id": "101", "collected_at": "08:05", "bikes": 7},
        {"station_id": "102", "collected_at": "08:00", "bikes": 3},
    ]

    fake_supabase = MagicMock()
    fake_supabase.schema.return_value.table.return_value.select.return_value.execute.return_value.data = backfilled_records

    result = increment_load(fake_supabase, backfilled_records)

    assert result == []

    # Aservices/pipeline/tests/test_backfill_incremental.py::test_incremental PASSED                                                                                                    [ 50%]
    # services/pipeline/tests/test_backfill_incremental.py::test_incremental_after_backfill PASSED                                                                                                       [100%]
