import json
import os
import subprocess
from datetime import datetime, timezone
from collections import defaultdict

from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

SUBSCRIPTION = subprocess.check_output(
    ["az", "account", "show", "--query", "id", "-o", "tsv"],
    text=True
).strip()

ENDPOINT = os.environ["COSMOS_DB_ENDPOINT"]

RESOURCE_GROUP = "rg-portfolio"
WORKBOOK_ID = "28236c19-2756-48f5-8e4e-a176a4a8210d"

AI_ID = (
    f"/subscriptions/{SUBSCRIPTION}/resourceGroups/{RESOURCE_GROUP}"
    "/providers/Microsoft.Insights/components/aniket-portfolio-api"
)

WORKBOOK_URL = (
    f"https://management.azure.com/subscriptions/{SUBSCRIPTION}"
    f"/resourceGroups/{RESOURCE_GROUP}"
    f"/providers/Microsoft.Insights/workbooks/{WORKBOOK_ID}"
    "?api-version=2023-06-01"
)

print("Connecting to Cosmos DB...")

client = CosmosClient(
    ENDPOINT,
    credential=DefaultAzureCredential()
)

container = (
    client.get_database_client("portfolio-db")
    .get_container_client("visitor-counters")
)

def query_items(query):
    return list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))

# --------------------------------------------------
# READ EXISTING ANALYTICS
# --------------------------------------------------

total_doc = container.read_item(
    item="total",
    partition_key="total"
)

total_visitors = total_doc.get("visitor_count", 0)

countries = query_items("""
    SELECT * FROM c
    WHERE STARTSWITH(c.id, 'country-')
""")

events = query_items("""
    SELECT * FROM c
    WHERE STARTSWITH(c.id, 'analytics-')
""")

engagement = query_items("""
    SELECT * FROM c
    WHERE STARTSWITH(c.id, 'engagement-')
""")

print("Cosmos DB data retrieved successfully.")

# --------------------------------------------------
# AGGREGATE PORTFOLIO ANALYTICS
# --------------------------------------------------

event_summary = defaultdict(int)

for item in events:
    key = (
        item.get("item_type", ""),
        item.get("item_id", ""),
        item.get("event_type", "")
    )
    event_summary[key] += item.get("event_count", 0)

resume_views = event_summary[("resume", "resume", "view")]
resume_downloads = event_summary[("resume", "resume", "download")]

certificate_views = sum(
    value for (kind, _, event), value in event_summary.items()
    if kind == "certificate" and event == "view"
)

certificate_downloads = sum(
    value for (kind, _, event), value in event_summary.items()
    if kind == "certificate" and event == "download"
)

sessions = 0
active_seconds = 0
likes = 0

sections = defaultdict(lambda: {"views": 0, "seconds": 0})

for item in engagement:

    metric = item.get("metric_type")

    if metric == "session":
        sessions += item.get("session_count", 0)
        active_seconds += item.get("total_active_seconds", 0)

    elif metric == "section":
        section = item.get("section_id", "unknown")
        sections[section]["views"] += item.get("view_count", 0)
        sections[section]["seconds"] += item.get(
            "total_active_seconds", 0
        )

    elif metric == "like":
        likes += 1

timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# --------------------------------------------------
# AZURE COST MANAGEMENT
# --------------------------------------------------

cost_query = {
    "type": "ActualCost",
    "timeframe": "MonthToDate",
    "dataset": {
        "granularity": "Daily",
        "aggregation": {
            "totalCost": {
                "name": "PreTaxCost",
                "function": "Sum"
            }
        },
        "grouping": [
            {
                "type": "Dimension",
                "name": "ResourceGroupName"
            }
        ]
    }
}

cost_error = None
daily_costs = []
month_to_date_cost = 0.0
cost_currency = "INR"

try:
    cost_response = json.loads(subprocess.check_output(
        [
            "az", "rest",
            "--method", "post",
            "--url",
            f"https://management.azure.com/subscriptions/{SUBSCRIPTION}/providers/Microsoft.CostManagement/query?api-version=2025-03-01",
            "--body", json.dumps(cost_query),
            "--output", "json"
        ],
        text=True
    ))

    cost_properties = cost_response.get("properties", {})
    cost_columns = [
        column["name"]
        for column in cost_properties.get("columns", [])
    ]

    for row in cost_properties.get("rows", []):
        record = dict(zip(cost_columns, row))

        if record.get("ResourceGroupName") != RESOURCE_GROUP:
            continue

        amount = float(record.get("PreTaxCost", 0) or 0)
        usage_date = str(record.get("UsageDate", ""))

        if usage_date:
            usage_date = datetime.strptime(
                usage_date, "%Y%m%d"
            ).strftime("%Y-%m-%d")

        cost_currency = record.get("Currency", cost_currency)
        month_to_date_cost += amount

        daily_costs.append({
            "date": usage_date,
            "cost": amount
        })

    daily_costs.sort(key=lambda item: item["date"])

    print(
        f"Azure cost data retrieved: "
        f"{cost_currency} {month_to_date_cost:.2f}"
    )

except Exception as exc:
    cost_error = str(exc)
    print(f"WARNING: Azure cost data unavailable: {cost_error}")



# --------------------------------------------------
# BUILD ANALYTICS SNAPSHOT
# --------------------------------------------------

lines = [
    "## Portfolio Analytics",
    "",
    f"**Data snapshot:** {timestamp}",
    "",
    "| KPI | Value |",
    "|---|---:|",
    f"| Total visitors | {total_visitors:,} |",
    f"| Countries represented | {len(countries)} |",
    f"| Resume views | {resume_views} |",
    f"| Resume downloads | {resume_downloads} |",
    f"| Certificate views | {certificate_views} |",
    f"| Certificate downloads | {certificate_downloads} |",
    f"| Portfolio sessions | {sessions} |",
    f"| Active time | {active_seconds // 60} min {active_seconds % 60} sec |",
    f"| Appreciations | {likes} |",
    "",
    "### Visitor Geography",
    "",
    "| Country | Visitors |",
    "|---|---:|"
]

for country in sorted(
    countries,
    key=lambda x: x.get("visitor_count", 0),
    reverse=True
):
    lines.append(
        f"| {country.get('flag', '')} {country.get('country_name', 'Unknown')} "
        f"| {country.get('visitor_count', 0):,} |"
    )

lines.extend([
    "",
    "### Resume Analytics",
    "",
    "| Document | Views | Downloads |",
    "|---|---:|---:|",
    f"| Resume | {resume_views} | {resume_downloads} |",
    "",
    "### Certificate Analytics",
    "",
    "| Certificate | Views | Downloads |",
    "|---|---:|---:|"
])

certificate_ids = sorted({
    item_id for (kind, item_id, _), value in event_summary.items()
    if kind == "certificate"
})

for cert in certificate_ids:
    views = event_summary[("certificate", cert, "view")]
    downloads = event_summary[("certificate", cert, "download")]
    lines.append(f"| {cert} | {views} | {downloads} |")

lines.extend([
    "",
    "### Portfolio Engagement",
    "",
    "| Section | Views | Active seconds |",
    "|---|---:|---:|"
])

for section, metrics in sorted(sections.items()):
    lines.append(
        f"| {section.title()} | "
        f"{metrics['views']} | {metrics['seconds']} |"
    )

lines.extend([
    "",
    "### Azure Cost Visibility",
    "",
    "| Cost Metric | Value |",
    "|---|---:|"
])

if cost_error:
    lines.append("| Cost data status | Unavailable - check deployment logs |")
else:
    lines.append(
        f"| Month-to-date cost ({RESOURCE_GROUP}) "
        f"| {cost_currency} {month_to_date_cost:.2f} |"
    )
    lines.extend([
        "",
        "| Date | Daily cost |",
        "|---|---:|---:"
    ])

    for entry in daily_costs:
        lines.append(
            f"| {entry['date']} | "
            f"{cost_currency} {entry['cost']:.2f} |"
        )

lines.extend([
    "",
    "### Security and Governance",
    "",
    "- Cost data is retrieved from Azure Cost Management.",
    "- Review resource usage and monitoring retention regularly.",
    "- Budget configuration and alert thresholds: not yet configured.",
    "- CI/CD identity permissions and deployment approvals: "
    "require separate verification.",
    "",
    "> Portfolio and cost metrics are snapshots captured during "
    "workbook deployment. Run this deployment again to refresh them."
])

snapshot_item = {
    "type": 1,
    "name": "Portfolio Analytics Snapshot",
    "customWidth": "100",
    "content": {
        "json": "\n".join(lines),
        "style": "info"
    }
}

# --------------------------------------------------
# LOAD EXISTING WORKBOOK
# --------------------------------------------------

workbook_path = "docs/workbook/workbook.json"

with open(workbook_path, encoding="utf-8") as f:
    workbook = json.load(f)

# Make deployment repeatable.
workbook["items"] = [
    item for item in workbook["items"]
    if item.get("name") != "Portfolio Analytics Snapshot"
]

# Fix boolean comparison in the availability query.
for item in workbook["items"]:
    if item.get("name") == "API Availability":
        item["content"]["query"] = item["content"]["query"].replace(
            "success == 1", "success == true"
        ).replace(
            "success == 0", "success == false"
        )

# Insert snapshot after the title.
workbook["items"].insert(1, snapshot_item)

# --------------------------------------------------
# ADD LIVE AZURE RESOURCE INVENTORY
# --------------------------------------------------

def resource_query(name, title, query, width="100"):
    return {
        "type": 3,
        "name": name,
        "customWidth": width,
        "content": {
            "version": "KqlItem/1.0",
            "title": title,
            "query": query,
            "size": 0,
            "queryType": 1,
            "resourceType": "microsoft.resourcegraph/resources",
            "visualization": "table"
        }
    }

resource_query_items = [
    resource_query(
        "Azure Resource Inventory",
        "Azure Resource Inventory",
        f"""
Resources
| where subscriptionId == '{SUBSCRIPTION}'
| where resourceGroup =~ '{RESOURCE_GROUP}'
| project name, type, location, kind
| order by type asc
""".strip()
    ),
    resource_query(
        "Monitoring Rules Inventory",
        "Monitoring Rules and Health Checks",
        f"""
Resources
| where subscriptionId == '{SUBSCRIPTION}'
| where resourceGroup =~ '{RESOURCE_GROUP}'
| where type in~ (
    'microsoft.insights/scheduledqueryrules',
    'microsoft.insights/metricalerts',
    'microsoft.insights/actiongroups',
    'microsoft.insights/webtests'
)
| extend Enabled = tostring(properties.enabled)
| project name, type, location, Enabled
| order by type asc
""".strip()
    )
]

existing_names = {
    item.get("name") for item in workbook["items"]
}

for item in resource_query_items:
    if item["name"] not in existing_names:
        workbook["items"].append(item)

workbook["$schema"] = (
    "https://github.com/Microsoft/Application-Insights-Workbooks/"
    "blob/master/schema/workbook.json"
)

# --------------------------------------------------
# CREATE AZURE RESOURCE PAYLOAD
# --------------------------------------------------

resource_group_id = (
    f"/subscriptions/{SUBSCRIPTION}/resourceGroups/{RESOURCE_GROUP}"
)

payload = {
    "location": "centralindia",
    "kind": "shared",
    "properties": {
        "displayName": "Azure Cloud Operations & Observability Platform",
        "description": (
            "Portfolio analytics, application monitoring, "
            "availability, performance and operational governance."
        ),
        "category": "workbook",
        "version": "Notebook/1.0",
        "sourceId": resource_group_id,
        "serializedData": json.dumps(workbook, separators=(",", ":"))
    }
}

# Save the local source of truth.
with open(workbook_path, "w", encoding="utf-8") as f:
    json.dump(workbook, f, indent=2, ensure_ascii=False)

with open("/tmp/p2-workbook-payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f)

print("\nWorkbook prepared.")
print("Dashboard components:", len(workbook["items"]))
print("Analytics snapshot:", timestamp)

# --------------------------------------------------
# DEPLOY EXISTING AZURE WORKBOOK
# --------------------------------------------------

print("\nDeploying Azure Workbook...")

subprocess.run([
    "az", "rest",
    "--method", "put",
    "--url", WORKBOOK_URL,
    "--body", "@/tmp/p2-workbook-payload.json",
    "--output", "none"
], check=True)

print("Workbook deployment completed.")

# --------------------------------------------------
# VERIFY DEPLOYMENT
# --------------------------------------------------

WORKBOOK_GET_URL = WORKBOOK_URL.replace(
    "?api-version=2023-06-01",
    "?api-version=2021-08-01&canFetchContent=true"
)

result = subprocess.check_output([
    "az", "rest",
    "--method", "get",
    "--url", WORKBOOK_GET_URL,
    "--output", "json"
], text=True)

deployed = json.loads(result)
properties = deployed.get("properties", {})

serialized = properties.get("serializedData")

if not serialized:
    raise RuntimeError("Workbook verification failed: serializedData is empty.")

deployed_workbook = json.loads(serialized)

print("\n========== DEPLOYMENT VERIFICATION ==========")
print("Workbook:", properties.get("displayName"))
print("Category:", properties.get("category"))
print("Serialized data:", "Present")
print("Dashboard components:", len(deployed_workbook.get("items", [])))
print("Snapshot time:", timestamp)

print("\n========== GIT STATUS ==========")

subprocess.run(["git", "status", "--short"])

print("\nPROJECT 2 WORKBOOK DEPLOYMENT COMPLETED.")
