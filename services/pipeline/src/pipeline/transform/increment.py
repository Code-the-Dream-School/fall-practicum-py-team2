
# increment_load function determines what part of data was not processed yet. It returns the collection of records which must be processed.
def increment_load(supabase, raw_rows):
    enriched_response = supabase.table("enriched_bks").select("station_id", "collected_at").execute()
    already_done = {(row["station_id"], row["collected_at"]) for row in enriched_response.data}

    to_classify = [row for row in raw_rows if (row["station_id"], row["collected_at"]) not in already_done]
    print(f"Records to classify: {len(to_classify)} (skipping {len(already_done)} already enriched)")
    return to_classify

