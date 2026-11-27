# CI/CD Lambda Deployment (KAN-37)

Automated deployment workflow for `bks-ingest-lambda` (`us-east-2`) using GitHub Actions.

## How the Workflow Runs
- **File:** `.github/workflows/deploy-lambda.yml`
- **Automatic Trigger:** Runs automatically whenever code is merged or pushed to the `main` branch.
- **Manual Trigger:** Can also be triggered on demand from the GitHub **Actions** tab → **Deploy Ingest Lambda** → **Run workflow**.
- **Steps:** Checks out the repo, installs Linux `x86_64` Python 3.11 dependencies, bundles `lambda_handler.py` and `services/pipeline/src/pipeline` into `lambda_package.zip`, authenticates with AWS, and updates `bks-ingest-lambda`.

## Security & Credentials
- AWS credentials are stored in **GitHub Repository Secrets** (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`)—never in the repository.
- The IAM user (`github-actions-bks-deploy`) follows least-privilege access via inline policy `DeployBksIngestLambda`, allowing only `lambda:UpdateFunctionCode` and `lambda:GetFunction` on `bks-ingest-lambda`.

## How to Know If a Deployment Failed
1. **Commit / PR Status:** A red **X** appears next to the latest commit on `main` (green checkmark = succeeded).
2. **GitHub Actions Tab:** Open **Actions → Deploy Ingest Lambda** to see the status of every run.
3. **Debugging Logs:** Click any failed run → click the **deploy** job → expand the step with the red **X** to read the exact error (e.g., missing file path, dependency install error, or AWS permission issue).