### CloudWatch Alarm: `bks-ingest-lambda-errors-alarm`

**Purpose:** Monitors the `bks-ingest-lambda` function for execution errors and notifies the team when the function encounters a failure.

#### Alarm Configuration

| Setting                 | Value                            |
| ----------------------- | -------------------------------- |
| Metric                  | `AWS/Lambda → Errors`            |
| Lambda Function         | `bks-ingest-lambda`              |
| Statistic               | Sum                              |
| Period                  | 5 minutes                        |
| Threshold               | Greater than or equal to 1 error |
| Evaluation Periods      | 1                                |
| Datapoints to Alarm     | 1                                |
| Alarm Name              | `bks-ingest-lambda-errors-alarm` |
| Notification Service    | Amazon SNS                       |
| SNS Topic               | `bks-alerts`                     |
| Notification Recipients | Team email addresses             |

#### Alarm Behavior

The alarm enters the `ALARM` state when the Lambda function reports at least one execution error within a 5-minute period.

When the alarm is triggered, CloudWatch sends a notification through the `bks-alerts` SNS topic to the subscribed team members.

The alarm returns to the `OK` state when the error count falls below the configured threshold.

#### Notes

- The alarm monitors execution errors, including function failures and timeouts.
- The alarm does not detect every possible issue, such as a function that stops running without reporting errors.
- The alarm requires an active SNS email subscription for each recipient.
- CloudWatch alarm notifications are configured for the `ALARM` state. Notifications for recovery can be enabled separately if needed.
