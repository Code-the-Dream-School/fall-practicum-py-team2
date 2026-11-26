# KAN-36 — EventBridge Scheduling and CloudWatch Monitoring

## 1. Overview

The goal of KAN-36 is to run our Bike Share data pipeline automatically using AWS EventBridge Scheduler.

Instead of starting the Lambda manually every time, EventBridge starts it on a schedule. CloudWatch helps us check if the Lambda runs successfully or if something goes wrong.

The workflow is:

EventBridge Scheduler → AWS Lambda → Bike Share API → Supabase Database

Our team deployed the ingest Lambda, `bks-ingest-lambda`, in the `us-east-2` region.

After discussing the schedule with the team, we agreed to run the pipeline every 4 hours, which means 6 executions per day.

On November 23, 2026, the manual Lambda test successfully processed 373 stations and 777 bikes in about 8.16 seconds.

On November 24, 2026, we successfully tested the automatic execution using EventBridge. The Lambda processed 375 stations and 639 bikes in about 7.58 seconds.

We also verified the CloudWatch logs, Scheduler metrics, and Supabase database results. The total number of records in the Gold table increased from 7,015 to 7,390.

This document explains:

- How to configure the EventBridge schedule.
- How often the Lambda runs and why.
- The difference between manual and scheduled runs.
- How to check CloudWatch logs.
- How to identify successful and failed runs.
- How to enable, pause, or delete the schedule.
- How to check that Supabase receives data automatically.

**Current status:** The Lambda and EventBridge schedule have been configured and successfully tested. The schedule was disabled after testing until the team is ready to enable it again.

## 2. EventBridge Schedule

We configured EventBridge Scheduler to run our Bike Share ingest Lambda every 4 hours after getting team approval.

### Why Every 4 Hours?

- It updates our Bike Share data six times per day.
- It allows us to collect data regularly without manual work.
- It gives us more data throughout the day for analysis.
- It helps us avoid unnecessary Lambda executions.
- It helps us keep AWS costs low.

### Schedule Configuration

| Setting | Configuration |
|---|---|
| AWS service | Amazon EventBridge Scheduler |
| Schedule name | `bks-ingest-schedule` |
| Schedule group | `default` |
| AWS region | `us-east-2` (Ohio) |
| Target | AWS Lambda |
| Lambda function | `bks-ingest-lambda` |
| Schedule expression | `rate(4 hours)` |
| Executions per day | 6 |
| Time zone | America/New_York |
| Flexible time window | Off |
| Start date | Not specified |
| End date | Not specified |
| Retry policy | Not configured |
| Dead-letter queue | Not configured |
| Execution role | `bks-eventbridge-scheduler-role` |
| Current schedule status | Disabled after testing |

### How to Create the Schedule

If we need to recreate the schedule:

1. Log in to the AWS Console.
2. Select the `us-east-2` region.
3. Open Amazon EventBridge.
4. Go to Scheduler, then Schedules.
5. Click Create schedule.
6. Enter `bks-ingest-schedule` as the schedule name.
7. Select the default schedule group.
8. Select a recurring schedule.
9. Select a rate-based schedule.
10. Set the frequency to every 4 hours.
11. Turn off the flexible time window.
12. Select AWS Lambda Invoke as the target.
13. Select `bks-ingest-lambda` as the function.
14. Configure the target input.
15. Configure the required execution permissions.
16. Keep the schedule disabled until we are ready to test it.
17. Review the settings and create the schedule.

We do not need to create another schedule because our schedule already exists.

### Target Input

We configured the following JSON input for scheduled runs:

```json
{
    "source": "eventbridge"
}
```

The Lambda handler records this source in CloudWatch. This helps us identify scheduled runs and separate them from manual runs.

### IAM Permissions

EventBridge Scheduler needs permission to invoke our Lambda function.

We created and verified the following execution role:

`bks-eventbridge-scheduler-role`

The role has a customer-managed permission policy that allows the following action:

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

The trust relationship allows EventBridge Scheduler to assume the role and use its permissions to invoke the Lambda.

This role is different from the Lambda execution role, which allows Lambda to access SSM Parameter Store and write logs to CloudWatch.

### Cost Control

Running the pipeline every 4 hours means approximately 180 executions in a 30-day month.

Our automatic test used 512 MB of configured memory and had a billed duration of about 11.23 seconds.

Based on this test, the estimated monthly Lambda compute usage is about 1,010 GB-seconds.

The expected compute cost is low and may be covered by the AWS free tier if enough free usage is available. Actual costs depend on execution time, requests, logging, data transfer, and other AWS usage.

We should continue monitoring AWS costs and avoid creating unnecessary resources.

### Current Status

- The schedule was created on November 23, 2026, Eastern Time.
- The team approved running the pipeline every 4 hours.
- The Scheduler execution role and trust relationship were verified.
- The automatic execution was successfully tested on November 24, 2026.
- The schedule was disabled after testing.

## 3. Manual vs. Scheduled Lambda Runs

Our Bike Share ingest Lambda can run in two different ways.

### Manual Run

A manual run happens when we start the Lambda ourselves from the AWS Lambda Console.

We use manual runs to:

- Test the Lambda after deployment.
- Check that the pipeline works correctly.
- Find and fix errors.
- Test changes before enabling automatic runs.

The team used the following JSON input during the manual test:

```json
{
    "source": "manual"
}
```

On November 23, 2026, the manual test successfully processed 373 stations and 777 bikes.

We verified the results in CloudWatch and Supabase.

### Scheduled Run

A scheduled run happens when EventBridge Scheduler starts the Lambda automatically.

We use scheduled runs to:

- Collect Bike Share data without manual work.
- Keep our Supabase database updated.
- Run the pipeline regularly.

The scheduled run uses the following JSON input:

```json
{
    "source": "eventbridge"
}
```

On November 24, 2026, we enabled the EventBridge schedule and successfully tested the automatic execution.

The Lambda processed 375 stations and 639 bikes without errors.

### Main Differences

| Feature | Manual Run | Scheduled Run |
|---|---|---|
| Started by | Team member | EventBridge Scheduler |
| Frequency | When needed | Every 4 hours when enabled |
| Input source | `manual` | `eventbridge` |
| Purpose | Testing and debugging | Automatic data collection |
| Logs | CloudWatch | CloudWatch |
| Database | Supabase | Supabase |
| Test status | Successful | Successful |

Both runs use the same Lambda function and perform the same pipeline operations.

### Actual Test Results

| Metric | Manual Run | Scheduled Run |
|---|---:|---:|
| Test date | November 23, 2026 | November 24, 2026 |
| Stations extracted | 373 | 375 |
| Bikes extracted | 777 | 639 |
| Total records extracted | 1,150 | 1,014 |
| Total raw records loaded | 1,150 | 1,014 |
| Gold rows upserted | 7,015 | 7,390 |
| Execution duration | 8.16 seconds | 7.58 seconds |
| Billed duration | 11.81 seconds | 11.23 seconds |
| Configured memory | 512 MB | 512 MB |
| Maximum memory used | 250 MB | 253 MB |
| Status | Success | Success |

The number of Gold rows upserted includes existing records that may have been updated. It does not mean that all those records were newly inserted.

The difference in the number of stations and bikes is normal because the Bike Share data changes throughout the day.

### Current Status

Both manual and automatic executions were successfully tested.

We confirmed that the Lambda handler records the input source in CloudWatch, which allows us to identify the type of execution.

## 4. Checking Lambda Logs in CloudWatch

AWS CloudWatch helps us understand what happens when our Lambda runs.

We can use the logs to check successful runs, find errors, and see how long each execution takes.

### How to Find the Logs

1. Log in to the AWS Console.
2. Select the `us-east-2` region.
3. Open CloudWatch.
4. Go to Logs, then Log groups or Log Management.
5. Look for the following log group:

```text
/aws/lambda/bks-ingest-lambda
```

6. Open the log group.
7. Select a recent log stream.
8. Check the execution time, messages, and errors.

### Understanding Lambda Logs

Lambda normally provides the following messages:

| Message | Meaning |
|---|---|
| INIT_START | Lambda starts initializing its environment |
| START | Lambda starts running the function |
| END | Lambda finishes the invocation |
| REPORT | Shows execution time and memory usage |
| RequestId | Helps identify each Lambda execution |
| INFO | Provides information about the execution |
| ERROR | Shows a problem during the execution |

### What a Successful Run Looks Like

During a successful run, the pipeline:

- Retrieves the Supabase credentials.
- Collects Bike Share data.
- Loads raw data into Supabase.
- Transforms and saves data to the Gold table.
- Updates the pipeline run history.
- Finishes without errors.

During our automatic test on November 24, 2026, CloudWatch showed the following messages:

```text
375 rows upserted to stations_raw

639 rows upserted to bike_information

7390 rows upserted to gold.enriched_bks

Data transformation complete!
```

The application also recorded the following result:

```json
{
    "status": "ok",
    "source": "eventbridge",
    "stages": {
        "extract": {
            "stations": 375,
            "bikes": 639
        },
        "load_raw": {
            "stations": 375,
            "bikes": 639
        },
        "transform": {
            "rows": 7390
        }
    },
    "run_id": "9045e216-efec-41a8-9c8b-db67594b3662"
}
```

The Lambda REPORT message showed:

| Metric | Result |
|---|---|
| Duration | 7579.66 ms |
| Billed duration | 11227 ms |
| Memory size | 512 MB |
| Maximum memory used | 253 MB |
| Initialization duration | 3646.51 ms |

These logs show that the extract, load, and transform stages completed successfully.

### What a Failed Run Looks Like

A failed run may include:

- Problems connecting to the Bike Share API.
- Problems connecting to Supabase.
- Missing credentials or permissions.
- Python errors.
- Lambda timeout errors.
- Incorrect Lambda handler configuration.

During our CloudWatch review, we found an earlier failed execution from November 23, 2026.

The error message was:

```text
Runtime.ImportModuleError:
Unable to import module 'lambda_function':
No module named 'lambda_function'
```

This error means that Lambda could not find the configured Python module.

The current Lambda handler configuration is:

```text
lambda_handler.lambda_handler
```

A later successful execution confirmed that the import problem was no longer blocking the pipeline.

We can use the error messages and RequestId to investigate problems.

The END and REPORT messages alone do not mean the pipeline was successful. We also need to check the application status and database results.

An initialization error may happen before the pipeline can write a record to Supabase. This is another reason why CloudWatch logs are important.

### Manual vs. Scheduled Logs

Both manual and scheduled runs use the same Lambda log group.

We verified that the Lambda handler records the source of each tested execution.

For manual runs:

```json
{
    "source": "manual"
}
```

For scheduled runs:

```json
{
    "source": "eventbridge"
}
```

We can use the source, execution timestamp, RequestId, Scheduler metrics, and database run history together to identify and verify an automatic execution.

### Checking EventBridge Scheduler Metrics

We can also use CloudWatch to check whether EventBridge attempted to invoke the Lambda.

1. Open CloudWatch in the `us-east-2` region.
2. Expand Metrics.
3. Select Classic metrics.
4. Search for Scheduler.
5. Open Scheduler > Schedule Group Metrics.
6. Select the `default` schedule group.
7. Select `InvocationAttemptCount`.
8. Choose a time range that includes the scheduled execution.

During our automatic test, CloudWatch showed one invocation attempt for the default schedule group.

The metric timestamp was consistent with our Lambda execution time.

The `TargetErrorCount` metric was not visible during our review. We did not observe a target error, but we could not verify an explicit zero value for this metric.

Scheduler metrics are reported at the schedule group level. We should use them together with the Lambda logs and Supabase results.

### Security and Cost Control

- Making sure API keys and passwords do not appear in the logs.
- Checking Lambda execution time and memory usage.
- Avoiding unnecessary Lambda executions.
- Reviewing log retention settings.
- Monitoring AWS costs.

During our review, the CloudWatch log group had a retention setting of Never expire.

We should discuss setting a reasonable retention period with the team to avoid storing unnecessary logs.

No API keys or passwords were visible in the execution logs we reviewed.

### Current Status

- CloudWatch log group verified.
- Successful manual execution logs verified.
- Earlier failed execution logs reviewed.
- Successful automatic execution logs verified.
- Manual and EventBridge input sources verified.
- Scheduler invocation metrics verified.
- Log retention reviewed but not changed.

CloudWatch alarms are covered separately in KAN-35.

## 5. Pausing or Deleting the EventBridge Schedule

Sometimes we may need to stop the Lambda from running automatically.

For example, we may need to fix an error, update our code, test a new feature, or reduce AWS costs.

### How to Pause the Schedule

1. Log in to the AWS Console.
2. Select the `us-east-2` region.
3. Open Amazon EventBridge.
4. Go to Scheduler, then Schedules.
5. Open `bks-ingest-schedule`.
6. Click Disable.
7. Confirm the change if requested.
8. Verify that the schedule status is Disabled.

Disabling the schedule stops future scheduled executions without deleting the schedule.

It does not stop a Lambda invocation that is already running or necessarily cancel an invocation that has already been submitted.

### How to Enable the Schedule Again

1. Open Amazon EventBridge.
2. Go to Scheduler, then Schedules.
3. Open `bks-ingest-schedule`.
4. Verify the schedule frequency and Lambda target.
5. Click Enable.
6. Confirm the change if requested.
7. Verify that the schedule status is Enabled.
8. Check CloudWatch after the next scheduled execution.

Before enabling the schedule again, we should make sure the Lambda is working correctly.

We should also confirm that the team is ready for automatic data collection.

### How to Delete the Schedule

1. Open Amazon EventBridge.
2. Go to Scheduler, then Schedules.
3. Select `bks-ingest-schedule`.
4. Click Delete.
5. Confirm the deletion.

Deleting the schedule removes it permanently. We would need to create a new schedule if we wanted to use it again.

Deleting the schedule does not delete the Lambda function or the data stored in Supabase.

We should not delete shared AWS resources without discussing it with the team.

### Important Notes

- Disabling the schedule is better when we only need to stop it temporarily.
- Deleting the schedule is useful when we no longer need it.
- Disabling the schedule does not prevent manual Lambda runs.
- Disabling the schedule does not delete existing CloudWatch logs or Supabase data.
- We should discuss changes with the team before modifying shared AWS resources.

### Current Status

On November 24, 2026, we enabled the schedule to test the automatic execution.

After verifying the CloudWatch logs, Scheduler metrics, and Supabase results, we disabled the schedule.

The schedule is still available with its four-hour configuration and can be enabled again when the team is ready.

## 6. Checking That the Lambda Ran Automatically

After enabling our EventBridge schedule, we need to check that the Lambda runs automatically and saves data to Supabase.

We completed this test on November 24, 2026.

### Step 1: Check EventBridge

1. Log in to the AWS Console.
2. Select the `us-east-2` region.
3. Open Amazon EventBridge.
4. Go to Scheduler, then Schedules.
5. Open `bks-ingest-schedule`.
6. Check the schedule frequency and Lambda target.
7. Enable the schedule when ready to test.
8. Check the Scheduler metrics in CloudWatch for invocation attempts and errors.

An enabled schedule does not mean the Lambda ran successfully. We still need to check the execution logs and database results.

### Step 2: Check CloudWatch Logs

1. Open CloudWatch.
2. Go to Logs, then Log groups or Log Management.
3. Find `/aws/lambda/bks-ingest-lambda`.
4. Open the logs around the scheduled execution time.
5. Check the RequestId, execution time, and pipeline messages.
6. Verify that the source is `eventbridge`.
7. Make sure the pipeline completed without errors.

We should avoid manual runs during the scheduled test so we do not confuse the results.

### Step 3: Check Supabase

Before and after the scheduled execution, open the Supabase SQL Editor and run the following query:

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

This query helps us check the latest pipeline runs, their status, and the number of records processed.

We can also check the Gold table:

```sql
SELECT
    COUNT(*) AS total_rows,
    MAX(collected_at) AS latest_run
FROM gold.enriched_bks;
```

Both queries are read-only and do not change the database.

The total number of rows may stay the same because the pipeline uses upserts to insert or update records.

The `collected_at` value represents the data collection timestamp and may be different from the Lambda execution start time.

We should use the pipeline run records and CloudWatch logs together to confirm that the pipeline ran successfully.

### Actual Automatic Test Timeline

The following times are in UTC.

| Time | Event |
|---|---|
| 22:00:34 | EventBridge schedule enabled |
| 22:01:16 | Lambda initialization started |
| 22:01:20 | Lambda execution started |
| 22:01:23 | Raw data loaded |
| 22:01:27 | Gold data saved and pipeline completed |
| After execution | Supabase results verified |
| After database verification | Scheduler invocation metrics verified |
| After testing | EventBridge schedule disabled |

### Supabase Results Before and After Testing

| Metric | Before | After |
|---|---|---|
| Total Gold records | 7,015 | 7,390 |
| Latest collection timestamp | 2026-11-23 18:38:45 | 2026-11-24 22:01:23 |
| Pipeline run records | 3 | 4 |
| Successful pipeline runs | 3 | 4 |

The total number of records in the Gold table increased by 375.

This confirmed that the database received updated data after the automatic Lambda execution.

### Automatic Pipeline Run Details

| Field | Result |
|---|---|
| Run ID | `9045e216-efec-41a8-9c8b-db67594b3662` |
| Lambda RequestId | `be6b0609-021e-469b-8a7e-297b76d711b2` |
| Status | success |
| Source in CloudWatch | eventbridge |
| Extracted | 1,014 |
| Loaded | 1,014 |
| Transformed | 7,390 |
| Duration | 7.58 seconds |

The Run ID and record counts matched the results from CloudWatch and Supabase.

We also verified that CloudWatch recorded one Scheduler invocation attempt for the default schedule group.

Together, these results confirmed that EventBridge automatically triggered our Lambda and that the pipeline successfully updated Supabase.

### Automatic Execution Checklist

- [x] EventBridge schedule is configured.
- [x] Scheduler has permission to invoke Lambda.
- [x] IAM trust relationship is verified.
- [x] EventBridge schedule was enabled for testing.
- [x] EventBridge triggered Lambda automatically.
- [x] CloudWatch logs show the scheduled execution.
- [x] The pipeline finished without errors.
- [x] Supabase shows a new successful pipeline run.
- [x] Raw and Gold data were processed successfully.
- [x] Gold table row count increased.
- [x] Scheduler invocation attempt was verified.
- [x] No API keys or passwords were visible in the reviewed logs.
- [x] Schedule was disabled after testing.
- [ ] Duplicate records checked separately using the same key.
- [ ] Multiple scheduled executions verified over a longer period.

### Remaining Recommendations

- Checking for duplicate records after repeated executions.
- Monitoring the pipeline after the schedule is enabled for regular use.
- Discussing CloudWatch log retention with the team.
- Discussing whether Scheduler retries and a dead-letter queue are needed.
- Continuing to monitor AWS costs.
- Enabling the schedule again when the team is ready.

### Final Status

The EventBridge schedule was successfully configured and tested.

We verified the automatic execution using three sources:

- EventBridge Scheduler invocation metrics.
- Lambda execution logs in CloudWatch.
- Pipeline run history and Gold table results in Supabase.

The automatic execution successfully processed 375 stations and 639 bikes. The total number of records in the Gold table increased from 7,015 to 7,390.

The initial automatic execution test is complete. The schedule is currently disabled until the team is ready to use it regularly.

No additional AWS resources are required for the current scheduling configuration.
