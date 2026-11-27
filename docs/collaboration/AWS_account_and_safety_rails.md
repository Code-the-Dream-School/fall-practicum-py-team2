# AWS account and safety rails
This document describes AWS account safety measures
## Budgets alarm
Budget alarms allow the team to monitor the project budget and receive notifications when the budget runs out. Team members will receive an alert if 20% , 50% and 80% is used from the $100 project budget.

## Limited IAM user or role
AWS allows creating IAM users and roles with limited permissions to separate responsibilities between team members and services. This helps prevent accidental changes to critical resources and reduces the risk of unauthorized access.
By following the principle of least privilege, each user or role is granted only the permissions necessary to perform its assigned tasks.

### IAM Role: `bks-enrich-lambda-role`

**Purpose:** Allows the AWS Lambda function to write execution logs to Amazon CloudWatch Logs and retrieve the required configuration parameters and API keys from AWS Systems Manager Parameter Store (SSM).

#### Permissions

| Service | Action | Resource |
|---|---|---|
| CloudWatch Logs | `logs:CreateLogGroup` | `*` |
| CloudWatch Logs | `logs:CreateLogStream` | `*` |
| CloudWatch Logs | `logs:PutLogEvents` | `*` |
| SSM Parameter Store | `ssm:GetParameter` | The four parameters listed below |
| SSM Parameter Store | `ssm:GetParameters` | The four parameters listed below |

#### SSM Parameters

The role grants read access to the following parameters:

- `/bks/SUPABASE_URL`
- `/bks/SUPABASE_KEY`
- `/bks/GEMINI_API_KEY`
- `/bks/OPENAI_API_KEY`

#### Security Notes

- The role follows the principle of least privilege by limiting SSM access to the specific parameters required by the Lambda function.
- The API keys are stored in SSM Parameter Store rather than hardcoded in the Lambda function.
- CloudWatch Logs permissions allow the function to create log groups and streams and publish execution logs.

### IAM Role: `bks-eventbridge-scheduler-role`

**Purpose:** Allows Amazon EventBridge Scheduler to invoke the AWS Lambda function `bks-ingest-lambda` on a scheduled basis.

#### Permissions

| Service | Action | Resource |
|---|---|---|
| AWS Lambda | `lambda:InvokeFunction` | `arn:aws:lambda:us-east-2:607601850743:function:bks-ingest-lambda` |
| AWS Lambda | `lambda:InvokeFunction` | `arn:aws:lambda:us-east-2:607601850743:function:bks-ingest-lambda:*` |

#### Resource Details

- **AWS Region:** `us-east-2` (Ohio)
- **AWS Account ID:** `607601850743`
- **Lambda Function:** `bks-ingest-lambda`
- **Function ARN:** `arn:aws:lambda:us-east-2:607601850743:function:bks-ingest-lambda`

#### Security Notes

- The role follows the principle of least privilege by granting permission to invoke only the specified Lambda function and its versions or aliases.
- The `lambda:InvokeFunction` permission allows EventBridge Scheduler to trigger the Lambda function.
- The role does not grant permission to modify the Lambda function, access its execution environment, or manage other AWS resources.
- The role is intended to be assumed by Amazon EventBridge Scheduler through its IAM trust policy.

#### Trust Relationship

The role's trust policy should allow the `scheduler.amazonaws.com` service principal to assume the role using `sts:AssumeRole`.

This enables EventBridge Scheduler to use the role's permissions when invoking the Lambda function.

### IAM Role: `bks-ingest-lambda-role`

**Purpose:** Allows the AWS Lambda function `bks-ingest-lambda` to write execution logs to Amazon CloudWatch Logs and retrieve the Supabase configuration parameters from AWS Systems Manager (SSM) Parameter Store.

#### Permissions

| Service | Action | Resource |
|---|---|---|
| CloudWatch Logs | `logs:CreateLogGroup` | `*` |
| CloudWatch Logs | `logs:CreateLogStream` | `*` |
| CloudWatch Logs | `logs:PutLogEvents` | `*` |
| SSM Parameter Store | `ssm:GetParameter` | `/bks/SUPABASE_URL` |
| SSM Parameter Store | `ssm:GetParameter` | `/bks/SUPABASE_KEY` |
| SSM Parameter Store | `ssm:GetParameters` | `/bks/SUPABASE_URL` |
| SSM Parameter Store | `ssm:GetParameters` | `/bks/SUPABASE_KEY` |

#### SSM Parameters

The role grants read access to the following parameters:

- `/bks/SUPABASE_URL` — Supabase project URL.
- `/bks/SUPABASE_KEY` — Supabase API key.

#### Security Notes

- The role follows the principle of least privilege by restricting SSM access to the two parameters required by the Lambda function.
- The Supabase credentials are stored in SSM Parameter Store rather than hardcoded in the Lambda function.
- CloudWatch Logs permissions allow the function to create log groups and streams and publish execution logs.
- The role does not grant permission to modify or delete SSM parameters.

#### Trust Relationship

The role's trust policy should allow the `lambda.amazonaws.com` service principal to assume the role using `sts:AssumeRole`.

This enables the Lambda function to use the permissions granted by the role during execution.

**Note:** If `/bks/SUPABASE_KEY` is stored as a `SecureString` encrypted with a customer-managed AWS KMS key, the role may also need `kms:Decrypt` permission for that key. This is not included in the permissions provided above.

## SSM Parameter Store
SSM parameter store keeps important information in a secure place so it's not available in public.
We have 3 secure parameters: GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY