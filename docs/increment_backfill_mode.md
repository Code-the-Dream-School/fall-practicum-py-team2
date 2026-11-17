### Pipeline Modes

The pipeline supports two loading modes:

- Backfill: Used to load historical data into the database.
  Run when you need to load data for certain period of time or for certain staions

- Incremental: Used to load only records that haven't been
  previously processed.
  Run during regular pipeline updates to avoid the data loss.