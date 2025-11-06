# Dropbox API Setup Guide

This guide walks you through setting up Dropbox API access for the GPG File Watcher.

## Overview

To upload encrypted files to Dropbox, you'll need:
1. A Dropbox account (free or paid)
2. A Dropbox App created in the App Console
3. An access token for authentication

## Step-by-Step Setup

### 1. Create Dropbox App

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click **Create app**
3. Choose API: Select **Scoped access**
4. Choose access type:
   - **Full Dropbox**: Access to all files and folders (recommended)
   - **App folder**: Access only to a specific folder (more restricted)
5. Name your app: "GPG File Watcher" (or any name you prefer)
6. Click **Create app**

### 2. Configure App Permissions

1. In your app's page, click the **Permissions** tab
2. Enable the following permissions:
   - ✅ `files.metadata.write` - Create, edit, and delete files
   - ✅ `files.content.write` - Upload file content
   - ✅ `files.content.read` - Download file content (for verification)
3. Click **Submit** at the bottom

### 3. Generate Access Token

1. Go to the **Settings** tab
2. Scroll down to **OAuth 2** section
3. Under **Generated access token**, click **Generate**
4. Copy the token (it will look like: `sl.B...`)
5. **Important**: Save this token securely - it won't be shown again!

### 4. Install Dropbox Library

```bash
pip3 install dropbox
```

### 5. Update Configuration

Edit your config file:

```bash
nano ~/.config/gpg-file-watcher/config.yaml
```

Update these fields:

```yaml
# Enable Dropbox
dropbox_enabled: true

# Paste your access token here
dropbox_access_token: "sl.B...your-token-here..."

# Optional: Specify upload folder
dropbox_folder_path: "/encrypted"  # or "/" for root
```

### 6. Test the Connection

Run the watcher with Dropbox enabled:

```bash
python3 gpg_file_watcher.py --dropbox
```

You should see:
```
✓ Dropbox connected successfully
```

## Access Token Security

### Best Practices

1. **Never commit token to version control**
   ```bash
   # Add to .gitignore
   echo "*.yaml" >> .gitignore
   ```

2. **Set restrictive file permissions**
   ```bash
   chmod 600 ~/.config/gpg-file-watcher/config.yaml
   ```

3. **Use environment variable (alternative method)**
   ```yaml
   # Instead of hardcoding token
   dropbox_access_token: "${DROPBOX_ACCESS_TOKEN}"
   ```
   
   Then set environment variable:
   ```bash
   export DROPBOX_ACCESS_TOKEN="sl.B...your-token..."
   ```

4. **Rotate tokens periodically**
   - Generate new token in app console
   - Update configuration
   - Revoke old token

### Revoking Access

To revoke access at any time:

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click on your app
3. Go to **Settings** tab
4. Scroll to **Generated access token**
5. Click **Revoke** next to the token

Or delete the app entirely:
- In the app console, click **Delete app**

## Finding Dropbox Folder Path

Dropbox uses Unix-style paths:

```
/                          → Root folder (all your Dropbox)
/Documents                 → Documents folder
/encrypted                 → Custom folder for encrypted files
/backups/work/encrypted    → Nested folder structure
```

**Tips:**
- Paths always start with `/`
- Use forward slashes `/` (not backslashes)
- Folder is created automatically if it doesn't exist
- Case-sensitive on all platforms

## Access Types Explained

### Full Dropbox Access (Recommended)
- Can access any file/folder in your Dropbox
- More flexible - can change upload location anytime
- Used by most apps

### App Folder Access (More Restricted)
- Only accesses files in `/Apps/GPG File Watcher/`
- More secure but less flexible
- Files isolated from rest of Dropbox

## Token Types

### Short-Lived Tokens (Advanced)
- Expire after 4 hours
- More secure but require refresh logic
- Not needed for personal use

### Long-Lived Tokens (Recommended)
- Don't expire automatically
- Perfect for automated scripts
- What we're using in this guide

## Troubleshooting

### "Invalid Access Token" Error

1. Verify token is correct (no extra spaces)
2. Check token hasn't been revoked
3. Generate new token if needed

```bash
# Test token manually
python3 -c "import dropbox; print(dropbox.Dropbox('YOUR_TOKEN').users_get_current_account())"
```

### Permission Denied Error

1. Go to app **Permissions** tab
2. Enable required permissions:
   - `files.metadata.write`
   - `files.content.write`
3. Click **Submit**
4. Generate **new** access token (old one won't get new permissions)

### Folder Not Found / Cannot Create Folder

1. Check path format (must start with `/`)
2. Verify parent folders exist
3. Check for typos in path
4. Try root folder `/` first to test

### Library Not Installed

```bash
pip3 install dropbox

# Or if using virtual environment
source venv/bin/activate
pip install dropbox
```

### Rate Limiting

Dropbox has API rate limits:
- ~12,000 API calls per app per hour
- Files >150MB use chunked upload

For personal use, these limits are unlikely to be hit.

## Command Line Usage

```bash
# Run with Dropbox upload
python3 gpg_file_watcher.py --dropbox

# Run without Dropbox (even if enabled in config)
python3 gpg_file_watcher.py

# Use custom config file
python3 gpg_file_watcher.py --config ~/my-config.yaml --dropbox

# Debug mode
python3 gpg_file_watcher.py --dropbox --debug
```

## Configuration Examples

### Basic Setup (Root Folder)
```yaml
dropbox_enabled: true
dropbox_access_token: "sl.B...your-token..."
dropbox_folder_path: "/"
```

### Organized Storage
```yaml
dropbox_enabled: true
dropbox_access_token: "sl.B...your-token..."
dropbox_folder_path: "/backups/encrypted"
```

### Using Environment Variable
```yaml
dropbox_enabled: true
dropbox_access_token: "${DROPBOX_ACCESS_TOKEN}"
dropbox_folder_path: "/encrypted"
```

Then run:
```bash
export DROPBOX_ACCESS_TOKEN="sl.B...your-token..."
python3 gpg_file_watcher.py --dropbox
```

## Testing

Test the setup:

```bash
# Create a test file
echo "Test content" > ~/Documents/to_encrypt/test.txt

# Run with Dropbox
python3 gpg_file_watcher.py --dropbox

# Check logs
tail -f ~/.local/share/gpg-file-watcher/watcher.log

# Check Dropbox
# You should see test.txt.gpg in your specified folder
```

## Comparison: Dropbox vs Google Drive

| Feature | Dropbox | Google Drive |
|---------|---------|--------------|
| Authentication | Access Token | OAuth 2.0 |
| Setup Complexity | Simple | Moderate |
| Browser Required | No | Yes (first time) |
| Token Expiry | Optional | Auto-refresh |
| File Size Limit | No limit* | No limit* |
| Best For | Quick setup | Enterprise integration |

*Subject to storage quota

## Advanced Usage

### Multiple Upload Locations

Create different configurations:

```bash
# config-personal.yaml
dropbox_folder_path: "/personal/encrypted"

# config-work.yaml  
dropbox_folder_path: "/work/encrypted"
```

Run separately:
```bash
python3 gpg_file_watcher.py --config config-personal.yaml --dropbox
python3 gpg_file_watcher.py --config config-work.yaml --dropbox
```

### Shared Folders

If uploading to a shared Dropbox folder:
1. Folder must be in your Dropbox
2. Path is relative to your Dropbox root
3. Example: `/Shared Folders/TeamName/encrypted`

## Security Considerations

### Access Token Protection
- ✅ Treat like a password
- ✅ Never share publicly
- ✅ Store securely
- ✅ Rotate periodically
- ✅ Revoke if compromised

### File Encryption
- ✅ Files are GPG-encrypted before upload
- ✅ Dropbox sees only encrypted data
- ✅ You control decryption keys
- ✅ End-to-end security maintained

### App Permissions
- ✅ Request only needed permissions
- ✅ Use App Folder access for maximum isolation
- ✅ Monitor app activity in Dropbox

## Migration from Google Drive

Already using Google Drive? Easy switch:

1. Get Dropbox access token (steps above)
2. Update config:
   ```yaml
   google_drive_enabled: false
   dropbox_enabled: true
   dropbox_access_token: "your-token"
   ```
3. Run with `--dropbox` instead of `--google-drive`

## Support

For issues:
1. Check logs: `~/.local/share/gpg-file-watcher/watcher.log`
2. Run with `--debug` flag for verbose output
3. Verify token in Dropbox App Console
4. Check permissions are enabled
5. Test token with simple script

## References

- [Dropbox API Documentation](https://www.dropbox.com/developers/documentation)
- [Dropbox App Console](https://www.dropbox.com/developers/apps)
- [Dropbox Python SDK](https://dropbox-sdk-python.readthedocs.io/)
- [API Rate Limits](https://www.dropbox.com/developers/reference/rate-limits)

---

**Version:** 2.1.0  
**Author:** bva (scourgethetracker/bt7474)  
**Date:** 2025-10-29
