# Runbook: Terraform Deployment and Remote State Recovery

## 1. Purpose

This runbook covers the Project 2 Terraform CI and approved deployment workflow, remote-state access, failed plans and state-lock incidents. It is for the five Terraform-managed monitoring resources in terraform/main.tf; it does not make the Azure Monitor Workbook a Terraform-managed resource.

## 2. Project 2 state backend

| Setting | Value |
|---|---|
| Resource Group | rg-portfolio |
| Storage Account | aniketterraformstate26 |
| Container | project2-tfstate |
| State key | project2.tfstate |
| Authentication | Microsoft Entra ID / Azure AD |
| CI identity | GitHub Actions OIDC CI identity |
| Deployment identity | Separate GitHub Actions OIDC deployment identity |
| State role | Blob Data Contributor scoped to the Project 2 container |

Project 1 uses its own project1-tfstate container and state key in the same dedicated account. Do not point Project 2 at the Project 1 container or state file. The old Project 2 state blob was deleted only after the destination state was checked; a local backup was retained.

## 3. What Terraform manages

Project 2 Terraform manages these existing monitoring resources:

1. Application Insights component aniket-portfolio-api (90-day retention).
2. Action Group ag-portfolio-failures.
3. Scheduled query alert alert-portfolio-api-failures.
4. Availability web test portfolio-api-health-check-aniket-portfolio-api.
5. Availability metric alert portfolio-api-health-check-aniket-portfolio-api.

The workbook is maintained separately from Terraform using scripts/deploy_workbook.py and the canonical docs/workbook/workbook.json. Never import the workbook into this Terraform state without an explicit ownership change.

## 4. Standard CI and deployment workflow

### CI

File: .github/workflows/terraform.yml.

The CI workflow runs on main pushes and manual dispatch. It authenticates with the CI OIDC identity, initializes the remote backend, checks formatting, validates configuration and creates a plan. Its Azure access is intended to be read-only, in addition to the state permissions required by Terraform.

### Approved deployment

File: .github/workflows/terraform-apply.yml.

1. Open Actions → Terraform Deployment.
2. Select branch main and run the workflow manually.
3. Review the generated plan.
4. Approve the protected terraform-apply GitHub Environment when prompted.
5. Verify the saved-plan apply and cleanup steps complete successfully.
6. Capture the run URL and plan summary in the relevant Azure Boards item.

Post-migration verification: Deployment run [#2 / run ID 45388391908](https://github.com/712Aniket/azure-cloud-operations-observability/actions/runs/45388391908) completed successfully on 24 November 2026. Azure deployment identity login, backend initialization, format, validation, plan and saved-plan apply all succeeded. The apply result was 0 added, 0 changed, 0 destroyed.

## 5. Local read-only checks

From the repository root:

~~~bash
cd terraform
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
~~~

Review the complete plan before authorizing any deployment. Do not run a local terraform apply as a shortcut around the protected workflow.

## 6. Troubleshooting

| Symptom | Safe first checks |
|---|---|
| OIDC login failure | Check workflow permissions, federated credential subject/audience, identity client ID and GitHub Environment configuration. Never replace OIDC with a committed client secret. |
| Backend 403 | Confirm the running workflow identity has Blob Data Contributor on the Project 2 state container and that Entra ID backend auth is enabled. |
| Backend not found | Verify storage account, container and state key against terraform/backend.tf; do not create a new empty state to bypass an access problem. |
| Terraform lock error | Check whether a GitHub Actions run or local Terraform process is still active. Wait for it to finish before considering any unlock. |
| Unexpected plan changes | Stop before approval. Compare code, provider version, Azure configuration and state ownership. Do not apply a destructive or unexplained plan. |
| Workbook differs from source | Run the workbook preflight. Workbook deployment is a separate explicit operation and must target only the primary workbook ID. |

## 7. State recovery precautions

- Never commit terraform.tfstate, state backups, .tfplan files or backend credentials.
- Do not manually edit the state JSON.
- Do not delete the remote blob to resolve a lock or plan issue.
- Do not use terraform force-unlock while any workflow or local process may still hold the lock.
- Before any state migration, take a timestamped backup, verify source and destination lineage/resource counts, and preserve the backup until a successful plan has been run against the destination.
- If the state backend is unavailable, stop deployments and restore access first. Do not recreate resources from an empty state.

## 8. Deployment incident closure

Close a deployment incident only after the expected OIDC identity authenticated, the correct remote backend initialized, Terraform validation passed, the plan was reviewed and the saved-plan apply completed. Record the run ID, commit SHA and add/change/destroy counts.
