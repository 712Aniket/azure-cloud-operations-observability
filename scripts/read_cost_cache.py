#!/usr/bin/env python3
"""Read the existing daily Project 2 cost snapshot without querying Cost Management."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone

import requests

RESOURCE_GROUP = "rg-portfolio"
FUNCTION_APP = "aniket-portfolio-api"
FUNCTION_BASE = "https://aniket-portfolio-api.azurewebsites.net"
ENDPOINT = f"{FUNCTION_BASE}/api/cost-analytics"


def run_az(*args: str) -> str:
    completed = subprocess.run(
        ["az", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=45,
    )
    return completed.stdout.strip()


def get_function_key() -> str:
    raw = run_az(
        "functionapp", "keys", "list",
        "--resource-group", RESOURCE_GROUP,
        "--name", FUNCTION_APP,
        "--output", "json",
    )
    data = json.loads(raw)
    candidates = [
        data.get("functionKeys", {}).get("default"),
        data.get("functionKeys", {}).get("defaultFunctionKey"),
        data.get("masterKey"),
    ]
    key = next((value for value in candidates if isinstance(value, str) and value), None)
    if not key:
        raise RuntimeError(
            "Azure CLI returned no usable default Function key. "
            "Check Function App key permissions; do not paste a key into chat."
        )
    return key


def main() -> int:
    try:
        subscription = run_az("account", "show", "--query", "id", "--output", "tsv")
        if not subscription:
            raise RuntimeError("No Azure subscription selected. Run az login and select the intended subscription.")

        key = get_function_key()
        response = requests.get(
            ENDPOINT,
            params={"code": key},
            headers={"Accept": "application/json"},
            timeout=(10, 30),
        )

        if response.status_code in (401, 403):
            raise RuntimeError(
                f"Cost cache endpoint returned HTTP {response.status_code}. "
                "Stop and verify Function key permissions; the key was not displayed."
            )
        if response.status_code == 503:
            try:
                detail = response.json().get("message", "Cost cache is not populated.")
            except ValueError:
                detail = "Cost cache is not populated."
            raise RuntimeError(f"HTTP 503: {detail}")
        response.raise_for_status()

        snapshot = response.json()
        generated_text = snapshot.get("generatedAtUtc")
        if not generated_text:
            raise RuntimeError("Cache response is missing generatedAtUtc; refusing to call it a verified snapshot.")

        generated = datetime.fromisoformat(generated_text.replace("Z", "+00:00"))
        if generated.tzinfo is None:
            generated = generated.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600

        summary = snapshot.get("summary", {})
        resource_costs = snapshot.get("resourceCosts", [])
        print("PROJECT 2 / SHARED RESOURCE GROUP COST SNAPSHOT")
        print(f"Subscription: {subscription}")
        print(f"Resource group: {snapshot.get('resourceGroup', RESOURCE_GROUP)}")
        print(f"Generated (UTC): {generated.isoformat()}")
        print(f"Snapshot age: {age_hours:.1f} hours")
        print(f"Reporting period: {snapshot.get('periodStart')} to {snapshot.get('periodEnd')}")
        print(f"Month-to-date total: {summary.get('monthToDateCost')} {summary.get('currency', snapshot.get('currency', ''))}")
        print(f"Resources with charges: {summary.get('resourceCount', len(resource_costs))}")
        print("\nRESOURCE BREAKDOWN (highest first)")
        print(f"{'Resource':48} {'Cost':>16} {'Currency':>10}")
        print("-" * 78)
        for row in sorted(resource_costs, key=lambda item: float(item.get("cost") or 0), reverse=True):
            print(
                f"{str(row.get('resourceName', 'Unknown'))[:48]:48} "
                f"{float(row.get('cost') or 0):16.4f} "
                f"{str(row.get('currency', snapshot.get('currency', ''))):>10}"
            )
        if age_hours > 30:
            print("\nWARNING: Snapshot is older than 30 hours. Treat it as stale and do not use it as current cost evidence.")
        print("\nRead-only operation completed. No Cost Management query or refresh was triggered.")
        print("Scope includes shared Project 1 and Project 2 resources in rg-portfolio.")
        return 0

    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip().splitlines()
        safe_detail = detail[-1] if detail else "Azure CLI command failed."
        print(f"ERROR: Azure CLI operation failed: {safe_detail}", file=sys.stderr)
        print("The Function key and access token were not printed.", file=sys.stderr)
        return 2
    except (requests.RequestException, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
