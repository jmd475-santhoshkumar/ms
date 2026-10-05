"""
Connection Permission Validation (CI gate)
==========================================

Shift-left check that the deployment service principal (SP) has a usable role on
every Fabric connection referenced by the items in the repository, BEFORE the CD
pipeline attempts to bind them. This prevents the "service principal lacks
connection permissions" failure from only surfacing during deployment.

Stages
------
1. Discover connection GUIDs from the Fabric item definitions in the repo.
2. (Optional) Resolve those GUIDs through `parameter.yml` for the target
   environment, because fabric-cicd swaps connection GUIDs per environment.
3. Authenticate as the SP (client_credentials).
4. For each connection, read its role assignments and confirm the SP has an
   acceptable role.

Exit code 0 = all good, 1 = at least one missing permission / hard error.

Environment variables (provided by the pipeline)
------------------------------------------------
AZURE_CLIENT_ID      App (client) ID of the SP.
AZURE_CLIENT_SECRET  Client secret.
AZURE_TENANT_ID      Tenant ID.
SP_OBJECT_ID         Object ID of the SP's enterprise application (the principal
                     ID that appears in connection role assignments). This is NOT
                     the same as AZURE_CLIENT_ID.
"""

import argparse
import json
import os
import re
import sys
import requests
import yaml


# Roles on a Fabric connection that allow the SP to actually use/bind it.
ACCEPTABLE_ROLES = {"owner", "user", "userwithreshare"}

# JSON keys whose values are connection / datasource references.
CONNECTION_KEYS = {"connection", "connectionid", "datasourceid", "connectionname"}

# A GUID, e.g. 3f2c1a90-1234-4abc-9def-0123456789ab
GUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

FABRIC_API = "https://api.fabric.microsoft.com/v1"


# ----------------------------------------------------------------------------
# Stage 1: discover connection references from repo item definitions
# ----------------------------------------------------------------------------
def _walk_json_for_connections(node, found):
    """Recursively collect GUIDs that sit under a known connection key."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in CONNECTION_KEYS and isinstance(value, str):
                for guid in GUID_RE.findall(value):
                    found.add(guid.lower())
            _walk_json_for_connections(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_json_for_connections(item, found)


def discover_connection_ids(repo_dir):
    """
    Scan the repo for Fabric item definition files and return a dict of
    { connection_guid: [files where it was referenced] }.

    We target the JSON files that carry connection references in fabric-cicd
    source format (pipeline-content.json, *.json item definitions). Parsing fails
    open per-file so one malformed file never blocks the whole check.
    """
    references = {}  # guid -> set(files)

    for root, _dirs, files in os.walk(repo_dir):
        # Skip VCS / CI plumbing.
        if any(part in root.lower() for part in (".git", "01_cicd_pipelines")):
            continue

        for fname in files:
            if not fname.lower().endswith(".json"):
                continue

            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8-sig") as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                # Not a clean JSON item definition; skip quietly.
                continue

            found = set()
            _walk_json_for_connections(data, found)
            for guid in found:
                references.setdefault(guid, set()).add(
                    os.path.relpath(fpath, repo_dir)
                )

    # Convert sets to sorted lists for stable output.
    return {guid: sorted(files) for guid, files in references.items()}


# ----------------------------------------------------------------------------
# Stage 2: resolve source GUIDs to the target-environment GUIDs via parameter.yml
# ----------------------------------------------------------------------------
def build_parameter_map(repo_dir, environment):
    """
    Read fabric-cicd `parameter.yml` (if present) and build a mapping of
    source GUID -> environment-specific GUID for `find_replace` entries.

    Supports both schema styles:

      # list style (newer)
      find_replace:
        - find_value: "<dev-guid>"
          replace_value:
            DEV: "<dev-guid>"
            PROD: "<prod-guid>"

      # mapping style (older)
      find_replace:
        "<dev-guid>":
          PROD: "<prod-guid>"

    Returns {} if there is no parameter file (then we check the raw GUIDs as-is).
    """
    env = (environment or "").upper()
    mapping = {}

    candidates = [
        os.path.join(repo_dir, "parameter.yml"),
        os.path.join(repo_dir, "parameter.yaml"),
    ]
    param_file = next((c for c in candidates if os.path.isfile(c)), None)
    if not param_file:
        return mapping

    try:
        with open(param_file, "r", encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
    except (yaml.YAMLError, OSError) as exc:
        print(f"WARNING: could not parse {param_file}: {exc}")
        return mapping

    find_replace = doc.get("find_replace")
    if not find_replace:
        return mapping

    def _add(find_value, replace_value):
        if not isinstance(find_value, str):
            return
        for guid in GUID_RE.findall(find_value):
            if isinstance(replace_value, dict):
                target = replace_value.get(env)
                if target:
                    mapping[guid.lower()] = str(target).lower()

    if isinstance(find_replace, list):
        for entry in find_replace:
            if isinstance(entry, dict):
                _add(entry.get("find_value"), entry.get("replace_value"))
    elif isinstance(find_replace, dict):
        for find_value, replace_value in find_replace.items():
            _add(find_value, replace_value)

    return mapping


def resolve_for_environment(references, param_map):
    """Apply the parameter map so we check the connection that will actually bind."""
    resolved = {}
    for guid, files in references.items():
        target = param_map.get(guid, guid)
        resolved.setdefault(target, set()).update(files)
    return {guid: sorted(files) for guid, files in resolved.items()}


# ----------------------------------------------------------------------------
# Stage 3: authenticate as the service principal
# ----------------------------------------------------------------------------
def get_access_token(client_id, client_secret, tenant_id):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://api.fabric.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    resp = requests.post(token_url, data=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["access_token"]


# ----------------------------------------------------------------------------
# Stage 4: check the SP role on each connection
# ----------------------------------------------------------------------------
def get_sp_role_on_connection(connection_id, sp_object_id, headers):
    """
    Return the SP's role (lowercased) on the connection, or None if the SP has no
    role assignment. Raises a special marker string for access errors so the
    caller can report them distinctly.
    """
    url = f"{FABRIC_API}/connections/{connection_id}/roleAssignments"

    while url:
        resp = requests.get(url, headers=headers, timeout=60)

        if resp.status_code in (403, 404):
            # The SP cannot even read the connection's role assignments, which
            # itself means it does not have access to the connection.
            return "__no_access__"

        resp.raise_for_status()
        body = resp.json()

        for assignment in body.get("value", []):
            principal = assignment.get("principal", {}) or {}
            if str(principal.get("id", "")).lower() == sp_object_id.lower():
                return str(assignment.get("role", "")).lower()

        # Pagination
        token = body.get("continuationToken")
        url = (
            f"{FABRIC_API}/connections/{connection_id}/roleAssignments"
            f"?continuationToken={token}"
            if token
            else None
        )

    return None


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Validate that the deployment SP has permission on every "
        "Fabric connection referenced by the repo items."
    )
    parser.add_argument("--repo_dir", required=True, help="Root of the source repo")
    parser.add_argument(
        "--environment",
        default="",
        help="Target environment (DEV/PROD). Used to resolve parameter.yml.",
    )
    args = parser.parse_args()

    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    sp_object_id = os.getenv("SP_OBJECT_ID")

    missing_env = [
        name
        for name, val in {
            "AZURE_CLIENT_ID": client_id,
            "AZURE_CLIENT_SECRET": client_secret,
            "AZURE_TENANT_ID": tenant_id,
            "SP_OBJECT_ID": sp_object_id,
        }.items()
        if not val
    ]
    if missing_env:
        print(f"Error: missing required environment variables: {', '.join(missing_env)}")
        sys.exit(1)

    print("======================================")
    print("CONNECTION PERMISSION VALIDATION")
    print("======================================")
    print(f"Repo dir    : {args.repo_dir}")
    print(f"Environment : {args.environment or '(raw / unresolved)'}")
    print("")

    # Stage 1
    references = discover_connection_ids(args.repo_dir)
    if not references:
        print("OK No connection references found in repo items. Nothing to validate.")
        sys.exit(0)

    # Stage 2
    param_map = build_parameter_map(args.repo_dir, args.environment)
    if param_map:
        references = resolve_for_environment(references, param_map)
        print(f"Applied parameter.yml mapping for '{args.environment}'.")
    elif args.environment:
        print(
            "WARNING: no parameter.yml mapping applied; checking the raw GUIDs from "
            "the repo. These are accurate only for a DEV-targeted PR."
        )
    print(f"Discovered {len(references)} unique connection(s) to validate.\n")

    # Stage 3
    try:
        access_token = get_access_token(client_id, client_secret, tenant_id)
    except requests.RequestException as exc:
        print(f"Error: failed to obtain access token: {exc}")
        sys.exit(1)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Stage 4
    failures = []
    for connection_id, files in sorted(references.items()):
        referenced_by = ", ".join(files)
        try:
            role = get_sp_role_on_connection(connection_id, sp_object_id, headers)
        except requests.RequestException as exc:
            failures.append((connection_id, referenced_by, f"API error: {exc}"))
            print(f"[FAIL] {connection_id} -> API error: {exc}")
            continue

        if role == "__no_access__":
            failures.append(
                (connection_id, referenced_by, "SP has no access to this connection")
            )
            print(f"[FAIL] {connection_id} -> SP has no access (referenced by {referenced_by})")
        elif role is None:
            failures.append(
                (connection_id, referenced_by, "SP is not in the role assignments")
            )
            print(f"[FAIL] {connection_id} -> SP not assigned any role (referenced by {referenced_by})")
        elif role in ACCEPTABLE_ROLES:
            print(f"[PASS] {connection_id} -> SP role '{role}' (referenced by {referenced_by})")
        else:
            failures.append(
                (connection_id, referenced_by, f"SP role '{role}' is insufficient")
            )
            print(f"[FAIL] {connection_id} -> SP role '{role}' is insufficient (referenced by {referenced_by})")

    print("")
    print("======================================")
    if failures:
        print(f"[FAIL] {len(failures)} connection(s) missing required SP permission:\n")
        for connection_id, referenced_by, reason in failures:
            print(f"  - {connection_id}")
            print(f"      reason      : {reason}")
            print(f"      referenced  : {referenced_by}")
        print("")
        print("Action: in Fabric > Manage connections, grant the service principal")
        print("at least the 'User' role on each connection listed above.")
        print("======================================")
        sys.exit(1)

    print("[PASS] Service principal has a usable role on all referenced connections.")
    print("======================================")
    sys.exit(0)


if __name__ == "__main__":
    main()
