# Project 2 Primary Workbook

- Primary workbook name: **Azure Cloud Operations & Observability Platform**
- Primary workbook resource ID: `43a2aae2-21ba-417a-9a09-409792adcd64`
- Retired/rollback workbook ID: `28236c19-2756-48f5-8e4e-a176a4a8210d` (not a deployment target)
- Canonical local source: `docs/workbook/workbook.json`
- The local JSON was exported from the saved Azure Portal primary-candidate workbook.

## Deployment

From the repository root:

```bash
python scripts/deploy_workbook.py          # read-only preflight
python scripts/deploy_workbook.py --deploy # deploy the exact local JSON to the primary ID
```

The deployment script does not generate or inject snapshots, does not rewrite workbook content, and refuses unexpected workbook IDs or component layouts. The former `p2_create_preview_single_scroll.py` is deprecated and intentionally disabled.

GitHub synchronization is a separate step; no commit or push is performed by the deployment script.
