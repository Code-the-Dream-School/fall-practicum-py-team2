# Ingest Lambda Deployment Guide (KAN-32)

Steps to deploy the Bay Area Bike Share **Ingest Lambda** to AWS and verify that it writes data to Supabase.

---

## 1. Set Up Least-Privilege IAM Role
1. In the AWS Console, go to **IAM → Roles → Create role**.
2. Choose **AWS service** → **Lambda**, then click **Next**.
3. Attach only **`AWSLambdaBasicExecutionRole`** (allows writing logs to CloudWatch) and **`AmazonSSMReadOnlyAccess`** (if reading secrets from SSM).
4. Name the role **`bks-ingest-lambda-role`** and click **Create role**.

---

## 2. Create & Deploy the Lambda Function
1. Go to **AWS Lambda → Create function → Author from scratch**.
2. Set **Function name** to `bks-ingest-lambda`, **Runtime** to `Python 3.11`, and **Execution role** to **`bks-ingest-lambda-role`**.
3. Click **Create function**.
4. Under **Code source**, click **Upload from → .zip file** and upload the deployment zip built from **KAN-31**.
5. Under **Runtime settings → Edit**, set **Handler** to match the KAN-31 handler (e.g., `lambda_handler.lambda_handler`).
6. Under **Configuration → General configuration → Edit**, set **Memory** to `512 MB` and **Timeout** to `1 min 0 sec`.
7. Under **Configuration → Environment variables**, add `SUPABASE_URL` and `SUPABASE_KEY`.

---

## 3. Invoke by Hand & Verify Database Writes

### Step A: Run Manual Test in AWS
1. Open the **Test** tab in `bks-ingest-lambda`.
2. Create a test event with `{}` and click **Test**.
3. Confirm the execution status shows **Succeeded** (green) with no errors in CloudWatch logs.

### Step B: Confirm Database Writes in Supabase
Run this query in the **Supabase SQL Editor** to confirm new rows were added:

```sql
SELECT COUNT(*) AS total_rows, MAX(collected_at) AS latest_run
FROM gold.enriched_bks;
```

Confirm that `latest_run` matches the timestamp of your manual Lambda test.
