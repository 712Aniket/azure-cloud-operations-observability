# Project 2 Operations Runbooks

Use this index to choose the correct response procedure. Start with the alert or symptom, preserve evidence, and verify recovery before closing an incident.

| Symptom / task | Runbook | Primary evidence |
|---|---|---|
| HTTP 5xx responses from the portfolio API | [API failure investigation](api-failure.md) | Application Insights requests, exceptions and dependencies |
| API health check failed or timed out | [API availability and recovery](api-availability.md) | Availability test results and metric alert |
| Investigate request, exception, dependency or latency telemetry | [Application Insights troubleshooting](application-insights.md) | KQL and operation ID correlation |
| Monthly spend, resource-level charges, budget notifications or Cost Management HTTP 429 | [Cost management](cost-management.md) | Azure Cost Management, workbook and daily cache |
| Terraform CI/deployment, remote state or state-lock issue | [Terraform deployment and state recovery](terraform-deployment.md) | GitHub Actions run, Terraform plan and remote backend |
| Decide whether VNet/subnet/private endpoint controls are required | [Networking scope decision](networking-scope.md) | Current public serverless architecture and security requirements |

## Standard incident workflow

1. Record the alert name, timestamp, affected resource and operation ID where available.
2. Check Azure Service Health and the relevant resource's status before making changes.
3. Use the runbook's read-only diagnostics first.
4. Identify the likely cause and capture evidence.
5. Make the smallest reviewed corrective change. Use the approved GitHub Actions deployment workflow for Terraform-managed infrastructure.
6. Verify the original symptom is gone and dependent endpoints still work.
7. Record the cause, action and verification in the relevant incident or Azure Boards item.

## Safety boundaries

- Project 1 and Project 2 share the rg-portfolio resource group and Function App. Do not delete or recreate shared resources as a Project 2 cleanup action.
- Project 1 owns the shared Function App, Cosmos DB and portfolio frontend. Project 2 Terraform owns only its five monitoring resources.
- Project 1 state and Project 2 state are separate private containers in aniketterraformstate26.
- Never print, commit or attach .env, function keys, access tokens, storage keys, Terraform state files or saved plans.
- Never use terraform force-unlock until a matching workflow/local Terraform process has been confirmed stopped and the lock ID is verified.
- The Resource Group budget is a notification mechanism, not a spending cap.
