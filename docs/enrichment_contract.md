# LLM Data Enrichment Contract — Team 2 (Bike Share Analytics)

This document establishes the official interface contract for the LLM enrichment phase of our data pipeline (`KAN-23`). It outlines data targeting, added schema fields, system prompts, and deterministic error fallback procedures.

---

## 1. Target Records Selection & Invariants
To maximize efficiency and minimize unnecessary LLM token expenses, the pipeline applies strict data invariants before invoking the model:

* **Records to Enrich:** The pipeline only processes unique bike stations where the `name` column has a valid string entry, and the station has not been previously enriched.
* **Records to Skip:** 
  * Any station record where the `name` string is missing, malformed, or blank.
  * Duplicate historical logging snapshots for an identical `station_id` (the LLM operates on a unique station dim level, not on every time-series log row).

---

## 2. Enrichment Schema Extensions
The LLM phase appends three brand-new analytical fields to our Gold Layer dataset. The model must output these fields using strict types and constrained categorical values:

| Extended Column Name | Data Type | Allowed Bounds / Categorical Options | Description |
| :--- | :---: | :--- | :--- |
| **`station_zone_profile`** | `TEXT` | `transit_hub`, `commercial_district`, `residential_neighborhood`, `recreational_park` | Classifies the station's primary geographic context based on its name. |
| **`commuter_density_impact`** | `TEXT` | `high`, `moderate`, `low` | Estimates the potential peak commute hour pressure and user demand. |
| **`enrichment_summary`** | `TEXT` | Plain text string (Maximum 150 characters) | A concise, human-readable summary detailing the surrounding infrastructure. |

---

## 3. System Prompts & Storage Strategy
* **Storage Location:** The production prompt engineering logic will be stored inside our repository as a dedicated text parameter template file path: `services/pipeline/src/pipeline/enrich/prompts/station_profiler.txt`.

### Production Prompt Template Matrix:
```text
You are an expert urban logistics data assistant specializing in San Francisco micromobility patterns.
Analyze the following bike share station location name text string: "{station_name}"

Your task is to classify this location and output a clean JSON object containing exactly these keys:
{
  "station_zone_profile": "[Choose strictly from: transit_hub, commercial_district, residential_neighborhood, recreational_park]",
  "commuter_density_impact": "[Choose strictly from: high, moderate, low]",
  "enrichment_summary": "[A short sentence describing why this area fits this profile under 150 characters]"
}

Do not include any conversational preamble, formatting ticks, or markdown code blocks. Return raw valid JSON only.
```

---

## 4. Fallback Handling & Error Mitigation
If the LLM returns an unusable response, the pipeline must catch the exception deterministically to prevent the ingestion script from crashing.

* **Scenario A: Malformed JSON output** ➔ The pipeline catches the `json.JSONDecodeError` exception and injects safe defaults:
  * `station_zone_profile` = `"commercial_district"` (Global baseline mode)
  * `commuter_density_impact` = `"moderate"`
  * `enrichment_summary` = `"Fallback: Location profile generated due to malformed LLM response string."`
* **Scenario B: Empty or Missing Key attributes** ➔ The code checks for key presence; any missing key is instantly backfilled with its type-safe fallback default value.
* **Scenario C: Unauthorized Categorical Out-of-Bounds Label** ➔ If the LLM invents a non-contract category (e.g., `"tourist_spot"`), a Python verification wrapper forces the string back to the nearest contract default entry (`"recreational_park"`).
