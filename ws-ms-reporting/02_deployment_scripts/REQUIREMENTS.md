# Python Dependencies - Requirements

## Overview
This document describes the Python packages required to run the Fabric Workspace Deployment Script (`deploy.py`).

## Installation

### Install All Dependencies
```bash
pip install -r requirements.txt
```

### Upgrade Existing Packages
```bash
pip install --upgrade -r requirements.txt
```

## Required Packages

### 1. azure-identity
**Purpose**: Azure authentication and credential management

**Description**: 
- Provides `ClientSecretCredential` class for service principal authentication
- Authenticates with Azure AD using client ID, secret, and tenant ID
- Manages token acquisition and refresh

**Usage in Script**:
```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    client_id=client_id,
    client_secret=client_secret,
    tenant_id=tenant_id
)
```

**Installation**:
```bash
pip install azure-identity
```

**Documentation**: https://learn.microsoft.com/en-us/python/api/azure-identity/

---

### 2. requests
**Purpose**: HTTP library for making API requests

**Description**:
- Industry-standard Python HTTP library
- Used for REST API calls to Azure and Fabric services
- Handles request/response formatting and error handling

**Usage in Script**:
- Indirect dependency (used by fabric_cicd library)
- May be used for additional HTTP calls

**Installation**:
```bash
pip install requests
```

**Documentation**: https://requests.readthedocs.io/

---

### 3. fabric_cicd
**Purpose**: Custom library for Microsoft Fabric CI/CD operations

**Description**:
- Proprietary library for Fabric workspace management
- Provides `FabricWorkspace` class for workspace operations
- Includes `publish_all_items()` and `unpublish_all_orphan_items()` functions
- Handles item publishing, dependency resolution, and orphan cleanup

**Key Classes/Functions**:
- `FabricWorkspace` - Main workspace management class
- `publish_all_items(fw)` - Publishes all items from repository to workspace
- `unpublish_all_orphan_items(fw)` - Removes orphaned items from workspace

**Usage in Script**:
```python
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

fw = FabricWorkspace(
    workspace_id=workspace_id,
    repository_directory=repo_dir,
    item_type_in_scope=item_types,
    environment=environment,
    token_credential=credential
)

publish_all_items(fw)
unpublish_all_orphan_items(fw)
```

**Installation**:
This is a custom internal package. Installation method depends on your package repository setup.

---

## Dependency Tree

```
deploy.py
├── azure-identity
│   └── (handles Azure authentication)
├── requests
│   └── (HTTP library)
└── fabric_cicd
    ├── azure-identity
    └── requests
```

## Version Compatibility

| Package | Python Version | Notes |
|---------|----------------|-------|
| azure-identity | 3.7+ | Supports Python 3.7 and newer |
| requests | 3.6+ | Supports Python 3.6 and newer |
| fabric_cicd | 3.7+ | Internal package requirements |

## Installation in Virtual Environment (Recommended)

### Windows
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Linux/macOS
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Checking Installed Packages

```bash
# List all installed packages
pip list

# Check specific package version
pip show azure-identity
pip show requests
pip show fabric_cicd

# Verify requirements are met
pip check
```

## Troubleshooting

### Installation Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'azure'` | Run `pip install azure-identity` |
| `ModuleNotFoundError: No module named 'requests'` | Run `pip install requests` |
| `ModuleNotFoundError: No module named 'fabric_cicd'` | Ensure custom package is available in your package repository |
| Permission denied during install | Try `pip install --user -r requirements.txt` or use virtual environment |
| SSL certificate error | Try `pip install --trusted-host pypi.org -r requirements.txt` |

### Runtime Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError` | Package not installed | Verify installation with `pip list` and reinstall if needed |
| Version conflicts | Incompatible package versions | Recreate virtual environment and reinstall all packages |
| Missing Azure module | azure-identity not installed | Install with `pip install azure-identity` |

## Updating Dependencies

### Update All Packages
```bash
pip install --upgrade -r requirements.txt
```

### Update Specific Package
```bash
pip install --upgrade azure-identity
```

### Generate Updated Requirements File
```bash
pip freeze > requirements.txt
```

## Security Considerations

- **Never commit credentials** to version control
- Store Azure credentials in secure vaults or environment variables
- Regularly rotate service principal secrets
- Audit package vulnerabilities:
  ```bash
  pip install safety
  safety check
  ```

## Azure-Identity Authentication Methods

The `azure-identity` package supports multiple authentication methods:

1. **ClientSecretCredential** (used in deploy.py)
   - Service principal with client secret
   - Suitable for CI/CD pipelines
   - Requires: Client ID, Client Secret, Tenant ID

2. **DefaultAzureCredential**
   - Automatic credential selection
   - Supports interactive, environment, and managed identity authentication

3. **ManagedIdentityCredential**
   - For Azure managed identities
   - Suitable for Azure services

4. **InteractiveBrowserCredential**
   - User interactive authentication
   - For local development

## Additional Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [Azure Identity Python Library](https://learn.microsoft.com/en-us/python/api/azure-identity/)
- [Requests Library Documentation](https://requests.readthedocs.io/)
- [Python Package Index](https://pypi.org/)

## Version Information

**Last Updated**: 2026-05-12
**Format**: standard pip requirements.txt
**Expected Maintenance**: Review and update annually or when security updates are released
