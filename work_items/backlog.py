import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from requests.auth import HTTPBasicAuth

from config import AZDO_ORG, AZDO_PROJECT, AZDO_PAT

BASE_URL = f"https://dev.azure.com/{AZDO_ORG}"
PROJECT_URL = requests.utils.quote(AZDO_PROJECT, safe="")
AUTH = HTTPBasicAuth("", AZDO_PAT)
API_VERSION = "7.1"

# One implementation Feature per Epic.
# Epic 1 already has four Features, which will be preserved.
BACKLOG = {
    "Azure Infrastructure Foundation": [
        {
            "feature": "Azure Resource Group and Environment Setup",
            "story": "Establish the Azure resource group and project environment",
            "tasks": [
                "Define the resource group and deployment region",
                "Create and verify the Azure resource group",
            ],
        },
        {
            "feature": "Azure Network Infrastructure",
            "story": "Design and configure the required network infrastructure",
            "tasks": [
                "Define network and subnet requirements",
                "Configure and validate network resources",
            ],
        },
        {
            "feature": "Resource Configuration and Provisioning",
            "story": "Provision the required Azure platform resources",
            "tasks": [
                "Identify required Azure resources",
                "Deploy and validate the resources",
            ],
        },
        {
            "feature": "Infrastructure Access and Identity Management",
            "story": "Configure secure access to Azure resources",
            "tasks": [
                "Review required identities and permissions",
                "Configure and validate role assignments",
            ],
        },
    ],
    "Infrastructure as Code": [
        {
            "feature": "Terraform Infrastructure Provisioning",
            "story": "Provision Azure infrastructure using Terraform",
            "tasks": [
                "Create Terraform configuration files",
                "Run Terraform plan and validate deployment",
            ],
        }
    ],
    "Monitoring & Observability": [
        {
            "feature": "Azure Monitor Configuration",
            "story": "Configure monitoring for Azure resources",
            "tasks": [
                "Identify monitoring requirements",
                "Configure and validate Azure Monitor",
            ],
        }
    ],
    "Log Analytics": [
        {
            "feature": "Log Analytics Workspace",
            "story": "Centralize Azure resource logs",
            "tasks": [
                "Create and configure Log Analytics workspace",
                "Validate log collection and KQL queries",
            ],
        }
    ],
    "Alerting & Incident Management": [
        {
            "feature": "Azure Alert Configuration",
            "story": "Configure alerts for important infrastructure conditions",
            "tasks": [
                "Define alert conditions and thresholds",
                "Configure and test alert notifications",
            ],
        }
    ],
    "Security & Governance": [
        {
            "feature": "Azure Security Baseline",
            "story": "Establish basic security and governance controls",
            "tasks": [
                "Review resource access and security settings",
                "Apply and validate security controls",
            ],
        }
    ],
    "Cost Management": [
        {
            "feature": "Azure Cost Monitoring",
            "story": "Monitor and control project resource expenditure",
            "tasks": [
                "Configure budget and cost alerts",
                "Review resource costs and identify savings",
            ],
        }
    ],
    "CI/CD Automation": [
        {
            "feature": "Infrastructure Deployment Pipeline",
            "story": "Automate infrastructure deployment through CI/CD",
            "tasks": [
                "Create the deployment pipeline configuration",
                "Execute and validate the pipeline",
            ],
        }
    ],
    "Documentation & Runbooks": [
        {
            "feature": "Operational Documentation",
            "story": "Document infrastructure operations and troubleshooting",
            "tasks": [
                "Document architecture and deployment steps",
                "Create an operational troubleshooting runbook",
            ],
        }
    ],
}


def get_all_work_items():
    url = f"{BASE_URL}/{PROJECT_URL}/_apis/wit/wiql"

    query = {
        "query": f"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.TeamProject] = '{AZDO_PROJECT}'
        """
    }

    response = requests.post(
        url,
        params={"api-version": API_VERSION},
        json=query,
        auth=AUTH,
        timeout=30,
    )
    response.raise_for_status()

    ids = [
        str(item["id"])
        for item in response.json().get("workItems", [])
    ]

    items = {}

    # Azure DevOps supports batch retrieval.
    for start in range(0, len(ids), 200):
        batch_ids = ",".join(ids[start:start + 200])

        details = requests.get(
            f"{BASE_URL}/_apis/wit/workitems",
            params={
                "ids": batch_ids,
                "$expand": "Relations",
                "api-version": API_VERSION,
            },
            auth=AUTH,
            timeout=30,
        )
        details.raise_for_status()

        for item in details.json().get("value", []):
            fields = item["fields"]
            parent_id = None

            for relation in item.get("relations", []):
                if relation.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
                    parent_id = int(relation["url"].rstrip("/").split("/")[-1])
                    break

            items[(fields["System.WorkItemType"], parent_id,
                   fields["System.Title"])] = item["id"]

    return items


def create_work_item(item_type, title, description, parent_id):
    url = (
        f"{BASE_URL}/{PROJECT_URL}/_apis/wit/workitems/"
        f"${requests.utils.quote(item_type, safe='')}"
    )

    parent_url = f"{BASE_URL}/_apis/wit/workItems/{parent_id}"

    payload = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title,
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": description,
        },
        {
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": parent_url,
            },
        },
    ]

    response = requests.post(
        url,
        params={"api-version": API_VERSION},
        json=payload,
        headers={"Content-Type": "application/json-patch+json"},
        auth=AUTH,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()["id"]


def main():
    print("\nLoading existing Azure DevOps work items...")
    existing = get_all_work_items()

    created = 0
    skipped = 0

    for epic_title, features in BACKLOG.items():

        epic_id = existing.get(("Epic", None, epic_title))

        if not epic_id:
            print(f"\nERROR: Epic not found: {epic_title}")
            continue

        print(f"\nEPIC: {epic_title}")

        for feature_data in features:

            feature_title = feature_data["feature"]
            feature_key = ("Feature", epic_id, feature_title)

            feature_id = existing.get(feature_key)

            if feature_id:
                print(f"  EXISTS Feature: {feature_title}")
                skipped += 1
            else:
                feature_id = create_work_item(
                    "Feature",
                    feature_title,
                    f"Feature under {epic_title}.",
                    epic_id,
                )
                existing[feature_key] = feature_id
                print(f"  CREATED Feature: {feature_title} [{feature_id}]")
                created += 1

            story_title = feature_data["story"]
            story_key = ("User Story", feature_id, story_title)

            story_id = existing.get(story_key)

            if story_id:
                print(f"    EXISTS Story: {story_title}")
                skipped += 1
            else:
                story_id = create_work_item(
                    "User Story",
                    story_title,
                    f"User Story under {feature_title}.",
                    feature_id,
                )
                existing[story_key] = story_id
                print(f"    CREATED Story: {story_title} [{story_id}]")
                created += 1

            for task_title in feature_data["tasks"]:

                task_key = ("Task", story_id, task_title)

                if task_key in existing:
                    print(f"      EXISTS Task: {task_title}")
                    skipped += 1
                    continue

                task_id = create_work_item(
                    "Task",
                    task_title,
                    f"Implementation task under {story_title}.",
                    story_id,
                )

                existing[task_key] = task_id
                print(f"      CREATED Task: {task_title} [{task_id}]")
                created += 1

    print("\n========== BACKLOG SUMMARY ==========")
    print(f"Created: {created}")
    print(f"Skipped existing: {skipped}")
    print("Backlog generation completed.")


if __name__ == "__main__":
    main()