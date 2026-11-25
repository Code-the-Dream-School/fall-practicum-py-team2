import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import boto3
from supabase import create_client

import pipeline.enrich.llm_enrichment as llm_mod

log = logging.getLogger()
log.setLevel(logging.INFO)


def load_secrets():
    ssm = boto3.client("ssm")
    for env_key, param_env in (
        ("SUPABASE_URL", "SUPABASE_URL_PARAM"),
        ("SUPABASE_KEY", "SUPABASE_KEY_PARAM"),
    ):
        if not os.environ.get(env_key):
            resp = ssm.get_parameter(Name=os.environ[param_env], WithDecryption=True)
            os.environ[env_key] = resp["Parameter"]["Value"].strip()

    for env_key, param_env in (
        ("OPENAI_API_KEY", "OPENAI_API_KEY_PARAM"),
        ("GEMINI_API_KEY", "GEMINI_API_KEY_PARAM"),
    ):
        param_name = os.environ.get(param_env)
        if param_name and not os.environ.get(env_key):
            try:
                resp = ssm.get_parameter(Name=param_name, WithDecryption=True)
                os.environ[env_key] = resp["Parameter"]["Value"].strip()
            except ssm.exceptions.ParameterNotFound:
                log.info("Optional SSM parameter %s not found.", param_name)


def call_gemini(prompt: str) -> str:
    api_key = os.environ["GEMINI_API_KEY"].strip()
    model = (os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite").strip()
    if model.startswith("models/"):
        model = model[len("models/"):]
    delay_sec = float(os.environ.get("GEMINI_REQUEST_DELAY_SEC") or "4.5")
    host = ".".join(["generativelanguage", "googleapis", "com"])
    path = "/v1beta/models/" + model + ":generateContent"
    url = urllib.parse.urlunsplit(("https", host, path, urllib.parse.urlencode({"key": api_key}), ""))
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json", "thinkingConfig": {"thinkingBudget": 0}},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini HTTP {err.code} on {path}: {detail}") from err
    if delay_sec > 0:
        time.sleep(delay_sec)
    return data["candidates"][0]["content"]["parts"][0]["text"]




def lambda_handler(event, context):
    load_secrets()
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    event = event or {}

    batch_size = int(event.get("batch_size") or os.environ.get("BATCH_SIZE", "10"))
    orig_get_pending = llm_mod.get_pending_stations
    counts = {"pending_before_run": 0}

    def batched_get_pending(stations, enriched_ids):
        pending = orig_get_pending(stations, enriched_ids)
        counts["pending_before_run"] = len(pending)
        return pending[:batch_size] if batch_size > 0 else pending

    llm_mod.get_pending_stations = batched_get_pending
    try:
        if os.environ.get("OPENAI_API_KEY"):
            results = llm_mod.run_openai_enrichment(supabase)
            provider = "openai"
        elif os.environ.get("GEMINI_API_KEY"):
            results = llm_mod.run_enrichment(supabase, call_gemini, "station_enrichments")
            provider = "gemini"
        else:
            raise RuntimeError("Neither OPENAI_API_KEY nor GEMINI_API_KEY is configured.")
    finally:
        llm_mod.get_pending_stations = orig_get_pending

    summary = {
        "status": "ok",
        "source": event.get("source", "manual"),
        "provider": provider,
        "pending_before_run": counts["pending_before_run"],
        "enriched_count": len(results.get("enriched", {})),
        "error_count": len(results.get("errors", {})),
    }
    log.info(json.dumps(summary))
    return summary
