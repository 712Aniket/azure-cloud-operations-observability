import requests
from requests.auth import HTTPBasicAuth

from config import AZDO_ORG, AZDO_PROJECT, AZDO_PAT

url = f"https://dev.azure.com/{AZDO_ORG}/{requests.utils.quote(AZDO_PROJECT, safe='')}/_apis/wit/wiql"

query = {
    "query": f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = '{AZDO_PROJECT}'
        ORDER BY [System.Id]
    """
}

params = {
    "api-version": "7.1"
}

try:
    response = requests.post(
        url,
        params=params,
        json=query,
        auth=HTTPBasicAuth("", AZDO_PAT),
        timeout=30
    )

    response.raise_for_status()

    data = response.json()
    work_items = data.get("workItems", [])

    print("Azure DevOps connection successful!")
    print(f"Organization: {AZDO_ORG}")
    print(f"Project: {AZDO_PROJECT}")
    print(f"Existing work items found: {len(work_items)}")

except requests.exceptions.HTTPError:
    print(f"Azure DevOps returned HTTP {response.status_code}.")
    print(response.text[:500])

except requests.exceptions.RequestException as error:
    print(f"Connection error: {error}")