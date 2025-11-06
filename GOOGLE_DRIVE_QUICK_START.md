# Google Drive Integration - 5-Minute Quick Start

Get Google Drive upload working in 5 minutes (after initial Google Cloud setup).

## Before You Start

✅ You have GPG File Watcher v2.0 installed and working
✅ You have a Google account
✅ 10-15 minutes for first-time Google Cloud setup

## Step 1: Google Cloud Setup (One-Time, ~10 min)

### 1.1 Create Project
1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it "GPG File Watcher" → Create
4. Wait for creation (~30 seconds)

### 1.2 Enable API
1. Make sure your new project is selected
2. Go to "APIs & Services" → "Library"
3. Search "Google Drive API"
4. Click it → Click "Enable"

### 1.3 Configure OAuth
1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" → Create
3. Fill in:
   - App name: `GPG File Watcher`
   - Your email for support
   - Your email for developer contact
4. Click "Save and Continue" through all screens
5. On "Test users" screen:
   - Click "Add Users"
   - Add YOUR Google email
   - Save and Continue

### 1.4 Create Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "+ Create Credentials" → "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "GPG File Watcher Desktop"
5. Click "Create"
6. **Download the JSON file** (this is important!)

## Step 2: Install Dependencies (~30 seconds)

```bash
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Step 3: Setup Credentials (~30 seconds)

```bash
# Create config directory
mkdir -p ~/.config/gpg-file-watcher

# Move downloaded credentials (adjust path if needed)
mv ~/Downloads/client_secret_*.json ~/.config/gpg-file-watcher/gdrive_credentials.json

# Secure the file
chmod 600 ~/.config/gpg-file-watcher/gdrive_credentials.json
```

## Step 4: Update Configuration (~1 minute)

Edit your config file:

```bash
nano ~/.config/gpg-file-watcher/config.yaml
```

Add these lines at the end:

```yaml
# Google Drive Configuration
google_drive_enabled: true
google_drive_credentials_file: "~/.config/gpg-file-watcher/gdrive_credentials.json"
google_drive_token_file: "~/.config/gpg-file-watcher/gdrive_token.json"
google_drive_folder_id: null
```

**Important**: When using `--google-drive` flag, files go directly to cloud storage and are NOT saved to the local `destination_directory`.

Save (Ctrl+O, Enter, Ctrl+X)

## Step 5: First Run (~2 minutes)

```bash
python3 gpg_file_watcher.py --google-drive
```

**What happens:**
1. A browser window opens automatically
2. Log in to your Google account
3. You'll see "Google hasn't verified this app"
   - Click "Advanced"
   - Click "Go to GPG File Watcher (unsafe)" ← This is YOUR app, it's safe!
4. Review permissions → Click "Allow"
5. Browser says "The authentication flow has completed"
6. Close browser
7. Terminal shows "✓ Google Drive connected successfully"

Done! The app is now running with Google Drive enabled.

## Step 6: Test (~30 seconds)

Keep the app running, open a new terminal:

```bash
# Create a test file
echo "Test content" > ~/Documents/to_encrypt/test.txt

# Watch the output in the first terminal
# You should see:
# ✓ Successfully encrypted: test.txt
# ✓ Uploaded to Google Drive: test.txt.gpg
```

Check your Google Drive - you should see `test.txt.gpg`!

## Troubleshooting

### "Google Drive libraries not installed"
```bash
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### "Credentials file not found"
```bash
# Check if file exists
ls -l ~/.config/gpg-file-watcher/gdrive_credentials.json

# If not, re-download from Google Cloud Console
```

### "Failed to authenticate"
```bash
# Delete token and try again
rm ~/.config/gpg-file-watcher/gdrive_token.json
python3 gpg_file_watcher.py --google-drive
```

### Upload works but want to upload to specific folder
1. Open Google Drive in browser
2. Create or navigate to target folder
3. Look at URL: `https://drive.google.com/drive/folders/1ABC...XYZ`
4. Copy the ID: `1ABC...XYZ`
5. Edit config:
   ```yaml
   google_drive_folder_id: "1ABC...XYZ"
   ```
6. Restart app

## Next Steps

### Want to run in background?
```bash
# Using nohup
nohup python3 gpg_file_watcher.py --google-drive > /tmp/gpg-watcher.log 2>&1 &

# Using tmux
tmux new -s gpg-watcher
python3 gpg_file_watcher.py --google-drive
# Press Ctrl+B, then D to detach
```

### Want to auto-start on login?
See README.md section on LaunchAgent setup

### Want to save space by auto-deleting local files?
Edit config:
```yaml
google_drive_delete_local: true  # ⚠️ Test thoroughly first!
```

### Want to disable Google Drive temporarily?
Just run without the flag:
```bash
python3 gpg_file_watcher.py
```

## Command Quick Reference

```bash
# Basic (no Google Drive)
python3 gpg_file_watcher.py

# With Google Drive
python3 gpg_file_watcher.py --google-drive

# Debug mode
python3 gpg_file_watcher.py --google-drive --debug

# Custom config
python3 gpg_file_watcher.py --config ~/other-config.yaml --google-drive

# Help
python3 gpg_file_watcher.py --help
```

## Configuration Quick Reference

| Setting | What It Does | Recommended |
|---------|-------------|-------------|
| `google_drive_enabled` | Turn on/off | `true` or use `--google-drive` flag |
| `google_drive_credentials_file` | OAuth creds location | `~/.config/gpg-file-watcher/gdrive_credentials.json` |
| `google_drive_token_file` | Token storage | Leave as default |
| `google_drive_folder_id` | Upload destination | `null` for root, or folder ID |

**Note**: When `--google-drive` is used, the `destination_directory` setting is ignored and files go directly to Google Drive.

## That's It!

You now have:
- ✅ GPG encryption
- ✅ Automatic Google Drive upload
- ✅ Secure authentication
- ✅ Local and cloud copies

## More Information

- **Detailed setup**: [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md)
- **Quick reference**: [GOOGLE_DRIVE_QUICK_REF.md](GOOGLE_DRIVE_QUICK_REF.md)
- **Full docs**: [README.md](README.md)

## Common Use Cases

**Cloud-only storage (recommended)**:
```yaml
google_drive_folder_id: null  # Upload to root
```
Run with: `python3 gpg_file_watcher.py --google-drive`
Result: Encrypted files go directly to Google Drive, no local encrypted copies

**Organized cloud storage**:
```yaml
google_drive_folder_id: "your-folder-id"
```
Run with: `python3 gpg_file_watcher.py --google-drive`
Result: Encrypted files go to specific Drive folder

**Local storage only**:
```yaml
google_drive_enabled: false
```
Run with: `python3 gpg_file_watcher.py` (no --google-drive flag)
Result: Encrypted files saved to local destination_directory

**Want both local AND cloud?**
You'll need to run two separate instances:
- Instance 1: Without `--google-drive` (saves locally)
- Instance 2: With `--google-drive` (uploads to cloud)
- Use different watch directories for each

---

**Need Help?**
1. Check logs: `tail -f ~/.local/share/gpg-file-watcher/watcher.log`
2. Run with `--debug`: `python3 gpg_file_watcher.py --google-drive --debug`
3. See [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) for detailed troubleshooting

**Version**: 2.0.0  
**Author**: bva (scourgethetracker/bt7474)
