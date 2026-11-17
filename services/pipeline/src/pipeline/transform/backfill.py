# backfill_load returns the collection of records which match certain stasion_ids and time gap
def backfill_load(raw_rows, date_start, date_end, station_ids):
    station_ids = set(station_ids)
    to_classify = [row for row in raw_rows if date_start <= row["collected_at"] < date_end and row["station_id"] in station_ids]
    return to_classify