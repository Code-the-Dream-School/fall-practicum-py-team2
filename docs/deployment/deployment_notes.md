# Deployment Notes and Runtime Configuration (KAN-33)

## 1. Overview

This document explains how our Bike Share pipeline runs in AWS, what services we use, and how we manage settings and secrets.

It also explains the difference between running the pipeline on our computers and running it in AWS.

Our team deployed the ingest Lambda and successfully tested both manual and automatic executions.

On November 23, 2026, the manual Lambda test processed 373 stations and 777 bikes in about 8.16 seconds.

On November 24, 2026, we successfully tested the automatic execution using EventBridge Scheduler. The Lambda processed 375 stations and 639 bikes in about 7.58 seconds.

We verified the AWS configuration, IAM permissions, CloudWatch logs, Scheduler metrics, and Supabase database results.

The team approved running the pipeline every 4 hours, which means 6 executions per day.

The EventBridge schedule is currently disabled after testing until the team is ready to enable it again.

The goal of this document is to help other team members understand our AWS setup, reproduce the deployment, and make changes when needed.

## 2. Cloud Architecture

Our existing Python pipeline runs on AWS Lambda instead of requiring a developer to start it manually every time.

EventBridge Scheduler allows us to run the pipeline automatically.

The data flow is:

```text
EventBridge Scheduler
        |
        v
    AWS Lambda
        |
        v
     GBFS API
        |
        v
      Extract
        |
        v
     Load Raw
        |
        v
     Transform
        |
        v
     Load Gold
        |
        v
     Supabase
        |
        v
 Streamlit Dashboard
```


The Lambda retrieves the Supabase credentials from SSM Parameter Store.

IAM controls which AWS resources Lambda and EventBridge can access.

CloudWatch stores the execution logs and helps us monitor the pipeline.

AWS Budgets helps us monitor AWS spending.

### Current Architecture Status

| Component | Status |
|---|---|
| Ingest Lambda | Deployed and tested |
| EventBridge Scheduler | Configured and tested |
| SSM Parameter Store | Configured and verified |
| IAM roles | Configured and verified |
| CloudWatch logging | Configured and verified |
| Supabase database | Data successfully loaded and verified |
| LLM enrichment Lambda | Deployment not verified |
| Streamlit cloud deployment | Deployment not verified |

A separate Lambda function is planned for LLM enrichment.

The Streamlit dashboard is planned to be deployed using Docker, Amazon ECR, and Amazon ECS with Fargate.

The deployment status of these additional components still needs to be confirmed with the team.

## 3. AWS Resources

The table below shows the AWS services used in our project and their current status.

| AWS Service | Purpose | Status |
|---|---|---|
| AWS Lambda | Runs our Python pipeline in AWS | Deployed and tested |
| EventBridge Scheduler | Runs the Lambda automatically on a schedule | Configured and tested; currently disabled |
| CloudWatch | Stores Lambda logs and helps us find errors | Logs and Scheduler metrics verified |
| IAM | Controls access to AWS resources | Execution roles and permissions verified |
| SSM Parameter Store | Stores Supabase connection information securely | Configured and verified |
| AWS Budgets | Sends alerts when AWS costs reach certain limits | Budget configuration previously verified |
| Amazon ECR | Stores Docker images for the dashboard | Deployment not verified |
| Amazon ECS | Manages dashboard containers | Deployment not verified |
| AWS Fargate | Runs dashboard containers without managing servers | Deployment not verified |

### Resource Names

| Resource | Name |
|---|---|
| AWS region | `us-east-2` (Ohio) |
| Ingest Lambda | `bks-ingest-lambda` |
| Lambda execution role | `bks-ingest-lambda-role` |
| EventBridge schedule | `bks-ingest-schedule` |
| EventBridge schedule group | `default` |
| EventBridge execution role | `bks-eventbridge-scheduler-role` |
| CloudWatch log group | `/aws/lambda/bks-ingest-lambda` |
| Supabase URL parameter | `/bks/SUPABASE_URL` |
| Supabase key parameter | `/bks/SUPABASE_KEY` |

Most of our pipeline resources are located in the `us-east-2` region.

IAM is a global AWS service, so IAM roles are not limited to one region.

We verified the deployed resources in the AWS Console on November 23 and November 24, 2026.

## 4. Lambda Runtime Configuration

Our team deployed the ingest Lambda to AWS and successfully tested manual and automatic executions.

The following settings were verified in the AWS Console.

| Setting | Configuration |
|---|---|
| Function name | `bks-ingest-lambda` |
| Python runtime | Python 3.11 |
| Memory | 512 MB |
| Timeout | 60 seconds |
| Temporary storage | 512 MB |
| Execution role | `bks-ingest-lambda-role` |
| Package type | ZIP |
| Deployment package | `lambda_package.zip` |
| Handler | `lambda_handler.lambda_handler` |
| AWS region | `us-east-2` (Ohio) |
| Architecture | `x86_64` |
| SnapStart | None |

The handler tells AWS Lambda which Python file and function to execute.

In our case, Lambda runs the `lambda_handler` function inside the `lambda_handler.py` file.

### Dependencies

Our Lambda needs these Python libraries to run the Bike Share pipeline:

- `pandas`
- `numpy`
- `requests`
- `supabase`
- `python-dotenv`
- `boto3`

The deployment package includes our Python pipeline code and the libraries it needs.

The package must be compatible with the AWS Lambda Linux environment, Python 3.11, and the `x86_64` architecture.

The `boto3` library is available in the AWS Lambda Python runtime. We should manage its version if our code needs a specific one.

### Building the Deployment Package

According to the KAN-32 deployment guide, the team used the following steps to build the Lambda deployment package.

Run these commands from the project root using a Bash environment with Python and the required ZIP tools installed.

Creating a new build directory:


```bash
mkdir -p build
```


Installing the required libraries:


```bash
pip install \
  --platform manylinux2014_x86_64 \
  --target=build \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  pandas numpy supabase requests python-dotenv
```


Copying the pipeline code and Lambda handler:

```bash
cp -r services/pipeline/src/pipeline build/
cp services/pipeline/lambda_handler.py build/
```


Creating the ZIP package:


```bash
cd build
zip -r ../lambda_package.zip . -x "*__pycache__*" "*.DS_Store"
cd ..
```


Before rebuilding the package, make sure the build directory is clean and does not contain files from an older build.

The ZIP file should contain the Lambda handler, pipeline package, and required dependencies at the correct directory level.

### Uploading the Deployment Package

1. Open the AWS Lambda Console.
2. Select the `us-east-2` region.
3. Open `bks-ingest-lambda`.
4. Go to the Code section.
5. Upload the new ZIP package.
6. Verify the runtime and handler settings.
7. Verify the environment variables and execution role.
8. Run a manual test.
9. Check CloudWatch and Supabase before enabling automatic execution.

These instructions are based on the KAN-32 deployment guide.

We have verified that the deployed package works, but I have not independently rebuilt and uploaded the package.

We should discuss code updates with the team before replacing the deployed Lambda package.

## 5. Secrets and Environment Variables

### Local Configuration

When we run the pipeline on our computers, we use a `.env` file to store the Supabase connection information.

The required variables are:


```text
SUPABASE_URL
SUPABASE_KEY
```


We use `python-dotenv` to load these values.

An example configuration without real secrets can look like this:


```text
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```


The actual `.env` file must stay private and should never be uploaded to GitHub.

### AWS Configuration

In AWS, our team uses SSM Parameter Store to keep the Supabase connection information secure.

We verified that both parameters exist in the `us-east-2` region and use the Standard tier with the `SecureString` type.

| Parameter Name | Purpose |
|---|---|
| `/bks/SUPABASE_URL` | Supabase project URL |
| `/bks/SUPABASE_KEY` | Supabase API key |

The Lambda has the following environment variables:

| Variable | Value |
|---|---|
| `SUPABASE_URL_PARAM` | `/bks/SUPABASE_URL` |
| `SUPABASE_KEY_PARAM` | `/bks/SUPABASE_KEY` |

These environment variables contain only the parameter names, not the actual secret values.

When Lambda runs, it uses `boto3` to retrieve the values from SSM Parameter Store.

### Lambda Execution Role

The Lambda uses the following execution role:

`bks-ingest-lambda-role`

We verified that the role has the following policies:

| Policy | Purpose |
|---|---|
| `AWSLambdaBasicExecutionRole` | Allows Lambda to write logs to CloudWatch |
| `bks-ingest-ssm-least-privilege` | Allows Lambda to retrieve the required SSM parameters |

The CloudWatch policy allows these actions:

```text
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
```

The SSM policy allows these actions:


```text
ssm:GetParameter
ssm:GetParameters
```


The SSM permissions are limited to the following parameter paths:


```text
arn:aws:ssm:*:*:parameter/bks/SUPABASE_URL
arn:aws:ssm:*:*:parameter/bks/SUPABASE_KEY
```

The current policy uses wildcards for the AWS region and account.

We should discuss restricting these permissions to our AWS account and the `us-east-2` region for better security.

### EventBridge Execution Role

EventBridge Scheduler uses a separate execution role:

`bks-eventbridge-scheduler-role`

We verified that this role allows the following action:


```text
lambda:InvokeFunction
```


The permission is limited to `bks-ingest-lambda`, including its versions and aliases.

We also verified the trust relationship.

| Setting | Configuration |
|---|---|
| Trusted service | `scheduler.amazonaws.com` |
| Action | `sts:AssumeRole` |
| Effect | Allow |
| Source account | Restricted to our AWS account |

This role allows EventBridge Scheduler to invoke the Lambda.

The Lambda execution role and EventBridge execution role have different purposes and should not be confused.

### Safe to Commit to GitHub

- Parameter names and paths
- Environment variable names
- Lambda configuration settings
- Documentation
- Example configuration files without real secrets

### Never Commit to GitHub

- Supabase API keys
- OpenAI API keys
- AWS access keys
- Passwords
- Secret values
- `.env` files containing credentials

We reviewed the CloudWatch execution logs during testing.

No API keys or passwords were visible in the logs we reviewed.

## 6. Local vs. Cloud Execution

Our Bike Share pipeline uses the same main functions locally and in AWS, but the way we run it is different.

| Feature | Local | AWS Cloud |
|---|---|---|
| Execution | Python scripts or Prefect | Lambda handler |
| Trigger | Manual execution | Manual test or EventBridge Scheduler |
| Credentials | `.env` file | SSM Parameter Store |
| File storage | Local filesystem | `/tmp` directory |
| Dependencies | Virtual environment | Lambda deployment package |
| Logging | Terminal | CloudWatch |
| Database | Supabase | Supabase |
| Automatic schedule | Not required | Every 4 hours when enabled |

### Local Execution

We run the pipeline locally when we are developing, testing, or fixing problems.

We install the required Python libraries in our virtual environment and use a `.env` file for the Supabase credentials.

We can run the pipeline manually and check the results in the terminal.

Local execution allows us to test changes before updating the deployed Lambda.

### Cloud Execution

In AWS, the Lambda handler runs our existing pipeline functions.

The main steps are:

1. Retrieving the Supabase credentials from SSM Parameter Store.
2. Preparing the temporary working directory.
3. Extracting Bike Share data from the GBFS API.
4. Loading raw data into Supabase.
5. Transforming the raw data.
6. Saving the transformed data to the Gold table.
7. Updating the pipeline run history.
8. Recording the execution results in CloudWatch.

We successfully verified both manual and automatic cloud executions.

### Manual Lambda Input


```json
{
    "source": "manual"
}
```


### EventBridge Lambda Input


```json
{
    "source": "eventbridge"
}
```


The Lambda handler records the input source in CloudWatch.

This helps us identify whether a run was started manually or by EventBridge.

### Temporary JSON Files

The extraction function creates two JSON files:

- `station_information.json`
- `bike_information.json`

These files are used to load the raw data into Supabase.

In AWS Lambda, the deployment directory is read-only, so the pipeline uses the `/tmp` directory for temporary files.

Both the extraction and loading functions need to use the correct file paths.

Files in `/tmp` are temporary and should not be used for permanent storage.

The successful manual and automatic tests show that the temporary file handling worked during those executions.

We should continue monitoring this during repeated scheduled executions.

## 7. Monitoring and Cost Control

### CloudWatch Monitoring

We use CloudWatch to check Lambda logs and find errors.

The logs help us check:

- When the pipeline starts and finishes
- Whether the execution succeeds or fails
- How many records are processed
- Errors during the pipeline
- Execution time
- Memory usage
- The source of the execution

The verified log group for our ingest Lambda is:


```text
/aws/lambda/bks-ingest-lambda
```


### How to Check the Logs

1. Open CloudWatch in the `us-east-2` region.
2. Go to Logs, then Log groups or Log Management.
3. Open `/aws/lambda/bks-ingest-lambda`.
4. Select a recent log stream.
5. Review the execution messages and results.
6. Check the RequestId, duration, memory usage, and errors.

We verified successful manual and automatic execution logs.

We also reviewed an earlier failed execution.

The CloudWatch log group currently has a retention setting of Never expire.

We should discuss a reasonable retention period with the team to avoid storing unnecessary logs.

CloudWatch alarms are covered separately in KAN-35.

### EventBridge Scheduling

We use Amazon EventBridge Scheduler to run the ingest Lambda automatically.

The team approved running the pipeline every 4 hours.

| Setting | Configuration |
|---|---|
| Schedule name | `bks-ingest-schedule` |
| Schedule group | `default` |
| Schedule expression | `rate(4 hours)` |
| Executions per day | 6 |
| Target | `bks-ingest-lambda` |
| Flexible time window | Off |
| Time zone | America/New_York |
| Retry policy | Not configured |
| Dead-letter queue | Not configured |
| Execution role | `bks-eventbridge-scheduler-role` |
| Current status | Disabled after testing |

The target input is:


```json
{
    "source": "eventbridge"
}
```


We successfully tested the automatic execution on November 24, 2026.

After completing the test, we disabled the schedule to avoid unnecessary executions until the team is ready.

### Scheduler Metrics

We also verified the EventBridge Scheduler metrics in CloudWatch.

To check these metrics:

1. Open CloudWatch.
2. Expand Metrics.
3. Select Classic metrics.
4. Search for Scheduler.
5. Open Scheduler > Schedule Group Metrics.
6. Select the `default` schedule group.
7. Select `InvocationAttemptCount`.
8. Choose the time range for the execution.

During our automatic test, CloudWatch recorded one invocation attempt.

The timestamp was consistent with the Lambda execution time.

The `TargetErrorCount` metric was not visible during our review, so we could not verify an explicit zero value.

We used the Scheduler metrics, Lambda logs, and Supabase results together to confirm the automatic execution.

More details about scheduling, monitoring, and pausing the schedule are covered in KAN-36.

### Cost Control

To help keep AWS costs low, we should:

- Avoid running the pipeline more often than needed.
- Check Lambda execution time and memory usage.
- Set a reasonable CloudWatch log retention period.
- Disable schedules and resources when they are not needed.
- Monitor ECS and Fargate costs before running containers continuously.
- Check AWS spending regularly.
- Discuss new AWS resources with the team before creating them.

### Estimated Lambda Usage

Running the pipeline every 4 hours means approximately 180 executions in a 30-day month.

Our automatic test had the following results:

| Metric | Value |
|---|---|
| Configured memory | 512 MB |
| Execution duration | 7.58 seconds |
| Billed duration | 11.23 seconds |
| Estimated monthly executions | 180 |
| Estimated monthly compute usage | About 1,010 GB-seconds |

The estimated monthly compute usage is calculated using:


```text
180 executions x 0.5 GB x 11.227 seconds

= 1,010.43 GB-seconds
```


The expected Lambda compute cost is low and may be covered by the AWS free tier if enough free usage is available.

This is only an estimate based on one automatic execution.

Actual costs may change depending on the amount of data, execution time, requests, CloudWatch logs, data transfer, and other AWS usage.

### AWS Budget Configuration

I checked the following budget settings in the AWS Console on November 19, 2026.

| Setting | Configuration |
|---|---|
| Budget name | My Monthly Cost Budget |
| Monthly budget | $100 |
| Actual cost alert | 85% ($85) |
| Actual cost alert | 100% ($100) |
| Forecasted cost alert | 100% ($100) |
| Email verification | 0 of 6 verified |
| Budget actions | None shown |

The team later reported additional budget notifications at 20%, 50%, and 80%.

These newer settings still need to be checked in the AWS Console.

We should also confirm that the budget notification email addresses are verified.

AWS budget alerts help us monitor spending, but they do not automatically stop AWS charges.

## 8. Deployment Verification

Our team deployed the ingest Lambda and successfully tested manual and automatic executions.

We verified the results using the AWS Console, CloudWatch, EventBridge Scheduler metrics, and Supabase.

### Manual Execution

To test the Lambda manually:

1. Open AWS Lambda in the AWS Console.
2. Select `bks-ingest-lambda` in the `us-east-2` region.
3. Create a test event with the following JSON:


```json
{
    "source": "manual"
}
```


4. Run the test.
5. Check the execution result.
6. Open CloudWatch to review the logs.
7. Check Supabase to confirm that the data was saved successfully.

### Verified Manual Test Results

The manual test was completed by the team on November 23, 2026.

I reviewed the actual CloudWatch logs and Supabase results to confirm the reported deployment results.

| Check | Result |
|---|---|
| Lambda function | `bks-ingest-lambda` |
| AWS region | `us-east-2` |
| Test type | Manual |
| Execution status | Successful |
| Execution time | 8.16 seconds |
| Billed duration | 11.81 seconds |
| Stations processed | 373 |
| Bikes processed | 777 |
| Total raw records loaded | 1,150 |
| Gold rows upserted | 7,015 |
| Configured memory | 512 MB |
| Maximum memory used | 250 MB |
| Source in CloudWatch | manual |

The manual test was successful, and the pipeline saved the data to Supabase.

### Automatic Execution

On November 24, 2026, we tested the automatic execution using EventBridge Scheduler.

Before enabling the schedule, we checked the existing data in Supabase.

We then enabled the schedule and waited for EventBridge to trigger the Lambda.

We did not manually invoke the Lambda during this test.

The Lambda successfully completed the automatic execution.

### Verified Automatic Test Results

| Check | Result |
|---|---|
| Lambda function | `bks-ingest-lambda` |
| Test date | November 24, 2026 |
| Test type | Automatic |
| Trigger | EventBridge Scheduler |
| Execution status | Successful |
| Execution time | 7.58 seconds |
| Billed duration | 11.23 seconds |
| Stations processed | 375 |
| Bikes processed | 639 |
| Total raw records loaded | 1,014 |
| Gold rows upserted | 7,390 |
| Configured memory | 512 MB |
| Maximum memory used | 253 MB |
| Source in CloudWatch | eventbridge |
| Scheduler invocation attempts | 1 in the default schedule group |

### Automatic Execution Timeline

The following times are in UTC on November 24, 2026.

| Time | Event |
|---|---|
| 22:00:34 | EventBridge schedule enabled |
| 22:01:16 | Lambda initialization started |
| 22:01:20 | Lambda execution started |
| 22:01:23 | Raw data loaded |
| 22:01:27 | Gold data saved and pipeline completed |
| After execution | Supabase results verified |
| After database verification | Scheduler metrics verified |
| After testing | EventBridge schedule disabled |

### Manual vs. Automatic Results

| Metric | Manual | Automatic |
|---|---:|---:|
| Stations extracted | 373 | 375 |
| Bikes extracted | 777 | 639 |
| Total extracted | 1,150 | 1,014 |
| Total loaded | 1,150 | 1,014 |
| Gold rows upserted | 7,015 | 7,390 |
| Execution duration | 8.16 seconds | 7.58 seconds |
| Billed duration | 11.81 seconds | 11.23 seconds |
| Maximum memory used | 250 MB | 253 MB |
| Status | Success | Success |

Both executions completed successfully using the same Lambda function.

The number of stations and bikes can change because the Bike Share data changes throughout the day.

The Gold rows upserted include existing records that may have been updated.

### Database Verification

We can check the latest pipeline runs in the Supabase SQL Editor:


```sql
SELECT
    run_id,
    status,
    extracted,
    loaded,
    transformed,
    message,
    started_at,
    ended_at
FROM logs.pipeline_runs
ORDER BY started_at DESC
LIMIT 5;
```


We can also check the Gold table:


```sql
SELECT
    COUNT(*) AS total_rows,
    MAX(collected_at) AS latest_run
FROM gold.enriched_bks;
```


Both queries are read-only and do not change the database.

The total row count may not increase every time because the pipeline uses upserts to insert or update records.

The `collected_at` value represents the data collection timestamp, so it may be different from the Lambda execution start time.

### Supabase Results Before and After Automatic Testing

| Metric | Before | After |
|---|---|---|
| Total Gold records | 7,015 | 7,390 |
| Latest collection timestamp | 2026-11-23 18:38:45 | 2026-11-24 22:01:23 |
| Pipeline run records | 3 | 4 |
| Successful pipeline runs | 3 | 4 |

The total number of records in the Gold table increased by 375.

We also verified that the new pipeline run in Supabase matched the CloudWatch execution results.

### Automatic Pipeline Run Details

| Field | Result |
|---|---|
| Run ID | `9045e216-efec-41a8-9c8b-db67594b3662` |
| Lambda RequestId | `be6b0609-021e-469b-8a7e-297b76d711b2` |
| Status | success |
| Extracted | 1,014 |
| Loaded | 1,014 |
| Transformed | 7,390 |

The matching Run ID and record counts confirmed that the automatic Lambda execution successfully updated Supabase.

### Failed Execution Verification

During our CloudWatch review, we found an earlier failed execution from November 23, 2026.

The error message was:


```text
Runtime.ImportModuleError:
Unable to import module 'lambda_function':
No module named 'lambda_function'
```


This error means that Lambda could not find the configured Python module.

The current Lambda handler is:


```text
lambda_handler.lambda_handler
```


The later successful executions confirmed that the import problem was no longer blocking the pipeline.

We did not intentionally create another failure because we are using shared AWS resources.

We also learned that an initialization error can happen before the pipeline writes a record to Supabase.

This is why we need CloudWatch logs in addition to the database run history.

### Deployment Checklist

- [x] Lambda runtime configuration verified.
- [x] Lambda execution role verified.
- [x] SSM Parameter Store configuration verified.
- [x] Lambda environment variables verified.
- [x] Lambda executes successfully during a manual test.
- [x] GBFS data is extracted.
- [x] Raw data is saved to Supabase.
- [x] Transformed data is saved to the Gold table.
- [x] Successful CloudWatch logs reviewed.
- [x] Earlier failed CloudWatch logs reviewed.
- [x] EventBridge schedule configured.
- [x] EventBridge execution permissions verified.
- [x] EventBridge trust relationship verified.
- [x] EventBridge triggers the Lambda automatically.
- [x] Scheduler invocation metrics verified.
- [x] Supabase pipeline run history verified.
- [x] Gold table updates verified.
- [x] No API keys or passwords visible in the reviewed logs.
- [x] EventBridge schedule disabled after testing.
- [ ] Deployment package independently rebuilt and tested.
- [ ] Duplicate records checked separately after repeated executions.
- [ ] Multiple scheduled executions verified over a longer period.
- [ ] Latest AWS budget notification settings verified.

### Related Deployment Guides

For more details about deploying the Lambda, see the KAN-32 guide:

[Ingest Lambda Deployment Guide](ingest_lambda.md)

For more details about automatic scheduling and CloudWatch monitoring, see the KAN-36 guide:

[EventBridge Scheduling and CloudWatch Monitoring](eventbridge_schedule.md)

These documents are maintained in separate tasks and will be available together after the related pull requests are merged.

## 9. Known Issues and Open Questions

### Known Issues

Our team has successfully deployed and tested the ingest Lambda, but we still have a few things to review.

- The final merge status of the KAN-31 Lambda handler and KAN-32 deployment documentation needs to be confirmed.
- The deployment package works, but we should confirm that other team members can rebuild it using the deployment guide.
- The Lambda uses `/tmp` for temporary JSON files. Both tested executions worked, but we should continue monitoring repeated executions.
- CloudWatch currently keeps logs without an expiration date.
- The SSM permission policy uses wildcards for the AWS region and account.
- EventBridge does not have a configured retry policy or dead-letter queue.
- Lambda asynchronous invocation retries may still apply separately from Scheduler retry settings.
- We have verified one automatic execution, but repeated scheduled executions still need to be monitored.
- We have not completed a separate duplicate-record verification test.
- The latest AWS budget notification settings still need to be verified.
- The architecture diagram may need an update to show the AWS resources that have been deployed.

### Resolved Issues

| Previous Issue | Current Status |
|---|---|
| Lambda import error | Current handler works successfully |
| EventBridge schedule not configured | Configured and tested |
| Schedule frequency not decided | Team approved every 4 hours |
| CloudWatch logs not reviewed | Successful and failed logs reviewed |
| Automatic execution not verified | Successfully tested |
| Supabase automatic updates not verified | Successfully verified |
| Scheduler execution permissions not verified | Permissions and trust relationship verified |

### Open Questions

- What should the CloudWatch log retention period be?
- Who will manage the SSM parameters and IAM permissions?
- Should we restrict the SSM policy to our AWS account and region?
- Should we configure EventBridge retries and a dead-letter queue?
- When should we enable the EventBridge schedule for regular use?
- How will the separate LLM enrichment Lambda be triggered?
- Will the dashboard run continuously on ECS Fargate, and how much will it cost?
- Will the machine learning component stay separate from the cloud pipeline?
- Have the related deployment pull requests been merged?
- Are the latest AWS budget notifications configured and verified?

### Previous AWS Verification

I checked the AWS Console on November 19 and November 20, 2026.

At that time, the following results were recorded:

| AWS Resource | November 19–20 Results |
|---|---|
| AWS account access | Confirmed |
| AWS Budgets | $100 monthly budget configured |
| Budget notifications | 0 of 6 email addresses verified |
| Ingest Lambda | Not found in `us-east-2` |
| SSM Parameter Store | No parameters visible in `us-east-2` |
| Ingest Lambda IAM role | Not found |
| CloudWatch | No log groups in `us-east-2` |
| Amazon ECS | No clusters in `us-east-2` |
| EventBridge Scheduler | No schedules found in `us-east-2` |

These were the results at the time of my checks.

No AWS resources were created or changed during those initial checks.

### Latest AWS Verification

We completed additional AWS and Supabase verification on November 23 and November 24, 2026.

| AWS Resource | Latest Verified Status |
|---|---|
| Ingest Lambda | Deployed and successfully tested |
| AWS region | `us-east-2` |
| Lambda execution role | Configured and verified |
| SSM Parameter Store | Both required parameters verified |
| Lambda environment variables | Configured and verified |
| Supabase | Raw and Gold data successfully loaded |
| EventBridge Scheduler | Configured and successfully tested |
| EventBridge execution role | Permissions and trust relationship verified |
| CloudWatch | Successful and failed execution logs reviewed |
| Scheduler metrics | One invocation attempt verified |
| EventBridge schedule status | Disabled after testing |
| ECS and Fargate | Latest dashboard deployment not verified |

### Final Deployment Status

The ingest Lambda and EventBridge Scheduler have been successfully configured and tested.

We verified both manual and automatic executions.

The automatic execution processed 375 stations and 639 bikes in about 7.58 seconds.

The total number of records in the Supabase Gold table increased from 7,015 to 7,390.

We confirmed the automatic execution using EventBridge Scheduler metrics, Lambda execution logs, and Supabase database results.

The EventBridge schedule is currently disabled until the team is ready to enable it again.

The initial ingest pipeline deployment and automatic execution verification are complete.

We should continue monitoring AWS costs, security settings, and pipeline performance as the project moves forward.
