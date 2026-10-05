# Connection Permission Validation

Shift-left CI gate that fails a PR when the deployment **service principal (SP)**
does not have a usable role on a Fabric **connection** referenced by the repo's
items. Without it, this only surfaces later as a `deploy.py` bind failure in CD.

## What it checks

1. **Discover** – scans the repo's Fabric item JSON definitions (e.g.
   `pipeline-content.json`) and collects connection GUIDs found under the keys
   `connection`, `connectionId`, `datasourceId`, `connectionName`.
2. **Resolve** – if a `parameter.yml` exists, applies its `find_replace` mapping
   for the **target environment** so the check targets the connection that will
   actually be bound (fabric-cicd swaps connection GUIDs per environment).
3. **Authenticate** – obtains a token as the SP (`client_credentials`).
4. **Authorize** – calls
   `GET /v1/connections/{id}/roleAssignments` and confirms the SP's object ID has
   `Owner`, `User`, or `UserWithReshare`. Anything else (or `403/404`) fails.

## Required pipeline variables

In the **service principal variable group**:

| Variable               | Meaning                                                        |
| ---------------------- | -------------------------------------------------------------- |
| `AZURE_CLIENT_ID`      | App (client) ID of the SP.                                     |
| `AZURE_CLIENT_SECRET`  | Client secret (mark as secret).                                |
| `AZURE_TENANT_ID`      | Tenant ID.                                                     |
| `SP_OBJECT_ID`         | **Object ID** of the SP enterprise app — the principal ID that |
|                        | appears in connection role assignments. NOT the client ID.    |

> Get `SP_OBJECT_ID` with:
> `az ad sp show --id <AZURE_CLIENT_ID> --query id -o tsv`

## Run locally

```bash
export AZURE_CLIENT_ID=...    AZURE_CLIENT_SECRET=...
export AZURE_TENANT_ID=...    SP_OBJECT_ID=...
py -3.11 connection_permission_validation.py --repo_dir <path-to-source-repo> --environment DEV
```

Exit `0` = all referenced connections OK · Exit `1` = one or more missing.

## Caveats

- Discovery relies on the connection reference keys above. If an item type stores
  its connection under a different key, add it to `CONNECTION_KEYS` in the script.
- For PRs into `dev`/`main`, accuracy depends on `parameter.yml` being present and
  mapping each connection GUID for that environment. Without it, the raw (dev)
  GUIDs are checked and a warning is printed.
