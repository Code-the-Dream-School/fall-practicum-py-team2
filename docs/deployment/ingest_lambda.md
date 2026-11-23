# Ingest Lambda Deployment Guide (KAN-32)

Steps to package, deploy, and verify the Bay Area Bike Share **Ingest Lambda** on AWS.

---

## 1. Store Secrets in AWS SSM Parameter Store
1. Open **AWS Systems Manager → Parameter Store → Create parameter** (in your deployment region, e.g., `us-east-2`).
2. Create two **`SecureString`** parameters (paste raw values without quotes):
   * **`/bks/SUPABASE_URL`** — Supabase project URL
   * **`/bks/SUPABASE_KEY`** — Supabase API key

---

## 2. Set Up Least-Privilege IAM Role
1. In the AWS Console, go to **IAM → Roles → Create role**.
2. Choose **AWS service** → **Lambda**, then click **Next**.
3. Attach **`AWSLambdaBasicExecutionRole`** (allows writing logs to CloudWatch).
4. Name the role **`bks-ingest-lambda-role`** and click **Create role**.
5. Open **`bks-ingest-lambda-role`**, click **Add permissions → Create inline policy → JSON**, and scope SSM access strictly to the two parameters:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ssm:GetParameter",
           "ssm:GetParameters"
         ],
         "Resource": [
           "arn:aws:ssm:*:*:parameter/bks/SUPABASE_URL",
           "arn:aws:ssm:*:*:parameter/bks/SUPABASE_KEY"
         ]
       }
     ]
   }
   ```
6. Name the inline policy **`bks-ingest-ssm-least-privilege`** and click **Create policy**.

---

## 3. Build the Deployment Package (`.zip`)
From the repository root, bundle `lambda_handler.py`, `services/pipeline/src/pipeline`, and Linux `x86_64` `Python 3.11` dependencies:

```bash
rm -rf build lambda_package.zip && mkdir -p build

pip install \
  --platform manylinux2014_x86_64 \
  --target=build \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  pandas numpy supabase requests python-dotenv

cp -r services/pipeline/src/pipeline build/
cp services/pipeline/lambda_handler.py build/

cd build && zip -r ../lambda_package.zip . -x "*__pycache__*" "*.DS_Store" && cd ..
```

---

## 4. Create & Deploy the Lambda Function
1. Go to **AWS Lambda → Create function → Author from scratch**.
2. Set **Function name** to **`bks-ingest-lambda`**, **Runtime** to **`Python 3.11`**, **Architecture** to **`x86_64`**, and **Execution role** to **`bks-ingest-lambda-role`**, then click **Create function**.
3. Under **Code source**, click **Update → .zip file** and upload **`lambda_package.zip`**.
4. Under **Runtime settings → Edit**, set **Runtime** to **`Python 3.11`** and **Handler** to **`lambda_handler.lambda_handler`**, then click **Save**.
5. Under **Configuration → General configuration → Edit**, set **Memory** to **`512 MB`** and **Timeout** to **`1 min 0 sec`**, then click **Save**.
6. Under **Configuration → Environment variables → Edit**, add the SSM parameter path names (do **not** store raw secrets here):
   * `SUPABASE_URL_PARAM` = `/bks/SUPABASE_URL`
   * `SUPABASE_KEY_PARAM` = `/bks/SUPABASE_KEY`

---

## 5. Invoke by Hand & Verify Database Writes

### Step A: Run Manual Test in AWS
1. Open the **Test** tab in `bks-ingest-lambda`.
2. Enter `{"source": "manual"}` in the Event JSON box and click **Test**.
3. Confirm the execution banner shows **Succeeded** (`"status": "ok"`).

### Step B: Confirm Database Writes in Supabase
Run these queries in the **Supabase SQL Editor** to confirm the pipeline run logged cleanly and populated the Gold layer:

```sql
SELECT run_id, status, extracted, loaded, transformed, message, ended_at
FROM logs.pipeline_runs
ORDER BY started_at DESC
LIMIT 5;

SELECT COUNT(*) AS total_rows, MAX(collected_at) AS latest_run
FROM gold.enriched_bks;
```
---

### Verified Test Result
* **Manual Test Run:** Invoked `bks-ingest-lambda` with `{"source": "manual"}` in `us-east-2` (`Python 3.11`, `512 MB` memory).
* **Outcome:** Succeeded in `~8.16s` (`status: "ok"`), extracting and loading `373` stations and `777` bikes into `raw` and `gold.enriched_bks` (`latest_run` verified in Supabase).

