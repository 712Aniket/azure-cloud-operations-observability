# Runbook: Application Insights Monitoring and Troubleshooting

## 1. Purpose

This runbook describes how to use Azure Application Insights to monitor, investigate and troubleshoot the Azure Cloud Resume Challenge API.

It covers request telemetry, application exceptions, dependency failures, performance investigation and availability monitoring using Kusto Query Language (KQL).

## 2. Monitored Resources

| Setting | Value |
|---|---|
| Resource Group | rg-portfolio |
| Azure Region | centralindia |
| Function App | aniket-portfolio-api |
| Application Insights | aniket-portfolio-api |
| Log Analytics Workspace | DefaultResourceGroup-CID |

Application Insights collects telemetry from the Azure Function App and provides information about API requests, dependencies, exceptions and application performance.

## 3. Accessing Application Insights

1. Sign in to Azure Portal.
2. Open the resource group `rg-portfolio`.
3. Select Application Insights `aniket-portfolio-api`.
4. Open Logs to investigate telemetry using KQL.
5. Use Performance and Availability to investigate application behaviour.

Select an appropriate time range before running queries.

## 4. HTTP Request Failure Investigation

Use the following query to identify HTTP 5xx responses during the last 24 hours.

```kusto
requests
| where toint(resultCode) >= 500
| where timestamp > ago(24h)
| project timestamp, name, url, resultCode, duration, operation_Id
| order by timestamp desc
```

Review:

- Request timestamp.
- Request name and URL.
- HTTP result code.
- Request duration.
- Operation ID for correlation.

HTTP 5xx responses indicate server-side failures that require further investigation.

## 5. Application Exception Investigation

Use this query to identify application exceptions.

```kusto
exceptions
| where timestamp > ago(24h)
| project timestamp, type, outerMessage, operation_Id
| order by timestamp desc
```

Review the exception type and message.

Use the operation ID to correlate an exception with related request telemetry where available.

## 6. Dependency Failure Investigation

Use this query to identify unsuccessful dependency calls.

```kusto
dependencies
| where timestamp > ago(24h)
| where success == false
| project timestamp, name, target, resultCode, duration, operation_Id
| order by timestamp desc
```

Investigate:

- Dependency name.
- Target service.
- Result code.
- Request duration.
- Related operation ID.

For this project, Cosmos DB connectivity is an important dependency to consider.

## 7. Request Distribution Analysis

Use this query to understand the distribution of HTTP response codes.

```kusto
requests
| where timestamp > ago(24h)
| summarize TotalRequests = count() by resultCode
| order by TotalRequests desc
```

This helps identify the number of successful and unsuccessful requests during the selected period.

## 8. Availability Investigation

Use the following query to review availability test results.

```kusto
availabilityResults
| where timestamp > ago(24h)
| project timestamp, name, location, success, duration, message
| order by timestamp desc
```

To investigate unsuccessful availability tests:

```kusto
availabilityResults
| where timestamp > ago(24h)
| where success == false
| project timestamp, name, location, success, duration, message
| order by timestamp desc
```

Review the test location, timestamp, duration and failure details.

Availability results help distinguish API availability problems from individual request failures.

## 9. Performance Investigation

Use Application Insights Performance to investigate:

- Slow API requests.
- Request duration.
- Operation performance.
- Dependency response times.
- Performance trends.

Use the following query to identify the slowest requests during the last 24 hours.

```kusto
requests
| where timestamp > ago(24h)
| project timestamp, name, duration, resultCode, operation_Id
| order by duration desc
| take 20
```

Investigate unusually long request durations and correlate them with dependency telemetry or exceptions.

## 10. Troubleshooting Workflow

When investigating an API issue:

1. Identify the affected time period.
2. Review HTTP request telemetry.
3. Check for HTTP 5xx responses.
4. Investigate application exceptions.
5. Review failed dependencies.
6. Examine availability test results.
7. Investigate slow requests and dependency response times.
8. Identify the likely failure point.
9. Apply an approved corrective action.
10. Verify recovery using subsequent telemetry.

Use operation IDs to correlate related telemetry when available.

## 11. Known Monitoring Observations

During project validation:

- A controlled HTTP 500 failure was successfully generated and recorded in Application Insights.
- The configured Azure Monitor alert detected the failure.
- An email notification was received through the Action Group.
- The temporary failure endpoint was subsequently removed.
- The visitor counter API was verified after the cleanup.
- A later investigation found four HTTP 200 requests in the selected one-hour request distribution query.
- The selected one-hour and 24-hour failure queries returned no HTTP 5xx records.
- Exception and failed dependency queries returned no records in the selected one-hour window.

These observations apply to the specific test and query time windows. They should not be interpreted as proof that failures can never occur.

## 12. Security and Operational Precautions

- Do not expose credentials, tokens or connection strings in logs.
- Avoid logging sensitive user information.
- Do not commit secrets to GitHub.
- Investigate unexpected telemetry before making production changes.
- Use the approved GitHub Actions deployment workflow.
- Preserve Terraform remote state.
- Review Terraform plans before applying infrastructure changes.

## 13. Incident Closure Criteria

An investigation can be closed when:

- The issue has been identified or sufficiently investigated.
- Corrective actions have been completed where required.
- API requests are behaving as expected.
- No unexpected exceptions or dependency failures are observed in the relevant verification period.
- Availability monitoring is functioning.
- The incident and findings are documented.

## 14. Operational Ownership

This runbook is maintained as part of the Azure Cloud Operations & Observability Platform project.

Review it whenever Application Insights configuration, telemetry collection, KQL queries or monitoring architecture changes.