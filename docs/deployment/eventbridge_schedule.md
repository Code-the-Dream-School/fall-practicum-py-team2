

# KAN-36 — EventBridge Scheduling and CloudWatch Monitoring

## 1. Overview

The goal of KAN-36 is to run our Bike Share data pipeline automatically using AWS EventBridge.

Instead of starting the Lambda manually every time, EventBridge will trigger it on a schedule.

CloudWatch will help us check whether the Lambda ran successfully or failed.

The planned workflow is:

EventBridge Scheduler → AWS Lambda → Bike Share API → Supabase Database

This task will also document:
- How often the Lambda runs and why.
- The difference between manual and scheduled runs.
- Where to find CloudWatch logs.
- How to identify successful and failed runs.
- How to pause or delete the schedule.
- How to verify that the database was updated automatically.

**Current status:** Documentation in progress. The schedule has not been created or tested yet. We are waiting for the ingest Lambda deployment.


## 2. EventBridge Schedule

We propose running the Bike Share ingest Lambda every 6 hours.

### Why every 6 hours?

- It updates our Bike Share data four times per day.
- It reduces unnecessary Lambda executions.
- It helps us control AWS usage and costs.
- It gives us enough runs to test automatic scheduling.

### Planned Configuration

- AWS service: Amazon EventBridge Scheduler
- Target: Bike Share ingest Lambda
- Schedule expression: rate(6 hours)
- Time zone: UTC
- Flexible time window: Off
- Schedule status: Not created yet

### Current Status

This frequency is a proposal and needs team approval.

We will create and enable the schedule only after the ingest Lambda is deployed and tested successfully.


## 3. Manual vs. Scheduled Lambda Runs

Our Bike Share ingest Lambda can be started in two ways.

### Manual Run

A manual run happens when we start the Lambda ourselves using the AWS Lambda console.

We use manual runs to:
- Test the Lambda after deployment.
- Check that the pipeline works correctly.
- Troubleshoot errors.

### Scheduled Run

A scheduled run happens when Amazon EventBridge Scheduler automatically triggers the Lambda.

We use scheduled runs to:
- Collect Bike Share data without manual work.
- Keep our Supabase database updated.
- Run the pipeline regularly.


### Main Difference

The difference is how we start the Lambda.

For a manual run, we start it ourselves in the AWS console.

For a scheduled run, EventBridge starts it automatically at the scheduled time.

Both runs should do the same job: collect Bike Share data and save it to our Supabase database.

EventBridge may send different information to the Lambda when it starts. We need to make sure our Lambda can handle that information.


### Current Status

Manual and scheduled runs have not been verified yet.

We will compare their CloudWatch logs after the ingest Lambda is deployed and the schedule is enabled.



## 4. Checking Lambda Logs in CloudWatch

AWS CloudWatch helps us see what happens when our Lambda runs.

Each time the Lambda runs, it can create logs that show us what happened.

### How to Find the Logs

1. Log in to the AWS Console.
2. Open CloudWatch.
3. Click Logs, then Log Management.
4. Look for `/aws/lambda/bks-ingest-lambda`.
5. Open the log group.
6. Select a recent log stream to see the details.

The log group name depends on the actual Lambda name.

### What a Successful Run Looks Like

A successful run should:
- Start without errors.
- Collect Bike Share data.
- Save the data to Supabase.
- Finish without any errors.

CloudWatch normally shows START, END, and REPORT messages for a Lambda run.

### What a Failed Run Looks Like

A failed run may show:
- An error while collecting data.
- A problem connecting to Supabase.
- Missing configuration or permissions.
- A timeout or another Python error.

We can read the error message to understand what went wrong.

### Current Status

We have not checked real Lambda execution logs yet.

After the Lambda is deployed, we will use CloudWatch to check both successful and failed runs.



## 5. Pausing or Deleting the EventBridge Schedule

Sometimes we may need to stop our Lambda from running automatically.

For example, we may want to fix an error, update our code, or avoid unnecessary AWS usage.

### How to Pause the Schedule

1. Log in to the AWS Console.
2. Open Amazon EventBridge.
3. Go to Scheduler, then Schedules.
4. Find our Bike Share schedule.
5. Select the schedule and click Edit.
6. Change the schedule status to Disabled.
7. Save the changes.

This stops future scheduled runs without deleting the schedule.

### How to Delete the Schedule

1. Open Amazon EventBridge.
2. Go to Scheduler, then Schedules.
3. Select our Bike Share schedule.
4. Click Delete.
5. Confirm the deletion.

Deleting the schedule removes it. We would need to create it again if we wanted to use it later.

### Current Status

Our EventBridge schedule has not been created yet.



## 6. Checking That the Lambda Ran Automatically

After we turn on our EventBridge schedule, we need to make sure it actually works.

We cannot just assume everything is working because the schedule is enabled.

### Step 1: Check CloudWatch

1. Open AWS CloudWatch.
2. Go to Logs, then Log Management.
3. Find our ingest Lambda log group.
4. Open the logs for the time when EventBridge should have started the Lambda.
5. Check if the Lambda started and finished without errors.

We also need to make sure this was an automatic run, not a manual test.

### Step 2: Check Supabase

1. Open our Supabase project.
2. Go to the SQL Editor.
3. Run this query:

```sql
SELECT
    COUNT(*) AS total_rows,
    MAX(collected_at) AS latest_data
FROM gold.enriched_bks;
```

4. Check the results.

The query shows how many rows we have and the latest data collection time.

We should compare the results before and after a scheduled run to see if the data was updated.

### Step 3: Confirm the Results

We can confirm our schedule works when:

- EventBridge shows that it triggered our Lambda.
- CloudWatch shows the Lambda ran successfully.
- Supabase shows that our data was updated.

### Current Status

We have not tested an automatic run yet because the ingest Lambda and EventBridge schedule are not ready.

We will add the real test results after the deployment.



