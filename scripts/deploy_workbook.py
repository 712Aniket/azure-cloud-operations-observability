#!/usr/bin/env python3
"""Deploy the canonical Project 2 workbook to its primary Azure resource.

Source of truth: docs/workbook/workbook.json (exported from the saved Azure Portal layout).
Default invocation performs preflight only. Use --deploy to update the primary resource.
The retired workbook ID is protected and is never a deployment target.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

RESOURCE_GROUP = "rg-portfolio"
PRIMARY_WORKBOOK_ID = "43a2aae2-21ba-417a-9a09-409792adcd64"
RETIRED_WORKBOOK_ID = "28236c19-2756-48f5-8e4e-a176a4a8210d"
WORKBOOK_DISPLAY_NAME = "Azure Cloud Operations & Observability Platform"
WORKBOOK_PATH = Path("docs/workbook/workbook.json")


def az_json(args: list[str]) -> dict:
    completed = subprocess.run(["az", *args], check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def validate_workbook(workbook: dict) -> int:
    items = workbook.get("items")
    if not isinstance(items, list) or len(items) < 20:
        raise SystemExit("Preflight failed: workbook is missing or has too few components.")
    names = []
    for item in items:
        content = item.get("content", {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = {}
        names.append(item.get("name") or content.get("title") or "")
    if any(not name for name in names) or len(names) != len(set(names)):
        raise SystemExit("Preflight failed: component names are missing or duplicated.")
    required = {
        "Project 2 Overview", "Operations and Monitoring Section",
        "API Health - KPI Summary", "Portfolio Analytics Section",
        "Portfolio KPI Summary", "Visitor Geography", "Resume Analytics",
        "Certificate Analytics", "Security and Governance", "RBAC Role Assignments",
        "Azure Resource Inventory", "Monitoring Rules Inventory",
    }
    missing = sorted(required - set(names))
    if missing:
        raise SystemExit(f"Preflight failed: missing required components: {missing}")

    def has_tabs(rows: list[dict]) -> bool:
        for row in rows:
            if (row.get("conditionalVisibility") or {}).get("parameterName") == "selectedTab":
                return True
            content = row.get("content", {})
            nested = content.get("items", []) if isinstance(content, dict) else []
            if nested and has_tabs(nested):
                return True
        return False
    if has_tabs(items):
        raise SystemExit("Preflight failed: tab-based conditional visibility is present.")
    return len(items)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deploy", action="store_true", help="Update the primary Azure Workbook resource.")
    args = parser.parse_args()

    if PRIMARY_WORKBOOK_ID == RETIRED_WORKBOOK_ID:
        raise SystemExit("Safety stop: primary and retired workbook IDs must differ.")
    if not WORKBOOK_PATH.is_file():
        raise SystemExit(f"Workbook source not found: {WORKBOOK_PATH}")

    workbook = json.loads(WORKBOOK_PATH.read_text(encoding="utf-8"))
    count = validate_workbook(workbook)
    subscription = subprocess.check_output(
        ["az", "account", "show", "--query", "id", "-o", "tsv"], text=True
    ).strip()
    base = (
        f"https://management.azure.com/subscriptions/{subscription}"
        f"/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Insights/workbooks/{PRIMARY_WORKBOOK_ID}"
    )
    current = az_json([
        "rest", "--method", "get",
        "--url", base + "?api-version=2021-08-01&canFetchContent=true",
        "--output", "json",
    ])
    current_props = current.get("properties", {})
    if current_props.get("displayName") not in {
        "Portfolio Analytics Layout Preview", WORKBOOK_DISPLAY_NAME
    }:
        raise SystemExit(
            "Safety stop: primary Azure resource has an unexpected display name: "
            f"{current_props.get('displayName')!r}"
        )

    print("PRIMARY WORKBOOK PREFLIGHT: PASS")
    print("Target ID:", PRIMARY_WORKBOOK_ID)
    print("Current Azure name:", current_props.get("displayName"))
    print("Target display name:", WORKBOOK_DISPLAY_NAME)
    print("Components:", count)
    print("Source:", WORKBOOK_PATH)
    print("Retired workbook (protected):", RETIRED_WORKBOOK_ID)
    print("Production/retired resource: NOT targeted")

    if not args.deploy:
        print("\nPreflight only. No Azure resources changed. Add --deploy to apply this exact local workbook.")
        return

    payload = {
        "location": current.get("location", "centralindia"),
        "kind": current.get("kind", "shared"),
        "properties": {
            "displayName": WORKBOOK_DISPLAY_NAME,
            "description": (
                "Primary Azure Cloud Operations & Observability Platform workbook. "
                "The serialized dashboard layout is sourced from the approved Azure Portal export."
            ),
            "category": current_props.get("category", "workbook"),
            "version": workbook.get("version", "Notebook/1.0"),
            "sourceId": current_props.get("sourceId", f"/subscriptions/{subscription}/resourceGroups/{RESOURCE_GROUP}"),
            "serializedData": json.dumps(workbook, separators=(",", ":"), ensure_ascii=False),
        },
    }
    payload_path = Path("/tmp/project2-primary-workbook-payload.json")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    put_url = base + "?api-version=2023-06-01"
    subprocess.run([
        "az", "rest", "--method", "put", "--url", put_url,
        "--body", f"@{payload_path}", "--output", "none",
    ], check=True)

    verify = az_json([
        "rest", "--method", "get",
        "--url", base + "?api-version=2021-08-01&canFetchContent=true",
        "--output", "json",
    ])
    props = verify.get("properties", {})
    serialized = props.get("serializedData")
    if not serialized:
        raise SystemExit("Deployment verification failed: Azure returned no serializedData.")
    deployed = json.loads(serialized) if isinstance(serialized, str) else serialized
    deployed_count = validate_workbook(deployed)
    if props.get("displayName") != WORKBOOK_DISPLAY_NAME or deployed_count != count:
        raise SystemExit("Deployment verification failed: display name or component count differs.")

    print("\nPRIMARY WORKBOOK DEPLOYMENT: PASS")
    print("Name:", props.get("displayName"))
    print("ID:", PRIMARY_WORKBOOK_ID)
    print("Components:", deployed_count)
    print("Retired workbook:", RETIRED_WORKBOOK_ID, "— untouched")


if __name__ == "__main__":
    main()
