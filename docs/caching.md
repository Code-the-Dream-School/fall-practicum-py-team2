# Lookup Caching Strategy

## What is cached and why
The pipeline caches responses for `gbfs.json`, `station_information` (static station metadata such as station names and coordinates), and `vehicle_types` (reference specifications for classic bikes and e-bikes). Because these reference feeds rarely change compared to live availability feeds (`station_status` and `free_bike_status`), caching them prevents redundant HTTP requests across repeated pipeline runs.

## Where the cache lives
The cache lives in memory using Python's `@functools.lru_cache(maxsize=32)` decorator inside `services/pipeline/src/pipeline/extract/extract.py` via the `_cached_extract(url, time_bucket)` and `cached_extract(url, max_age)` functions.

## When a cached value is refreshed or considered stale
Cached lookups use a Time-To-Live (TTL) bucket of 24 hours calculated via `int(time.time() // max_age)`. Once the 24-hour time bucket rolls over (or if `cache_clear()` is called), the cached entry is considered stale and the next lookup fetches fresh data from the GBFS endpoint.