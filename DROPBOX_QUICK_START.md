# Dropbox Integration - 3-Minute Quick Start

Get Dropbox upload working in 3 minutes.

## Before You Start

✅ You have GPG File Watcher v2.1 installed and working
✅ You have a Dropbox account
✅ 5 minutes for Dropbox app setup

## Step 1: Create Dropbox App (~2 minutes)

### 1.1 Go to App Console
https://www.dropbox.com/developers/apps

### 1.2 Create App
1. Click **Create app**
2. Choose **Scoped access**
3. Choose **Full Dropbox**
4. Name: "GPG File Watcher"
5. Click **Create app**

### 1.3 Set Permissions
1. Click **Permissions** tab
2. Enable:
   - ✅ `files.metadata.write`
   - ✅ `files.content.write`
   - ✅ `files.content.read`
3. Click **Submit**

### 1.4 Generate Token
1. Click **Settings** tab
2. Scroll to **Generated access token**
3. Click **Generate**
4. **Copy the token** (starts with `sl.B...`)

## Step 2: Install Dropbox Library (~30 seconds)

```bash
pip3 install dropbox
```

## Step 3: Update Configuration (~1 minute)

Edit your config file:

```bash
nano ~/.config/gpg-file-watcher/config.yaml
```

Add at the end:

```yaml
# Dropbox Configuration
dropbox_enabled: true
dropbox_access_token: "sl.B...PASTE-YOUR-TOKEN-HERE..."
dropbox_folder_path: "/"
```

Save (Ctrl+O, Enter, Ctrl+X)

## Step 4: Run (~30 seconds)

```bash
python3 gpg_file_watcher.py --dropbox
```

**You should see:**
```
✓ Dropbox connected successfully
```

## Step 5: Test (~30 seconds)

Keep the app running, open new terminal:

```bash
# Create test file
echo "Test content" > ~/Documents/to_encrypt/test.txt

# Watch output - you should see:
# ✓ Successfully encrypted: test.txt
# ✓ Uploaded to Dropbox: test.txt.gpg
```

Check your Dropbox - you should see `test.txt.gpg`!

## Troubleshooting

### "Dropbox library not installed"
```bash
pip3 install dropbox
```

### "Invalid access token"
1. Go back to app console
2. Generate new token
3. Copy entire token (no spaces)
4. Update config

### "Permission denied"
1. Go to app **Permissions** tab
2. Enable all required permissions
3. Click **Submit**
4. Generate **NEW** token (important!)

### Upload to specific folder
1. Create folder in Dropbox (e.g., "encrypted")
2. Update config:
   ```yaml
   dropbox_folder_path: "/encrypted"
   ```
3. Restart app

## Command Quick Reference

```bash
# Basic (no Dropbox)
python3 gpg_file_watcher.py

# With Dropbox
python3 gpg_file_watcher.py --dropbox

# Debug mode
python3 gpg_file_watcher.py --dropbox --debug

# Custom config
python3 gpg_file_watcher.py --config ~/my-config.yaml --dropbox

# Help
python3 gpg_file_watcher.py --help
```

## Configuration Quick Reference

| Setting | What It Does | Example |
|---------|-------------|---------|
| `dropbox_enabled` | Enable/disable | `true` or use `--dropbox` flag |
| `dropbox_access_token` | Your access token | `"sl.B..."` |
| `dropbox_folder_path` | Upload destination | `"/"` or `"/encrypted"` |

**Important**: When `--dropbox` is used, files go directly to Dropbox and are NOT saved to local `destination_directory`.

## Common Use Cases

**Cloud-only storage**:
```yaml
dropbox_folder_path: "/"
```
Run: `python3 gpg_file_watcher.py --dropbox`

**Organized storage**:
```yaml
dropbox_folder_path: "/backups/encrypted"
```
Run: `python3 gpg_file_watcher.py --dropbox`

**Local storage only**:
```yaml
dropbox_enabled: false
```
Run: `python3 gpg_file_watcher.py`

## Security Tips

```bash
# Protect your config file
chmod 600 ~/.config/gpg-file-watcher/config.yaml

# Never commit token to git
echo "config.yaml" >> .gitignore

# Revoke token if compromised
# Go to app console → Settings → Revoke token
```

## Dropbox vs Google Drive

| Feature | Dropbox | Google Drive |
|---------|---------|--------------|
| Setup Time | 3 min | 10 min |
| Auth Type | Token | OAuth 2.0 |
| Browser Needed | No | Yes |
| Complexity | Simple | Moderate |

## Next Steps

### Run in background
```bash
nohup python3 gpg_file_watcher.py --dropbox > /tmp/gpg-watcher.log 2>&1 &
```

### Auto-start on login
See README.md for LaunchAgent setup

### Switch to different folder
Edit config and change `dropbox_folder_path`

## That's It!

You now have:
- ✅ GPG encryption
- ✅ Automatic Dropbox upload
- ✅ Secure access token auth
- ✅ Cloud-only storage

## More Information

- **Detailed setup**: [DROPBOX_SETUP.md](DROPBOX_SETUP.md)
- **Full docs**: [README.md](README.md)
- **Troubleshooting**: Run with `--debug` flag

---

**Need Help?**
1. Check logs: `tail -f ~/.local/share/gpg-file-watcher/watcher.log`
2. Run with `--debug`
3. See [DROPBOX_SETUP.md](DROPBOX_SETUP.md)

**Version**: 2.1.0  
**Author**: bva (scourgethetracker/bt7474)
