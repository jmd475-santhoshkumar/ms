# Workspace Validation Script

## Overview
This Python script (`workspace_validation.py`) validates that a Microsoft Fabric workspace exists and has the correct name by querying the Fabric API.

## Purpose
The script performs the following validation:
- Authenticates with Azure using service principal credentials
- Retrieves workspace details from the Microsoft Fabric API
- Compares fetched workspace name with expected workspace name
- Reports success or failure of validation

## Requirements
- Python 3.7+
- See [REQUIREMENTS.md](./REQUIREMENTS.md) for Python package dependencies

## Usage

### Command Syntax
```bash
python workspace_validation.py --workspace_id <workspace_id> --workspace_name <workspace_name>
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--workspace_id` | Yes | Microsoft Fabric Workspace ID (UUID) |
| `--workspace_name` | Yes | Expected Fabric Workspace Display Name |

### Example Usage
```bash
python workspace_validation.py \
  --workspace_id "12345678-1234-1234-1234-123456789012" \
  --workspace_name "ws-ms-analytics-PROD"
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

## Validation Workflow

### 1. Argument Parsing
- Parses required arguments: `--workspace_id` and `--workspace_name`
- Validates that both arguments are provided

### 2. Environment Variable Validation
- Checks for presence of Azure credentials
- Exits with error code 1 if any credential is missing

### 3. Azure Authentication
- Constructs token request URL using tenant ID
- Sends OAuth 2.0 client credentials flow request
- Obtains access token from Azure AD
- Exits with error if token acquisition fails

### 4. API Request
- Calls Microsoft Fabric API endpoint: `https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}`
- Includes Bearer token in Authorization header
- Retrieves workspace details in JSON format

### 5. Name Validation
- Compares fetched `displayName` with expected `workspace_name`
- Reports success or failure with workspace names
- Exits with code 0 on success, 1 on failure

## API Endpoints

### Microsoft Fabric Workspace Details
**Endpoint**: `GET https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}`

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Response Example**:
```json
{
  "id": "12345678-1234-1234-1234-123456789012",
  "displayName": "ws-ms-analytics-PROD",
  "description": "Workspace for Media Sense analytics",
  "type": "Workspace"
}
```

## Output Examples

### Successful Validation
```
Success :: Workspace name 'ws-ms-analytics-PROD' matches 'ws-ms-analytics-PROD'
Exit Code: 0
```

### Failed Validation - Name Mismatch
```
Error :: Workspace name 'ws-ms-analytics-PROD' does not match 'ws-ms-analytics-DEV'
Exit Code: 1
```

### Failed Validation - Missing Credentials
```
Error: Missing required environment variables.
Exit Code: 1
```

### Failed Validation - API Error
```
HTTPError: 404 Client Error: Not Found for url: https://api.fabric.microsoft.com/v1/workspaces/invalid-id
Exit Code: 1
```

## Error Handling

The script includes error handling for:
- **Missing credentials** - Validates environment variables before API calls
- **Authentication failures** - Handles token request errors
- **API failures** - Raises HTTP exceptions for non-200 responses
- **Network errors** - Propagates connection errors with full details

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing environment variables | Credentials not set | Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` |
| 404 Not Found | Workspace ID doesn't exist | Verify workspace ID in Azure Fabric portal |
| 401 Unauthorized | Invalid credentials or expired token | Verify service principal credentials are correct |
| Name mismatch error | Workspace name doesn't match expectation | Verify the workspace display name is correct |
| Connection error | Network connectivity issue | Check network connectivity and proxy settings |

## Dependencies

- **requests** - HTTP library for API calls

See [REQUIREMENTS.md](./REQUIREMENTS.md) for details.

## Integration with CI/CD

This script is designed for use in CI/CD pipelines:
- Validates workspace configuration before deployment
- Prevents deployment to incorrect workspaces
- Suitable for pre-deployment validation stage
- Provides clear exit codes for pipeline decisions (0=success, 1=failure)
- Works with Azure Pipelines and other CI/CD systems

## Security Considerations

- **Credentials in environment variables** - Use secure vaults in CI/CD systems
- **Never hardcode credentials** - Always use environment variables
- **Access tokens** - Tokens are temporarily held in memory and not persisted
- **HTTPS only** - All API calls use HTTPS encryption
- **Audit logging** - Workspace validation calls appear in Azure AD audit logs

## Implementation Example: Azure Pipelines

```yaml
- script: |
    python workspace_validation.py \
      --workspace_id $(FABRIC_WORKSPACE_ID) \
      --workspace_name "ws-ms-analytics-PROD"
  displayName: Validate Workspace
  env:
    AZURE_CLIENT_ID: $(AZURE_CLIENT_ID)
    AZURE_CLIENT_SECRET: $(AZURE_CLIENT_SECRET)
    AZURE_TENANT_ID: $(AZURE_TENANT_ID)
```

## Notes

- Script performs read-only validation (no workspace modifications)
- Workspace ID must be a valid UUID format
- Service principal must have permissions to read workspace metadata
- API calls use Microsoft Fabric API v1 (stable)
- Response time typically under 1 second

## Troubleshooting Tips

1. **Test credentials independently**:
   ```bash
   $env:AZURE_CLIENT_ID = "your-id"
   $env:AZURE_CLIENT_SECRET = "your-secret"
   $env:AZURE_TENANT_ID = "your-tenant"
   python workspace_validation.py --workspace_id "test-id" --workspace_name "test"
   ```

2. **Enable verbose output**:
   Add print statements to debug authentication or API calls

3. **Verify workspace ID**:
   - Log into Fabric portal
   - Navigate to workspace settings
   - Copy workspace ID from URL or settings page

4. **Check service principal permissions**:
   - Ensure service principal has Reader or higher role on workspace
   - Verify in Azure portal under workspace Access

## Additional Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [Fabric API Documentation](https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces)
- [Azure Authentication Flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow)
