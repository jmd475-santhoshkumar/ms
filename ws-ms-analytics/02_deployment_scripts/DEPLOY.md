# Fabric Workspace Deployment Script

## Overview
This Python script (`deploy.py`) automates the deployment of Microsoft Fabric workspace items including Lakehouses, Warehouses, Notebooks, DataPipelines, Environments, SemanticModels, and Reports.

## Purpose
The script handles the complete deployment workflow:
- Validates deployment arguments and configuration
- Authenticates with Azure using service principal credentials
- Initializes a Fabric workspace connection
- Publishes all repository items to the specified workspace
- Removes orphaned items from the workspace

## Requirements
- Python 3.7+
- See [REQUIREMENTS.md](./REQUIREMENTS.md) for Python package dependencies

## Usage

### Command Syntax
```bash
python deploy.py --repo_dir <path_to_repo> --workspace_id <workspace_id> [--environment <environment>]
```

### Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--repo_dir` | Yes | Path to the repository root folder | N/A |
| `--workspace_id` | Yes | Microsoft Fabric Workspace ID | N/A |
| `--environment` | No | Fabric Environment name | `DEV` |

### Example Usage
```bash
python deploy.py \
  --repo_dir "C:\projects\ws-ms-analytics" \
  --workspace_id "12345678-1234-1234-1234-123456789012" \
  --environment "DEV"
```

## Environment Variables Required

The script requires the following Azure service principal credentials as environment variables:

| Variable | Description |
|----------|-------------|
| `AZURE_CLIENT_ID` | Azure Application (Client) ID |
| `AZURE_CLIENT_SECRET` | Azure Client Secret |
| `AZURE_TENANT_ID` | Azure Tenant ID |

### Setting Environment Variables (Windows)
```powershell
$env:AZURE_CLIENT_ID = "your-client-id"
$env:AZURE_CLIENT_SECRET = "your-client-secret"
$env:AZURE_TENANT_ID = "your-tenant-id"
```

### Setting Environment Variables (Linux/macOS)
```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
```

## Supported Item Types
The script automatically deploys the following Microsoft Fabric item types:
- **Lakehouse** - Data lake storage
- **Warehouse** - SQL data warehouse
- **Notebook** - Spark notebooks for data processing
- **DataPipeline** - Orchestration pipelines
- **Environment** - Fabric environments
- **SemanticModel** - Power BI semantic models
- **Report** - Power BI reports

## Deployment Workflow

### 1. Argument Parsing
- Validates required arguments (`--repo_dir`, `--workspace_id`)
- Sets optional environment (defaults to "DEV")
- Confirms repository directory exists

### 2. Configuration
- Constructs the fabric working directory path (appends `01_fabric_dwh`)
- Displays configuration summary

### 3. Git Information
- Retrieves current Git branch name
- Falls back to environment variable `BUILD_SOURCEBRANCHNAME` if in detached HEAD state
- Displays Git context for deployment tracking

### 4. Azure Authentication
- Validates presence of required credential environment variables
- Creates Azure service principal credential object
- Exits with error if credentials are missing

### 5. Fabric Workspace Initialization
- Instantiates FabricWorkspace object with:
  - Target workspace ID
  - Repository directory path
  - Configured item types
  - Environment name
  - Azure credentials

### 6. Item Publishing
- Publishes all items from the repository to the Fabric workspace
- Handles item creation, updates, and dependencies

### 7. Orphan Cleanup
- Identifies and removes items in workspace that no longer exist in repository
- Keeps workspace clean and in sync with source control

### 8. Completion
- Displays final deployment summary
- Exit code 0 on success, 1 on failure

## Error Handling

The script includes comprehensive error handling with:
- **Validation checks** - Confirms credentials and paths before deployment
- **Exception catching** - Gracefully handles errors at each stage
- **Stack traces** - Outputs full exception details for debugging
- **Exit codes** - Returns exit code 1 on any failure

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing credentials | Environment variables not set | Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` |
| Invalid repository path | Path doesn't exist | Verify `--repo_dir` points to valid directory |
| Workspace not found | Incorrect workspace ID | Confirm workspace ID in Azure portal |
| Authentication failed | Invalid credentials or permissions | Verify service principal has Fabric workspace access |
| Encoding errors | Windows compatibility issue | Script includes UTF-8 encoding fix for Windows agents |

## Dependencies

- **azure-identity** - Azure authentication
- **requests** - HTTP library for API calls
- **fabric_cicd** - Custom library for Fabric deployment operations

See [REQUIREMENTS.md](./REQUIREMENTS.md) for version details.

## Integration with CI/CD

This script is designed to integrate with Azure Pipelines CI/CD workflows:
- Falls back to `BUILD_SOURCEBRANCHNAME` environment variable for Git branch info
- Suitable for automated deployment stages
- Designed for service principal authentication in pipeline agents

## Logging Output

The script provides verbose output organized in sections:
```
============================================================
FABRIC WORKSPACE DEPLOYMENT SCRIPT
============================================================

--- Parsing arguments ---
OK Arguments parsed successfully

--- Configuration ---
  Workspace ID   : 12345678-...
  Repo Directory : C:\projects\ws-ms-analytics\01_fabric_dwh
  Environment    : DEV
  Repo Exists    : True

--- Git Info ---
  Current Branch : main

--- Azure Credentials ---
  AZURE_CLIENT_ID     : set
  AZURE_CLIENT_SECRET : set
  AZURE_TENANT_ID     : set

--- Authentication ---
OK ClientSecretCredential created successfully

--- Initializing FabricWorkspace ---
  Item types in scope: Lakehouse, Warehouse, Notebook, ...
OK FabricWorkspace initialized

--- Publishing all items ---
OK All items published

--- Removing orphan items ---
OK Orphan items removed

============================================================
DEPLOYMENT COMPLETE
  Environment    : DEV
  Workspace ID   : 12345678-...
============================================================
```

## Notes

- The script appends `01_fabric_dwh` to the provided repository directory
- Windows environments include special UTF-8 encoding configuration for compatibility
- Scripts should be run with appropriate permissions to access repository and Azure resources
- Deployment time varies based on number and size of items
