import boto3 
import dotenv
import os
import time

from src.pipeline.extract.extract import run_extract
from src.pipeline.load.load_raw import load_raw
from src.pipeline.transform.transform_gold import transform_and_load_to_gold
from src.pipeline.enrich.llm_enrichment import run_openai_enrichment

log = logging.getLogger()

def get_aws():
    s3 = boto3.resource('s3')
def lambda_handler():
    log_run = {}
    try:
        log_run['started_at'] = time.time()
        run_extract()
        load_raw()
        transform_and_load_to_gold()
        run_openai_enrichment()
        log_run['ended_at'] = time.time()
    except:
        raise
        log.exception("Pipeline failed during %s", current_stage)
        log.info(json.dumps(result))
        raise
        log.info(json.dumps(result))

s3.meta.events.register(bike-data, lambda_handler)