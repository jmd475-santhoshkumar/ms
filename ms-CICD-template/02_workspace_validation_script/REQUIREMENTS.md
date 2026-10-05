# Python Dependencies - Requirements

## Overview
This document describes the Python packages required to run the Workspace Validation Script (`workspace_validation.py`).

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

### requests
**Purpose**: HTTP library for making API requests

**Description**:
- Industry-standard Python HTTP library
- Used for OAuth 2.0 token acquisition
- Handles REST API calls to Microsoft Fabric API
- Manages request/response formatting and error handling

**Usage in Script**:
```python
import requests

# Token acquisition
token_response = requests.post(token_url, data=token_payload)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]

# Workspace validation
response = requests.get(workspace_url, headers=headers)
response.raise_for_status()
workspace_details = response.json()
```

**Key Functions**:
- `requests.post()` - Make POST requests (for token acquisition)
- `requests.get()` - Make GET requests (for API queries)
- `response.raise_for_status()` - Raise exception on HTTP errors
- `response.json()` - Parse JSON response body

**Installation**:
```bash
pip install requests
```

**Documentation**: https://requests.readthedocs.io/

---

## Dependency Tree

```
workspace_validation.py
└── requests
    └── (HTTP library for API and token calls)
```

## Version Compatibility

| Package | Python Version | Notes |
|---------|----------------|-------|
| requests | 3.6+ | Supports Python 3.6 and newer |

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
pip show requests

# Verify requirements are met
pip check
```

## Troubleshooting

### Installation Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'requests'` | Run `pip install requests` |
| Permission denied during install | Try `pip install --user -r requirements.txt` or use virtual environment |
| SSL certificate error | Try `pip install --trusted-host pypi.org -r requirements.txt` |
| HTTP errors in script | Ensure requests library is updated: `pip install --upgrade requests` |

### Runtime Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError: No module named 'requests'` | Package not installed | Verify installation with `pip list` and reinstall if needed |
| Connection timeouts | Network or proxy issues | Check network connectivity and proxy settings |
| SSL verification errors | Certificate validation issues | May need to configure certificate bundles or proxy settings |

## Updating Dependencies

### Update Requests Package
```bash
pip install --upgrade requests
```

### Generate Updated Requirements File
```bash
pip freeze > requirements.txt
```

## Security Considerations

- **HTTPS connections** - The script uses HTTPS for all API calls
- **Token security** - Bearer tokens are temporarily held in memory
- **Never commit credentials** - Use environment variables for secrets
- **Audit package vulnerabilities**:
  ```bash
  pip install safety
  safety check
  ```

## Network & Proxy Configuration

If behind a corporate proxy, configure requests:

```python
import requests

# Define proxy settings
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080',
}

# Use proxy in requests
response = requests.get(url, headers=headers, proxies=proxies)
```

Or set environment variables:
```bash
set HTTP_PROXY=http://proxy.example.com:8080
set HTTPS_PROXY=https://proxy.example.com:8080
```

## Common Requests Library Usage Patterns

### Making a POST Request (Token Acquisition)
```python
import requests

url = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
payload = {
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://api.fabric.microsoft.com/.default",
    "grant_type": "client_credentials"
}

response = requests.post(url, data=payload)
response.raise_for_status()  # Raise exception on HTTP errors
token = response.json()["access_token"]
```

### Making a GET Request (API Query)
```python
import requests

url = "https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
response.raise_for_status()
data = response.json()
```

### Error Handling
```python
import requests

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
except requests.exceptions.ConnectionError as e:
    print(f"Connection Error: {e}")
except requests.exceptions.Timeout as e:
    print(f"Timeout Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request Error: {e}")
```

## Additional Resources

- [Requests Library Documentation](https://requests.readthedocs.io/)
- [HTTP Status Codes Reference](https://httpwg.org/specs/rfc9110.html#overview.of.status.codes)
- [Python Package Index](https://pypi.org/)
- [Microsoft Fabric API Documentation](https://learn.microsoft.com/en-us/rest/api/fabric/)

## Version Information

**Last Updated**: 2026-05-12
**Format**: standard pip requirements.txt
**Expected Maintenance**: Review and update annually or when security updates are released
**Minimal Dependencies**: This script requires only 1 external package, making it lightweight and easy to maintain
