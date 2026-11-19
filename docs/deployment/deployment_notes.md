

# Deployment Notes and Runtime Configuration (KAN-33)

## 1. Overview

This document explains the AWS deployment architecture, runtime
configuration, secrets management, and the differences between
running the Bike Share pipeline locally and in AWS.

The goal is to help team members understand, reproduce, and
maintain the cloud deployment.

The deployment is currently in progress. Some configuration
details will be confirmed after KAN-30, KAN-31, and KAN-32
are completed.

## 2. Cloud Architecture

The existing Python pipeline will run on AWS Lambda instead
of requiring a developer to start it manually.

The planned data flow is:

EventBridge → Lambda → GBFS API → Extract → Load Raw
→ Transform → Load Gold → Supabase → Streamlit Dashboard

A separate Lambda function is planned for LLM enrichment.

The Streamlit dashboard is planned to be deployed using
Docker, Amazon ECR, and Amazon ECS with Fargate.

## 3. AWS Resources

| AWS Service | Purpose                                           |
| ------------| --------------------------------------------------|
| Lambda      | Running the Python pipeline in the cloud          |
| EventBridge | Scheduling automatic pipeline runs                |
| CloudWatch  | Monitoring executions, logs, and errors           |
| IAM         | Managing permissions and access                   |
| SSM P Store | Storing configuration and secrets securely        |
| AWS Budgets | Monitoring costs and sending budget alerts        |
| Amazon ECR  | Storing the dashboard Docker image                |
| Amazon ECS  | Managing dashboard containers                     |
| AWS Fargate | Running containers without managing servers       |

These resources represent the planned architecture.
Their deployment status will be verified before finalizing
this document.


## 4. Lambda Runtime Configuration

The following configuration is based on the KAN-32
deployment guide.

| Setting                | Proposed Configuration |
| ---------------------- | ---------------------- |
| Function name          | bks-ingest-lambda      |
| Python runtime         | Python 3.11            |
| Memory                 |    512 MB              |
| Timeout                |   60 seconds           |
| Execution role         | bks-ingest-lambda-role |
| Deployment package     |      ZIP file          |
| Handler                | Pending KAN-31         |
| AWS Region             | To be confirmed        |
|------------------------|------------------------|
### Dependencies

The ingest pipeline requires the following Python libraries:

- pandas
- numpy
- requests
- supabase
- python-dotenv
- boto3

The deployment package must include the required dependencies
that are not already provided by the Lambda runtime.

Dependencies must be compatible with the Lambda Linux
environment and selected Python version.

The final package structure and handler configuration
will be confirmed after KAN-31 is completed.



## 5. Secrets and Environment Variables

# Local Configuration

When running the pipeline locally, database credentials
are loaded from the .env file using python-dotenv.

Required environment variables:

- SUPABASE_URL
- SUPABASE_KEY

The .env file must not be committed to GitHub.

# AWS Configuration

In AWS, credentials will be stored in SSM Parameter Store
as SecureString parameters.

| Parameter Name    | Purpose                     |
| --------------    | --------------------------- |
| /bks/SUPABASE_URL | Supabase project URL        |
| /bks/SUPABASE_KEY | Supabase authentication key |

Lambda will retrieve these parameters at runtime using boto3.

The Lambda execution role must have permission to access
only the required parameters.

# Safe to Commit

- Parameter names and paths
- Environment variable names
- Lambda configuration settings
- Documentation and example configuration

# Never Commit

- Supabase authentication keys
- OpenAI API keys
- AWS access keys
- Secret values
- .env files containing credentials

The final SSM configuration and permissions will be
verified after KAN-30 and KAN-31 are completed.


## 6. Local vs. Cloud Execution

The local and cloud environments use the same pipeline
functions but have different execution methods and
runtime configurations.
--------------|--------------------------------|----------------------|
| Feature     | Local                          | AWS Cloud            |
| ----------- | ------------------------------ | -------------------- |
| Execution   | Python scripts or Prefect      | Lambda handler       |
| Trigger     | Manual execution               | Manual or EventBridge|
| Credentials | .env file                      | SSM Parameter Store  |
| File storage| Local filesystem               | /tmp directory       |
| Dependencies| Virtual environment            | Deployment package   |
| Logging     | Terminal                       | CloudWatch           |
| Database    | Supabase                       | Supabase             |
|-------------|--------------------------------|----------------------|
### Local Execution

Developers can run the pipeline locally for development,
testing, and debugging.

Python dependencies are installed using requirements.txt,
and credentials are loaded from the local .env file.

### Cloud Execution

Lambda will execute the existing pipeline functions
through a handler.

EventBridge will trigger scheduled executions, and
CloudWatch will collect execution logs and errors.

### Temporary JSON Files

The current extraction function generates two JSON files:

- station_information.json
- bike_information.json

These files are used by the raw loading function to
insert data into Supabase.

The Lambda deployment directory is read-only.
Temporary files must be written to the /tmp directory.

Both extraction and raw loading must use the same
file paths.

Files stored in /tmp should not be treated as permanent
storage or relied on between executions.

The final implementation will be confirmed after
KAN-31 is completed.


## 7. Monitoring and Cost Control

### CloudWatch Monitoring

CloudWatch will be used to monitor Lambda executions.

The logs should include:

- Pipeline start and end times
- Execution status
- Number of records processed
- Errors and failed pipeline stages
- Execution duration

The expected log group for the ingest function is:

/aws/lambda/bks-ingest-lambda

CloudWatch alarms are planned as part of KAN-35.

### EventBridge Scheduling

EventBridge will automatically trigger the ingest Lambda
at a configured interval.

The schedule frequency, execution verification, and
instructions for pausing or removing the schedule will
be documented separately as part of KAN-36.

### Cost Control

AWS Budgets will be used to monitor cloud spending
and send budget alerts.

To help control costs:

- Using a modest execution frequency.
- Monitoring Lambda execution duration.
- Limiting CloudWatch log retention.
- Disabling unused schedules and resources.
- Monitoring ECS and Fargate costs.
- Reviewing AWS spending regularly.

Budget configuration and alerts will be confirmed
after KAN-30 is completed.


## 8. Deployment Verification

After deploying the ingest Lambda, the team should
verify that the pipeline runs successfully and writes
data to Supabase.

### Manual Execution

1. Open the ingest Lambda in the AWS Console.
2. Create a test event using an empty JSON object {}.
3. Execute the Lambda function.
4. Review the execution status.
5. Check CloudWatch logs for errors and record counts.

### Database Verification

Run the following query in the Supabase SQL Editor
before and after executing the Lambda function:

```sql
SELECT COUNT(*) AS total_rows,
       MAX(collected_at) AS latest_run
FROM gold.enriched_bks;
```

Compare the results to verify that the pipeline
processed and saved the expected data.

The total row count may remain unchanged when existing
records are updated because the pipeline uses upsert
operations.

The collected_at timestamp represents the source data
timestamp and may differ from the Lambda execution time.

### Successful Deployment Checklist

- [ ] Lambda executes without errors.
- [ ] SSM credentials are retrieved successfully.
- [ ] GBFS data is extracted successfully.
- [ ] Raw data is saved to Supabase.
- [ ] Transformed data is saved to the Gold table.
- [ ] CloudWatch logs are available.
- [ ] No duplicate records are created for the same key.
- [ ] No sensitive information appears in the logs.

### Related Deployment Guide

For detailed Lambda deployment instructions, refer to
the KAN-32 ingest Lambda deployment guide:

[Ingest Lambda Deployment Guide](ingest_lambda.md)

Scheduled execution verification will be documented
separately under KAN-36.



## 9. Known Issues and Open Questions

### Known Issues

- The current Lambda handler is still under development
  as part of KAN-31.

- The extraction and raw loading functions currently
  use different paths for JSON files. These paths need
  to be consistent in the Lambda environment.

- The transform function returns a DataFrame.
  Writing transformed records to the Gold table must
  be handled correctly when called from Lambda.

- Error handling and structured logging need to be
  finalized in the Lambda handler.

- Python dependencies must be packaged for the
  Lambda Linux environment.

- The current architecture diagram needs to be updated
  to reflect the AWS deployment.

### Open Questions

- Which AWS region will the team use?

- What will be the final Lambda handler and
  deployment package structure?

- Have the SSM parameters and IAM permissions
  been configured and verified?

- How often should EventBridge trigger the pipeline?

- What is the expected CloudWatch log retention period?

- How will the separate LLM enrichment Lambda
  be triggered?

- Will the dashboard run continuously on ECS Fargate,
  and what will be the estimated cost?

- Will the machine learning component remain separate
  from the cloud pipeline?
