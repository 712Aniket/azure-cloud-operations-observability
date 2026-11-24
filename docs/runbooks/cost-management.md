# Runbook: Azure Cost Management and Budget Operations

## 1. Purpose and scope

Use this runbook to review Azure costs for the shared portfolio environment, investigate resource-level charges, respond to budget notifications, and handle Cost Management Query API throttling.

Important scope: the budget and cost query are scoped to Resource Group rg-portfolio. That Resource Group contains shared Project 1 and Project 2 resources. The ₹300 budget is therefore a combined Resource Group budget, not an isolated Project 2 budget.

## 2. Configured budget

| Setting | Value |
|---|---|
| Budget | portfolio-monthly-budget |
| Scope | Resource Group rg-portfolio |
| Amount | ₹300 per month |
| Budget period | 1 November 2026 – 31 October 2027 |
| Actual-spend notifications | 50%, 80%, 100% |
| Forecast notification | 100% |
| Action Group | ag-portfolio-failures |

Budget alerts notify; they do not stop, throttle or automatically delete resources. A notification is a prompt to investigate, not proof that a spend limit has been enforced.

## 3. Cost data sources

The primary Azure Monitor Workbook is defined in docs/workbook/workbook.json.

- Azure Daily Cost Trend calls the Azure Resource Manager Cost Management Query API at Resource Group scope. It queries ActualCost, MonthToDate, daily granularity, sums PreTaxCost, and groups by ResourceId and ServiceName (the Query API supports up to two group-by clauses).
- Azure Cost by Resource and Azure Cost by Service reuse the same daily result through Workbook Merge components. The service chart groups the returned rows by ServiceName; it does not issue a second Cost Management query.
- The Project 1 Function App cost cache is a separate supporting path. The shared Function App's daily timer refreshes a snapshot into the private project2-cost-cache/cost-analytics.json blob at 02:30 UTC. The cache includes month-to-date totals, daily costs and per-resource totals. The cache is read through the Function-key-protected GET /api/cost-analytics endpoint. The protected POST /api/cost-cache-refresh operation is intended for controlled administrative use.
- The workbook's current Cost Management panels query ARM directly; they do not call the Function App cache endpoint. Do not assume the workbook is displaying the cached snapshot.

The cache refresh code checks whether a snapshot has already been generated on the current UTC date. A failed refresh preserves the last good snapshot instead of overwriting it with an empty or partial result.

## 4. Resource-level cost review

### Azure Portal

1. Open Cost Management + Billing → Cost analysis.
2. Select the subscription and filter Scope to Resource Group rg-portfolio.
3. Select the Month-to-date date range and Actual cost.
4. Group by Resource.
5. Confirm the currency, reporting period and latest available usage date.
6. Identify the largest resources and compare them with the architecture and expected workload.
7. Record both the amount and reporting date. Cost data is delayed; do not treat today's partial usage as a final month-end amount.

The Resource Group contains both portfolio projects and shared services. Attribute charges to Project 1, Project 2 or shared infrastructure before making project-specific savings claims.

### Read the already-generated daily cache

From the Project 2 repository root, run:

~~~bash
python scripts/read_cost_cache.py
~~~

The script obtains a Function App key through the signed-in Azure CLI session, calls only the read-only GET /api/cost-analytics endpoint, and prints the snapshot timestamp, reporting period, currency, month-to-date total and resource-level amounts. It does not invoke Cost Management or refresh the cache. It never prints the key.

If Azure CLI is not signed in, run az login and select the intended subscription before using the script. If the cache returns 503, no snapshot has been generated. If it returns 401/403, stop and verify the function key retrieval and endpoint authorization; do not paste a key into chat or a shell command that will be saved in history.

## 5. Cost Management Query API throttling (HTTP 429)

Cost Management may return HTTP 429 when query-processing-unit quotas are exhausted. Microsoft documents the response header x-ms-ratelimit-microsoft.costmanagement-qpu-retry-after; wait for the specified number of seconds before retrying. A generic Retry-After header may also be returned.

Operational guidance:

1. Do not repeatedly refresh the workbook cost panel while investigating a 429 response.
2. Capture the HTTP status and retry-after value without logging authorization headers or tokens.
3. Wait for the service-provided back-off period before a retry.
4. Cost data is refreshed by Azure as usage arrives; Microsoft recommends calling the Cost Management APIs no more than once per day because more frequent calls do not provide fresher data.
5. Prefer the existing daily cache for an immediate read-only review. Do not manually trigger an additional refresh if today's scheduled refresh already completed.
6. The timer function retries throttled requests using the QPU retry-after header and preserves the prior snapshot if refresh ultimately fails.

A 429 response is a throttling signal, not evidence that the subscription has no cost data. A stale cached snapshot must be labelled with its generation timestamp; do not describe it as current.

## 6. Investigation and savings checklist

For each resource with non-zero cost:

- Confirm the resource is required by Project 1, Project 2 or both.
- Check whether it is a shared service before assigning the charge to one project.
- Review the SKU, region, capacity and retention settings.
- Check whether the resource is idle or can be safely stopped/deleted.
- Check logs, metrics and alerts before reducing retention or monitoring frequency.
- Avoid changing the shared Function App, Cosmos DB, runtime storage or Static Web App as part of a Project 2-only cleanup.
- Record a proposed saving separately from a verified saving. A recommendation is not a realized cost reduction until the change has been applied and the next cost data confirms it.

## 7. Incident closure criteria

A cost-review task can be closed when:

- A successful cost dataset is available and its generation/reporting dates are recorded.
- Currency and month-to-date total are identified.
- Resource-level rows are reviewed and shared resources are labelled correctly.
- The configured budget and alert thresholds are verified.
- Any proposed savings are documented with impact and risk.
- No unresolved 429 or stale-cache condition is misrepresented as a completed review.

## 8. References

- [Microsoft: Manage Azure costs with automation — data latency, QPU quotas and retry-after headers](https://learn.microsoft.com/azure/cost-management-billing/costs/manage-automation)
- [Microsoft: Cost Management Query — Usage REST API](https://learn.microsoft.com/rest/api/cost-management/query/usage)
