import argparse
import subprocess
import os
import requests
import sys



parser = argparse.ArgumentParser(description="Validate Azure Fabric Workspace")
parser.add_argument('--workspace_id', required=True, help='Fabric Workspace ID')
parser.add_argument('--workspace_name', required=True, help='Expected Fabric Workspace Name')
args = parser.parse_args()


workspace_id = args.workspace_id
workspace_name = args.workspace_name


client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")
tenant_id = os.getenv("AZURE_TENANT_ID")


if not all([client_id, client_secret, tenant_id]):
    print("Error: Missing required environment variables.")
    sys.exit(1)
    
    

token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


token_payload = {
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://api.fabric.microsoft.com/.default",
    "grant_type": "client_credentials"
}


token_response = requests.post(token_url, data=token_payload)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}


workspace_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"


response = requests.get(workspace_url, headers=headers)
response.raise_for_status()


workspace_details = response.json()
workspace_name_fetched = workspace_details.get("displayName")


if workspace_name_fetched == workspace_name:
    print(f"Success :: Workspace name '{workspace_name}' matches '{workspace_name_fetched}'")
else:
    print(f"Error :: Workspace name '{workspace_name}' does not match '{workspace_name_fetched}'")
    sys.exit(1)