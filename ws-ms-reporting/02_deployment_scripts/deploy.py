"""
Fabric Workspace Deployment Script
"""

import argparse
import os
import subprocess
import sys
import traceback

# Fix encoding for Windows agents
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from azure.identity import ClientSecretCredential
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

print("="*60)
print("FABRIC WORKSPACE DEPLOYMENT SCRIPT")
print("="*60)
print()

print("--- Parsing arguments ---")
parser = argparse.ArgumentParser(description="Run Fabric Workspace Publish")
parser.add_argument('--repo_dir', required=True, help='Path to repository folder')
parser.add_argument('--workspace_id', required=True, help='Fabric Workspace ID')
parser.add_argument('--environment', required=False, help='Fabric Environment', default="DEV")
args = parser.parse_args()
print("OK Arguments parsed successfully")
print()

workspace_id = args.workspace_id
repo_dir = os.path.join(args.repo_dir, "01_fabric_dwh")
environment = args.environment

print("--- Configuration ---")
print(f"  Workspace ID   : {workspace_id}")
print(f"  Repo Directory : {repo_dir}")
print(f"  Environment    : {environment}")
print(f"  Repo Exists    : {os.path.isdir(repo_dir)}")
print()


print("--- Git Info ---")
try:
    branch_name = subprocess.check_output(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        stderr=subprocess.DEVNULL
    ).decode().strip()
    if branch_name == "HEAD":
        branch_name = os.getenv("BUILD_SOURCEBRANCHNAME", "detached-HEAD")
except Exception:
    branch_name = os.getenv("BUILD_SOURCEBRANCHNAME", "unknown")
print(f"  Current Branch : {branch_name}")
print()


print("--- Azure Credentials ---")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")
tenant_id = os.getenv("AZURE_TENANT_ID")

print(f"  AZURE_CLIENT_ID     : {'set' if client_id else 'MISSING'}")
print(f"  AZURE_CLIENT_SECRET : {'set' if client_secret else 'MISSING'}")
print(f"  AZURE_TENANT_ID     : {'set' if tenant_id else 'MISSING'}")
print()

if not client_id or not client_secret or not tenant_id:
    print("FAILED Azure credential validation failed")
    sys.exit(1)

print("--- Authentication ---")
try:
    credential = ClientSecretCredential(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id
    )
    print("OK ClientSecretCredential created successfully")
except Exception as e:
    print(f"FAILED Authentication error: {e}")
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
print()


print("--- Initializing FabricWorkspace ---")
item_types = ["Lakehouse", "Warehouse", "Notebook", "DataPipeline", "Environment", "SemanticModel", "Report"]
print(f"  Item types in scope: {', '.join(item_types)}")

try:
    fw = FabricWorkspace(
        workspace_id=workspace_id,
        repository_directory=repo_dir,
        item_type_in_scope=item_types,
        environment=environment,
        token_credential=credential
    )
    print("OK FabricWorkspace initialized")
except Exception as e:
    print(f"FAILED FabricWorkspace initialization error: {e}")
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
print()

print("--- Publishing all items ---")
try:
    publish_all_items(fw)
    print("OK All items published")
except Exception as e:
    print(f"FAILED publish_all_items error: {e}")
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
print()

print("--- Removing orphan items ---")
try:
    unpublish_all_orphan_items(fw)
    print("OK Orphan items removed")
except Exception as e:
    print(f"FAILED unpublish_all_orphan_items error: {e}")
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
print()

print("="*60)
print("DEPLOYMENT COMPLETE")
print(f"  Environment    : {environment}")
print(f"  Workspace ID   : {workspace_id}")
print("="*60)
