# Google Drive API Setup Guide

This guide walks you through setting up Google Drive API access for the GPG File Watcher.

## Overview

To upload encrypted files to Google Drive, you'll need:
1. A Google Cloud Platform (GCP) project
2. Google Drive API enabled
3. OAuth 2.0 credentials
4. The credentials JSON file

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name (e.g., "GPG File Watcher")
4. Click **Create**
5. Wait for project creation to complete

### 2. Enable Google Drive API

1. In the Cloud Console, select your project
2. Go to **APIs & Services** → **Library**
3. Search for "Google Drive API"
4. Click on **Google Drive API**
5. Click **Enable**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (unless you have a Google Workspace)
3. Click **Create**
4. Fill in the required fields:
   - **App name**: "GPG File Watcher"
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click **Save and Continue**
6. On **Scopes** screen, click **Add or Remove Scopes**
7. Search for and add: `https://www.googleapis.com/auth/drive.file`
8. Click **Update** → **Save and Continue**
9. On **Test users** screen:
   - Click **Add Users**
   - Add your Google account email
   - Click **Add** → **Save and Continue**
10. Review and click **Back to Dashboard**

### 4. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: Select **Desktop app**
4. Name: "GPG File Watcher Desktop"
5. Click **Create**
6. A dialog appears with Client ID and Client Secret
7. Click **Download JSON**
8. Save the file as `gdrive_credentials.json`

### 5. Install Credentials File

```bash
# Create config directory if it doesn't exist
mkdir -p ~/.config/gpg-file-watcher

# Move downloaded credentials file
mv ~/Downloads/client_secret_*.json ~/.config/gpg-file-watcher/gdrive_credentials.json

# Verify file exists
ls -l ~/.config/gpg-file-watcher/gdrive_credentials.json
```

### 6. Update Configuration

Edit your config file:

```bash
nano ~/.config/gpg-file-watcher/config.yaml
```

Update these fields:

```yaml
# Enable Google Drive
google_drive_enabled: true

# Path to credentials (should already be set correctly)
google_drive_credentials_file: "~/.config/gpg-file-watcher/gdrive_credentials.json"

# Optional: Specify a folder ID
# google_drive_folder_id: "1ABC...XYZ"
```

### 7. First-Time Authentication

Run the watcher with Google Drive enabled:

```bash
python3 gpg_file_watcher.py --google-drive
```

On first run:
1. A browser window will open automatically
2. Log in with your Google account
3. You may see a warning "Google hasn't verified this app"
   - Click **Advanced**
   - Click **Go to GPG File Watcher (unsafe)**
4. Review permissions and click **Allow**
5. You'll see "The authentication flow has completed"
6. Close the browser window

The authentication token is saved to `~/.config/gpg-file-watcher/gdrive_token.json` and will be reused for future runs.

## Finding a Google Drive Folder ID

To upload to a specific folder instead of root:

1. Open Google Drive in your browser
2. Navigate to the folder you want
3. Look at the URL in your address bar:
   ```
   https://drive.google.com/drive/folders/1ABC...XYZ
                                            ^^^^^^^^^
                                            This is the folder ID
   ```
4. Copy the ID (everything after `/folders/`)
5. Add it to your config:
   ```yaml
   google_drive_folder_id: "1ABC...XYZ"
   ```

## Security Considerations

### Protecting Your Credentials

```bash
# Set proper permissions on credentials file
chmod 600 ~/.config/gpg-file-watcher/gdrive_credentials.json
chmod 600 ~/.config/gpg-file-watcher/gdrive_token.json

# Verify permissions
ls -l ~/.config/gpg-file-watcher/
```

### OAuth Scopes

The application uses the `https://www.googleapis.com/auth/drive.file` scope, which:
- ✅ Allows access ONLY to files created by this application
- ✅ Cannot read or modify other files in your Drive
- ✅ Most secure option for this use case

### Revoking Access

To revoke access at any time:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click **Third-party apps with account access**
3. Find "GPG File Watcher"
4. Click **Remove Access**

Or simply delete the token file:

```bash
rm ~/.config/gpg-file-watcher/gdrive_token.json
```

## Troubleshooting

### "Google hasn't verified this app" Warning

This is normal for personal projects. The app is safe to use because:
- You created it
- You control the credentials
- It only has access to files it creates

### Authentication Fails

```bash
# Delete token and try again
rm ~/.config/gpg-file-watcher/gdrive_token.json
python3 gpg_file_watcher.py --google-drive
```

### "Access Not Configured" Error

Make sure you:
1. Enabled Google Drive API in the Cloud Console
2. Added your email as a test user in OAuth consent screen

### File Upload Fails

Check logs:
```bash
tail -f ~/.local/share/gpg-file-watcher/watcher.log
```

Common issues:
- Invalid folder ID
- Insufficient permissions
- Network connectivity

### Quota Exceeded

Google Drive API has usage quotas:
- 20,000 queries per 100 seconds per project
- 1 billion queries per day per project

For personal use, these limits are unlikely to be hit.

## Command Line Usage

```bash
# Run with Google Drive upload
python3 gpg_file_watcher.py --google-drive

# Run without Google Drive (even if enabled in config)
python3 gpg_file_watcher.py

# Use custom config file
python3 gpg_file_watcher.py --config ~/my-config.yaml --google-drive

# Debug mode
python3 gpg_file_watcher.py --google-drive --debug
```

## Advanced Configuration

### Multiple Upload Locations

If you want to upload to different folders based on file type, you can:
1. Run multiple instances with different config files
2. Set different `watch_directory` and `google_drive_folder_id` for each

### Automatic Local Cleanup

To delete local files after successful upload:

```yaml
google_drive_delete_local: true
```

⚠️ **Warning**: Only enable this after thoroughly testing your setup!

## Testing

Test the setup:

```bash
# Create a test file
echo "Test content" > ~/Documents/to_encrypt/test.txt

# Watch the logs
tail -f ~/.local/share/gpg-file-watcher/watcher.log

# Check Google Drive
# You should see test.txt.gpg appear in your Drive
```

## Support

For issues:
1. Check logs: `~/.local/share/gpg-file-watcher/watcher.log`
2. Run with `--debug` flag for verbose output
3. Verify Google Drive API is enabled in Cloud Console
4. Ensure you're added as a test user in OAuth consent screen

## References

- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth 2.0 Desktop Apps Guide](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google Cloud Console](https://console.cloud.google.com/)
