#!/usr/bin/env python3
"""Close only the Project 2 items completed by the operational-readiness work.

The script changes nine existing work items; it never creates, deletes or
re-parents records. Run without --apply to preview. It appends a visible,
rerun-safe description section and sets state to Closed after strict checks.
"""
from __future__ import annotations

import argparse
import html
import sys
import time
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import AZDO_ORG, AZDO_PROJECT, AZDO_PAT  # noqa: E402

API_VERSION = "7.1"
BASE_URL = f"https://dev.azure.com/{AZDO_ORG}"
PROJECT_URL = requests.utils.quote(AZDO_PROJECT, safe="")
SESSION = requests.Session()
SESSION.auth = HTTPBasicAuth("", AZDO_PAT)
SESSION.headers.update({"Accept": "application/json"})

# id: expected type, exact title, current state, expected parent id or None, closure note
CLOSURES = {
    1: (
        "Epic", "Azure Infrastructure Foundation", "Active", None,
        "The existing Azure platform foundation and access/identity work has been implemented and reconciled. "
        "The network-infrastructure feature was assessed against the current public Flex Consumption serverless "
        "architecture and formally scoped as not required for this baseline. No VNet, subnet, NSG, NAT Gateway "
        "or private endpoint deployment is claimed. The decision and triggers for reconsideration are in "
        "docs/runbooks/networking-scope.md. Shared Project 1 resources are retained."
    ),
    11: (
        "Feature", "Azure Network Infrastructure", "New", 1,
        "Scope assessment completed. A dedicated VNet/subnet/private endpoint is not required for the current "
        "public portfolio API baseline. The application has public visitor ingress and no documented private-only "
        "dependency requirement. This is a completed architecture decision, not a deployed network. Reopen if "
        "private endpoints, restricted dependencies, or controlled egress become requirements. See "
        "docs/runbooks/networking-scope.md."
    ),
    18: (
        "User Story", "Design and configure the required network infrastructure", "New", 11,
        "Reviewed inbound and outbound network requirements for the public serverless API. No requirement for a "
        "dedicated VNet or subnet was identified in the current scope. The design decision and future triggers "
        "are documented in docs/runbooks/networking-scope.md. No VNet deployment is claimed."
    ),
    19: (
        "Task", "Define network and subnet requirements", "New", 18,
        "Completed the requirements assessment. A dedicated integration subnet is not required in the present "
        "baseline because no private endpoint, network-restricted dependency or forced-egress policy is in scope. "
        "Flex Consumption supports VNet integration if a future private-network requirement is approved. "
        "See docs/runbooks/networking-scope.md."
    ),
    20: (
        "Task", "Configure and validate network resources", "New", 18,
        "No dedicated VNet, subnet, NSG, NAT Gateway or private endpoint was provisioned because the current "
        "public API architecture does not require one. Existing HTTPS, managed identity, Cosmos DB Entra ID "
        "authorization and firewall controls remain in place. This task is closed as not required for the "
        "approved baseline, not as a claim that network resources were deployed."
    ),
    9: (
        "Epic", "Documentation & Runbooks", "Active", None,
        "The operational documentation scope has been delivered: the repository now has an indexed six-runbook "
        "set covering API failures, availability, Application Insights, cost/429 throttling, Terraform deployment/"
        "state recovery, and networking scope. The canonical entry point is docs/runbooks/README.md. "
        "The separate resource-level cost review remains open under Cost Management."
    ),
    57: (
        "Feature", "Operational Documentation", "Active", 9,
        "Completed the operational runbook set and its index. The set covers API failure response, availability "
        "recovery, Application Insights/KQL investigations, Cost Management and HTTP 429 handling, Terraform "
        "deployment/state recovery, and the networking-scope decision. See docs/runbooks/README.md."
    ),
    58: (
        "User Story", "Document infrastructure operations and troubleshooting", "Active", 57,
        "The operational procedures, safety boundaries, diagnostics, recovery steps and incident closure criteria "
        "are documented in docs/runbooks/. The resource-level cost analysis remains a separate open work item and "
        "is not represented as completed by this documentation closure."
    ),
    60: (
        "Task", "Create an operational troubleshooting runbook", "Active", 58,
        "Completed the runbook deliverable. The indexed procedures cover API 5xx failures, availability incidents, "
        "Application Insights and KQL, Cost Management/HTTP 429 throttling, Terraform deployment and state recovery, "
        "and the network architecture scope decision. See docs/runbooks/README.md."
    ),
}

MARKER = "Project2ClosureUpdate2026-11-24"


def request(method: str, url: str, **kwargs) -> requests.Response:
    last_error = None
    for attempt in range(5):
        try:
            response = SESSION.request(method, url, timeout=(15, 60), **kwargs)
            if response.status_code == 429 or response.status_code in (500, 502, 503, 504):
                delay = min(2 ** attempt * 2, 30)
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
            time.sleep(min(2 ** attempt * 2, 30))
    if last_error:
        raise last_error
    raise RuntimeError(f"{method} {url} failed after retries.")


def fetch_work_items(ids: list[int]) -> dict[int, dict]:
    result = {}
    for offset in range(0, len(ids), 200):
        batch = ids[offset:offset + 200]
        response = request(
            "GET",
            f"{BASE_URL}/_apis/wit/workitems",
            params={
                "ids": ",".join(map(str, batch)),
                "$expand": "Relations",
                "api-version": API_VERSION,
            },
        )
        for item in response.json().get("value", []):
            result[int(item["id"])] = item
    return result


def parent_id(item: dict) -> int | None:
    for relation in item.get("relations", []):
        if relation.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
            return int(relation["url"].rstrip("/").split("/")[-1])
    return None


def progress_html(note: str) -> str:
    safe = html.escape(note, quote=False)
    return (
        f"<p><strong>{MARKER}</strong></p>"
        f"<h3>Operational completion update — 24 November 2026</h3>"
        f"<p>{safe}</p>"
        "<p>Evidence: see the linked operational runbooks in the Project 2 GitHub repository.</p>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the verified closures.")
    args = parser.parse_args()

    if not all((AZDO_ORG, AZDO_PROJECT, AZDO_PAT)):
        raise SystemExit("Missing Azure Boards settings. Check the untracked local .env file.")

    print(f"Reading Azure Boards project '{AZDO_PROJECT}' in organization '{AZDO_ORG}'...")
    items = fetch_work_items(list(CLOSURES))
    if set(items) != set(CLOSURES):
        missing = sorted(set(CLOSURES) - set(items))
        raise SystemExit(f"Preflight failed. Missing expected work item IDs: {missing}")

    actions = []
    for item_id, (expected_type, expected_title, expected_state, expected_parent, note) in CLOSURES.items():
        item = items[item_id]
        fields = item["fields"]
        actual_type = fields.get("System.WorkItemType")
        actual_title = fields.get("System.Title", "").strip()
        actual_state = fields.get("System.State")
        actual_parent = parent_id(item)

        if actual_type != expected_type or actual_title != expected_title:
            raise SystemExit(
                f"Preflight failed for #{item_id}: type/title mismatch "
                f"({actual_type!r}, {actual_title!r}). No changes made."
            )
        if actual_parent != expected_parent:
            raise SystemExit(
                f"Preflight failed for #{item_id}: parent {actual_parent}, "
                f"expected {expected_parent}. No changes made."
            )
        if actual_state not in (expected_state, "Closed"):
            raise SystemExit(
                f"Preflight failed for #{item_id}: state is {actual_state!r}, "
                f"expected {expected_state!r} or 'Closed'. No changes made."
            )

        description = fields.get("System.Description") or ""
        already_documented = MARKER in description
        needs_state = actual_state != "Closed"
        actions.append({
            "id": item_id,
            "type": expected_type,
            "title": expected_title,
            "state": actual_state,
            "needs_state": needs_state,
            "needs_description": not already_documented,
            "note": note,
            "description": description,
        })

    print(f"Preflight passed: {len(items)} IDs, exact titles/types, expected parent links and current states.")
    print("\nClosure preview:")
    for x in actions:
        flags = []
        if x["needs_state"]:
            flags.append("state -> Closed")
        if x["needs_description"]:
            flags.append("append scope/evidence description")
        if not flags:
            flags.append("already complete; skip")
        print(f"  #{x['id']} [{x['type']}] {x['title']}: {', '.join(flags)}")

    if not args.apply:
        print("\nPREVIEW ONLY. No Azure Boards changes were made. Re-run with --apply to close these verified items.")
        return 0

    print("\nApplying closure updates. No work items will be created, deleted or re-parented.")
    for x in actions:
        if not x["needs_state"] and not x["needs_description"]:
            print(f"SKIPPED #{x['id']}: already documented and Closed")
            continue

        patch = []
        if x["needs_description"]:
            patch.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": x["description"] + progress_html(x["note"]),
            })
        if x["needs_state"]:
            patch.append({
                "op": "add",
                "path": "/fields/System.State",
                "value": "Closed",
            })

        request(
            "PATCH",
            f"{BASE_URL}/{PROJECT_URL}/_apis/wit/workitems/{x['id']}",
            params={"api-version": API_VERSION},
            json=patch,
            headers={"Content-Type": "application/json-patch+json"},
        )
        print(f"UPDATED #{x['id']} -> Closed: {x['title']}")

    print("\nVerifying saved fields...")
    verified = fetch_work_items(list(CLOSURES))
    issues = []
    for item_id, (expected_type, expected_title, _, expected_parent, _) in CLOSURES.items():
        item = verified.get(item_id)
        if not item:
            issues.append(f"#{item_id}: missing after update")
            continue
        fields = item["fields"]
        if fields.get("System.State") != "Closed":
            issues.append(f"#{item_id}: state is {fields.get('System.State')!r}")
        if MARKER not in (fields.get("System.Description") or ""):
            issues.append(f"#{item_id}: closure description marker missing")
        if fields.get("System.WorkItemType") != expected_type or fields.get("System.Title", "").strip() != expected_title:
            issues.append(f"#{item_id}: type/title changed unexpectedly")
        if parent_id(item) != expected_parent:
            issues.append(f"#{item_id}: parent changed unexpectedly")

    if issues:
        print("Verification found issues:")
        for issue in issues:
            print("  " + issue)
        return 2

    print(f"Verification successful: all {len(CLOSURES)} selected work items are Closed and documented.")
    print("Only the specified existing work items were updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
