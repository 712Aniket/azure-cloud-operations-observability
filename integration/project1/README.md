# Dynamic Portfolio Analytics Endpoint

Copy `portfolio_analytics_endpoint.py` into the existing Project 1 `api/` folder.

At the bottom of Project 1 `api/function_app.py`, after the existing `container` is created, add:

```python
from portfolio_analytics_endpoint import create_portfolio_analytics_blueprint
app.register_functions(create_portfolio_analytics_blueprint(container))
```

Then add `https://portal.azure.com` to the existing Function App CORS allowed origins using the existing deployment process. Do not use `*`. The endpoint reads existing Cosmos DB documents and returns aggregate values only; it does not write data and never returns visitor hashes. In the Workbook, trust the host `aniket-portfolio-api.azurewebsites.net` when Azure prompts.

The workbook invokes this read-only endpoint from the browser, so the route is anonymous. It exposes only aggregated portfolio counters. Do not add IP addresses, visitor hashes, or other personal data. The `https://portal.azure.com` CORS allow-list is required but is not an authentication control.

Azure Cost Management panels use the signed-in workbook viewer's ARM context. Ensure that viewer has Cost Management Reader (or equivalent read access) on the subscription or cost scope.
