# Deployment & Operations Guide: LLM Enrichment Lambda (`bks-enrich-lambda`)

## Overview
- **Jira Ticket:** KAN-34 — LLM enrichment as a second Lambda
- **Function Name:** `bks-enrich-lambda`
- **AWS Region:** `us-east-2` (Ohio)
- **Runtime & Handler:** Python 3.11 (`enrich_lambda_handler.lambda_handler`)
- **Memory & Timeout:** 512 MB memory, 5-minute timeout
- **Execution Role:** `bks-enrich-lambda-role` (CloudWatch Logs + read-only SSM Parameter Store access)

## LLM Provider & Secrets (SSM Parameter Store)
- AWS Bedrock (`bedrock:InvokeModel`) is blocked by an account-level guardrail (`ValidationException: Operation not allowed`) on the Practicum AWS account.
- Per project documentation (`docs/tools_and_prior_coverage.md`), `bks-enrich-lambda` uses **Google Gemini (`gemini-3.5-flash-lite`)** via Google AI Studio's free tier (`$0` cost), while retaining optional OpenAI support if `/bks/OPENAI_API_KEY` is configured.
- All secrets are stored as `SecureString` parameters in AWS Systems Manager Parameter Store (`us-east-2`):
  - `/bks/SUPABASE_URL`
  - `/bks/SUPABASE_KEY`
  - `/bks/GEMINI_API_KEY`
  - `/bks/OPENAI_API_KEY` (optional)

## Environment Variables

| Key | Value | Purpose |
| :--- | :--- | :--- |
| `SUPABASE_URL_PARAM` | `/bks/SUPABASE_URL` | SSM parameter path for Supabase URL |
| `SUPABASE_KEY_PARAM` | `/bks/SUPABASE_KEY` | SSM parameter path for Supabase service role key |
| `GEMINI_API_KEY_PARAM` | `/bks/GEMINI_API_KEY` | SSM parameter path for Gemini API key |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Active Gemini model ID |
| `BATCH_SIZE` | `10` (default) | Stations processed per invocation to respect free-tier RPM limits |
| `GEMINI_REQUEST_DELAY_SEC` | `4.5` (default) | Pacing delay between LLM requests |

## Packaging & Deployment
Build the Linux-compatible deployment zip (`manylinux2014_x86_64`, Python 3.11) from the repository root:

```bash
rm -rf build_enrich enrich_lambda_package.zip && mkdir -p build_enrich
python3 -m pip install \
  --platform manylinux2014_x86_64 \
  --target=build_enrich \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  supabase openai python-dotenv
cp -r services/pipeline/src/pipeline build_enrich/
cp services/pipeline/enrich_lambda_handler.py build_enrich/
cd build_enrich && zip -r ../enrich_lambda_package.zip . -x "*__pycache__*" "*.DS_Store" && cd ..
```

Upload `enrich_lambda_package.zip` to `bks-enrich-lambda` in AWS Lambda (`Code` tab -> `Update` -> `.zip file`), then remove local temporary build files (`rm -rf build_enrich enrich_lambda_package.zip`).

## Manual Invocation & Idempotency
- **Test / Manual Event Payload:**
  ```json
  {
    "source": "manual",
    "batch_size": 10
  }
  ```
- **Idempotency Behavior:** Before calling the LLM, `run_enrichment` queries existing `station_id` records in `gold.station_enrichments` and processes only unenriched stations. Re-running skips already-enriched stations and automatically retries any station that previously logged an error in `logs.enrichment_errors`.
