import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3
from supabase import create_client

from pipeline.extract.extract import run_extract
from pipeline.load.load_raw import load_raw
from pipeline.transform.transform_gold import transform_and_load_to_gold
from pipeline.enrichment.llm_enrichment import run_enrichment

log = logging.getLogger()
log.setLevel(logging.INFO)

# /tmp is the only folder Lambda can write to
OUTPUT_DIR = "/tmp"


def load_secrets():
    # Already set when testing locally, so there is no need to call AWS
    if os.environ.get("SUPABASE_KEY"):
        return

    ssm = boto3.client("ssm")
    for name, param in (
        ("SUPABASE_URL", "SUPABASE_URL_PARAM"),
        ("SUPABASE_KEY", "SUPABASE_KEY_PARAM"),
    ):
        response = ssm.get_parameter(Name=os.environ[param], WithDecryption=True)
        os.environ[name] = response["Parameter"]["Value"]


def save_run(logs_db, run):
    # A logging problem should never crash or hide the real pipeline result
    try:
        logs_db.table("pipeline_runs").upsert(run).execute()
    except Exception:
        log.exception("Could not write run %s to logs.pipeline_runs", run["run_id"])


def lambda_handler(event, context):
    # Summary written to CloudWatch
    result = {
        "status": "running",
        "source": (event or {}).get("source", "manual"),
        "stages": {},
    }

    # Row written to logs.pipeline_runs
    run = {
        "run_id": str(uuid.uuid4()),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ended_at": None,
        "records_processed": 0,
        "status": "running",
        "message": "Pipeline started",
    }
    result["run_id"] = run["run_id"]

    logs_db = None
    stage = "secrets"

    try:
        # Connect to Supabase
        load_secrets()
        supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        raw_db = supabase.schema("raw")
        logs_db = supabase.schema("logs")
        save_run(logs_db, run)

        # Extract: save the JSON files to /tmp
        stage = "extract"
        station_count, bike_count = run_extract()
        result["stages"]["extract"] = {"stations": station_count, "bikes": bike_count}

        # Load: upsert the JSON files into the raw schema
        stage = "load_raw"
        stations = load_raw(raw_db, "/tmp/station_information.json", "stations_raw")
        bikes = load_raw(raw_db, "/tmp/bike_information.json", "bike_information", "bike_id")
        run["records_processed"] = stations + bikes
        result["stages"]["load_raw"] = {"stations": stations, "bikes": bikes}

        # Transform: build the gold table
        stage = "transform"
        gold = transform_and_load_to_gold()
        result["stages"]["transform"] = {"rows": len(gold)}

        run["status"] = "success"
        run["message"] = f"Loaded {stations} stations and {bikes} bikes; {len(gold)} gold rows"
        result["status"] = "ok"
        
        return result
    except Exception as error:
        run["status"] = "failed"
        run["message"] = f"Failed during {stage}: {error}"[:500]
        result.update(status="failed", failed_stage=stage, error=str(error))
        log.exception("Pipeline failed during %s", stage)
        raise

    finally:
        run["ended_at"] = datetime.now(timezone.utc).isoformat()
        if logs_db is not None:
            save_run(logs_db, run)
        log.info(json.dumps(result))