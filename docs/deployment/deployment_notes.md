

# Deployment Notes and Runtime Configuration (KAN-33)

### 1. Overview

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

### 3. AWS Resources

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
