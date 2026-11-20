import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from requests.auth import HTTPBasicAuth

from config import AZDO_ORG, AZDO_PROJECT, AZDO_PAT

BASE_URL = f"https://dev.azure.com/{AZDO_ORG}"
PROJECT_URL = requests.utils.quote(AZDO_PROJECT, safe="")

PLANNED_EPICS = [
    "Azure Infrastructure Foundation",
    "Infrastructure as Code",
    "Monitoring & Observability",
    "Log Analytics",
    "Alerting & Incident Management",
    "Security & Governance",
    "Cost Management",
    "CI/CD Automation",
    "Documentation & Runbooks",
]

AUTH = HTTPBasicAuth("", AZDO_PAT)


def get_existing_epics():
    """Retrieve existing Epic titles from Azure DevOps."""

    url = f"{BASE_URL}/{PROJECT_URL}/_apis/wit/wiql"

    query = {
        "query": f"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.TeamProject] = '{AZDO_PROJECT}'
            AND [System.WorkItemType] = 'Epic'
        """
    }

    response = requests.post(
        url,
        params={"api-version": "7.1"},
        json=query,
        auth=AUTH,
        timeout=30,
    )

    response.raise_for_status()

    work_items = response.json().get("workItems", [])

    if not work_items:
        return set()

    ids = ",".join(str(item["id"]) for item in work_items)

    details_url = f"{BASE_URL}/_apis/wit/workitems"

    details_response = requests.get(
        details_url,
        params={
            "ids": ids,
            "fields": "System.Title",
            "api-version": "7.1",
        },
        auth=AUTH,
        timeout=30,
    )

    details_response.raise_for_status()

    return {
        item["fields"]["System.Title"]
        for item in details_response.json().get("value", [])
    }


def create_epic(title):
    """Create an Epic in Azure DevOps."""

    url = (
        f"{BASE_URL}/{PROJECT_URL}"
        f"/_apis/wit/workitems/$Epic"
    )

    payload = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title,
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": f"Epic for the Azure Cloud Operations & Observability Platform: {title}.",
        },
    ]

    response = requests.post(
        url,
        params={"api-version": "7.1"},
        json=payload,
        headers={"Content-Type": "application/json-patch+json"},
        auth=AUTH,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def main():
    print("\nChecking existing Azure DevOps Epics...")

    existing = get_existing_epics()

    missing = [
        epic for epic in PLANNED_EPICS
        if epic not in existing
    ]

    print(f"\nExisting Epics: {len(existing)}")
    print(f"Planned Epics: {len(PLANNED_EPICS)}")
    print(f"Missing Epics: {len(missing)}")

    if not missing:
        print("\nAll planned Epics already exist.")
        return

    print("\nCreating missing Epics...\n")

    for title in missing:
        try:
            result = create_epic(title)

            print(
                f"CREATED: {title} "
                f"(ID: {result['id']})"
            )

        except requests.exceptions.RequestException as error:
            print(f"FAILED: {title}")
            print(f"Reason: {error}")

            if error.response is not None:
                print(error.response.text[:500])

    print("\nEpic creation process completed.")

    final_epics = get_existing_epics()

    print(
        f"Verified Epics: {len(final_epics)} "
        f"/ {len(PLANNED_EPICS)}"
    )


if __name__ == "__main__":
    main()