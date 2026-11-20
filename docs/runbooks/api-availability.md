# Runbook: API Availability Monitoring and Recovery

## 1. Purpose

This runbook describes how to monitor the availability of the Azure Cloud Resume Challenge Function App using Azure Application Insights availability tests and Azure Monitor metric alerts.

It explains how to investigate failed health checks, identify availability issues and restore API functionality.

## 2. Monitored Resources

| Setting | Value |
|---|---|
| Resource Group | rg-portfolio |
| Azure Region | centralindia |
| Function App | aniket-portfolio-api |
| Application Insights | aniket-portfolio-api |
| Availability Test | portfolio-api-health-check-aniket-portfolio-api |
| Metric Alert | portfolio-api-health-check-aniket-portfolio-api |
| Action Group | ag-portfolio-failures |
| Alert Severity | 1 - Critical |

## 3. Availability Monitoring Architecture

The availability monitoring workflow operates as follows:

1. Application Insights executes a scheduled HTTP health check.
2. The health check calls the Function App health endpoint.
3. Application Insights records the availability test result.
4. Azure Monitor evaluates the availability metric.
5. If the configured failure condition is met, Azure Monitor triggers an alert.
6. The Action Group sends an email notification.

### Health Check Endpoint

`https://aniket-portfolio-api.azurewebsites.net/api/health`

### Expected Response

- HTTP status code: 200
- Endpoint should respond successfully.
- SSL certificate validation should pass.

## 4. Availability Test Configuration

The Application Insights Standard Web Test is configured as follows:

| Configuration | Value |
|---|---|
| Test Name | portfolio-api-health-check-aniket-portfolio-api |
| Enabled | Yes |
| Test Frequency | 900 seconds (15 minutes) |
| Test Location | Singapore |
| Retry Enabled | Yes |
| Timeout | 120 seconds |
| HTTP Method | GET |
| Expected Status Code | 200 |
| Follow Redirects | No |
| Parse Dependent Requests | No |
| SSL Certificate Check | Enabled |
| Minimum Certificate Lifetime | 7 days |

The test checks whether the API health endpoint is reachable and returns the expected HTTP response.

## 5. Availability Metric Alert Configuration

Azure Monitor uses a metric alert to detect availability failures.

| Configuration | Value |
|---|---|
| Alert Name | portfolio-api-health-check-aniket-portfolio-api |
| Severity | 1 - Critical |
| Evaluation Frequency | 1 minute |
| Evaluation Window | 5 minutes |
| Failed Location Count | 1 |
| Auto Mitigate | Disabled |
| Action Group | ag-portfolio-failures |

The alert uses the availability test results to identify potential API availability problems.

## 6. Incident Investigation Procedure

### Step 1: Review the Alert

When an availability alert notification arrives:

1. Open Azure Portal.
2. Navigate to Azure Monitor.
3. Open Alerts.
4. Locate the availability metric alert.
5. Review the alert firing time and affected resource.
6. Check the alert condition and metric details.

### Step 2: Review Availability Test Results

Navigate to:

Application Insights → Availability.

Review:

- Availability test results.
- Failed test executions.
- Response times.
- Test execution locations.
- Failure details.
- Availability trends.

Determine whether the failure is isolated or repeated.

### Step 3: Verify the Health Endpoint

Check the following endpoint:

`https://aniket-portfolio-api.azurewebsites.net/api/health`

Expected result:

HTTP 200 OK.

If the endpoint is unavailable, investigate the Function App.

### Step 4: Investigate Function App Health

In Azure Portal:

1. Open the Function App `aniket-portfolio-api`.
2. Review Overview and current status.
3. Check application logs.
4. Review recent deployments or configuration changes.
5. Investigate runtime errors.
6. Check whether the Function App is responding to HTTP requests.

### Step 5: Investigate Application Dependencies

If the Function App is running but the application is experiencing issues:

- Review Cosmos DB connectivity.
- Check application configuration.
- Review identity and access permissions.
- Investigate dependency failures in Application Insights.

## 7. Common Availability Problems

| Symptom | Possible Investigation |
|---|---|
| Health endpoint returns HTTP 500 | Investigate application exceptions. |
| Health endpoint returns HTTP 503 | Investigate Function App availability and hosting. |
| Connection timeout | Investigate endpoint reachability and service response time. |
| SSL certificate failure | Check certificate validity and expiration. |
| Repeated availability failures | Review test results and Function App logs. |
| API works intermittently | Investigate request duration and dependency behaviour. |

These are investigation suggestions, not confirmed diagnoses.

## 8. Recovery Procedure

After identifying the issue:

1. Identify the component causing the availability failure.
2. Review Application Insights telemetry and Function App logs.
3. Correct the application, configuration or dependency issue.
4. Use the approved deployment workflow if application changes are required.
5. Verify that the health endpoint returns HTTP 200.
6. Review subsequent Application Insights availability test results.
7. Confirm that the availability alert returns to a resolved state.
8. Verify that the visitor counter API is functioning correctly.
9. Document the incident and corrective actions.

Do not make unreviewed production changes.

## 9. Security and Operational Precautions

- Do not expose secrets or connection strings in logs.
- Do not commit credentials or private keys.
- Keep availability monitoring enabled.
- Avoid unnecessary repeated tests against production.
- Use the approved GitHub Actions deployment workflow.
- Preserve Terraform remote state.
- Review Terraform plans before applying infrastructure changes.

## 10. Incident Closure Criteria

An availability incident can be considered resolved when:

- The underlying issue has been identified and corrected.
- The health endpoint returns HTTP 200.
- Application Insights records successful availability tests.
- The visitor counter API works correctly.
- No new unexpected availability failures are observed.
- The Azure Monitor alert returns to a resolved state.
- The incident and corrective actions are documented.

## 11. Operational Ownership

This runbook is maintained as part of the Azure Cloud Operations & Observability Platform project.

Review it whenever the health endpoint, availability test, metric alert or monitoring architecture changes.