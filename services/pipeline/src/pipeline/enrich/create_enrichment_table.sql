

-- Creating a table for station-level LLM enrichment.
CREATE TABLE IF NOT EXISTS gold.station_enrichments (
    station_id TEXT PRIMARY KEY,
    station_zone_profile TEXT NOT NULL,
    commuter_density_impact TEXT NOT NULL,
    enrichment_summary TEXT NOT NULL,
    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    enriched_at TIMESTAMPTZ DEFAULT NOW()
);



-- Creating a table for recording LLM enrichment failures.
CREATE TABLE IF NOT EXISTS logs.enrichment_errors (
    error_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_id TEXT NOT NULL,
    error_message TEXT NOT NULL,
    failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
