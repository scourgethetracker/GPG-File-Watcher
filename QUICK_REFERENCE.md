# GPG File Watcher - Quick Command Reference

## Three Storage Modes

GPG File Watcher supports three distinct storage modes. Choose one based on your needs.

## 🗂️ Mode 1: Local Storage (Default)

### When to Use
- Want encrypted files on local disk
- No internet/cloud needed
- Maximum privacy and control
- Fast performance

### Command
```bash
python3 gpg_file_watcher.py
```

### Workflow
```
File → Encrypt → Save to destination_directory
```

### Result
- ✅ Encrypted file in local `destination_directory`
- ✅ Original file deleted (if configured)
- ❌ No cloud backup

### Configuration
```yaml
# No cloud settings needed, use defaults:
watch_directory: "~/Documents/to_encrypt"
destination_directory: "~/Documents/encrypted"
google_drive_enabled: false
dropbox_enabled: false
```

---

## ☁️ Mode 2: Google Drive (Cloud-Only)

### When to Use
- Want cloud backup
- Have Google account with Drive
- Need OAuth 2.0 security
- 15 GB free storage
- Access from anywhere

### Command
```bash
python3 gpg_file_watcher.py --google-drive
```

### Workflow
```
File → Encrypt → Upload to Google Drive → Delete local encrypted
```

### Result
- ✅ Encrypted file in Google Drive
- ✅ Original file deleted (if configured)
- ❌ No local encrypted copy

### Configuration
```yaml
google_drive_enabled: true
google_drive_credentials_file: "~/.config/gpg-file-watcher/gdrive_credentials.json"
google_drive_token_file: "~/.config/gpg-file-watcher/gdrive_token.json"
google_drive_folder_id: null  # or "folder-id"
```

### Setup Time
~15 minutes (OAuth setup, browser auth)

---

## 📦 Mode 3: Dropbox (Cloud-Only)

### When to Use
- Want cloud backup
- Have Dropbox account
- Prefer simple access token auth
- 2 GB free storage
- Access from anywhere

### Command
```bash
python3 gpg_file_watcher.py --dropbox
```

### Workflow
```
File → Encrypt → Upload to Dropbox → Delete local encrypted
```

### Result
- ✅ Encrypted file in Dropbox
- ✅ Original file deleted (if configured)
- ❌ No local encrypted copy

### Configuration
```yaml
dropbox_enabled: true
dropbox_access_token: "sl.your-token-here"
dropbox_folder_path: "/"  # or "/encrypted"
```

### Setup Time
~5 minutes (get access token, paste in config)

---

## 📊 Quick Comparison

| Feature | Local | Google Drive | Dropbox |
|---------|-------|--------------|---------|
| **Command** | `python3 gpg_file_watcher.py` | `--google-drive` | `--dropbox` |
| **Setup** | None | ~15 min | ~5 min |
| **Auth** | None | OAuth 2.0 | Access Token |
| **Internet** | ❌ Not needed | ✅ Required | ✅ Required |
| **Free Storage** | Unlimited | 15 GB | 2 GB |
| **Speed** | Fastest | Fast | Fast |
| **Local Copy** | ✅ Yes | ❌ No | ❌ No |
| **Cloud Copy** | ❌ No | ✅ Yes | ✅ Yes |
| **Access Anywhere** | ❌ No | ✅ Yes | ✅ Yes |

---

## 🚫 Important Rules

### Cannot Use Both Cloud Services
```bash
# ❌ This will error:
python3 gpg_file_watcher.py --google-drive --dropbox

# ✅ Choose one:
python3 gpg_file_watcher.py --google-drive
# OR
python3 gpg_file_watcher.py --dropbox
```

### Cloud Modes Skip Local Destination
When using `--google-drive` or `--dropbox`:
- Files go **directly** to cloud
- `destination_directory` is **ignored**
- No local encrypted copies created

---

## 💡 Common Scenarios

### Scenario 1: Maximum Privacy
**Goal**: Keep everything local, no cloud

**Solution**:
```bash
python3 gpg_file_watcher.py
```

**Config**:
```yaml
watch_directory: "~/sensitive"
destination_directory: "~/encrypted"
google_drive_enabled: false
dropbox_enabled: false
```

---

### Scenario 2: Google Drive Backup
**Goal**: Automatic cloud backup with Google Drive

**Solution**:
```bash
python3 gpg_file_watcher.py --google-drive
```

**Config**:
```yaml
watch_directory: "~/Documents/to_backup"
google_drive_enabled: true
google_drive_credentials_file: "~/.config/gpg-file-watcher/gdrive_credentials.json"
google_drive_folder_id: null  # Root folder
```

**Prerequisites**:
1. Google Cloud project created
2. Drive API enabled
3. OAuth credentials downloaded
4. First-time browser authentication completed

---

### Scenario 3: Dropbox Backup
**Goal**: Simple cloud backup with Dropbox

**Solution**:
```bash
python3 gpg_file_watcher.py --dropbox
```

**Config**:
```yaml
watch_directory: "~/Documents/to_backup"
dropbox_enabled: true
dropbox_access_token: "sl.xxxxxxxxxxxxx"
dropbox_folder_path: "/"
```

**Prerequisites**:
1. Dropbox app created
2. Access token generated
3. Token added to config file

---

### Scenario 4: Both Local AND Cloud
**Goal**: Keep local encrypted copies AND upload to cloud

**Solution**: Run two instances

**Instance 1 - Local**:
```bash
# Terminal 1
python3 gpg_file_watcher.py --config config-local.yaml
```

**config-local.yaml**:
```yaml
watch_directory: "~/Documents/to_encrypt_local"
destination_directory: "~/Documents/encrypted"
google_drive_enabled: false
dropbox_enabled: false
```

**Instance 2 - Cloud (Dropbox example)**:
```bash
# Terminal 2
python3 gpg_file_watcher.py --config config-dropbox.yaml --dropbox
```

**config-dropbox.yaml**:
```yaml
watch_directory: "~/Documents/to_encrypt_cloud"
dropbox_enabled: true
dropbox_access_token: "sl.xxxxx"
dropbox_folder_path: "/"
```

**Result**: Drop files in `to_encrypt_local` for local storage, or in `to_encrypt_cloud` for Dropbox upload.

---

## 🔧 Advanced Commands

### Custom Config File
```bash
# Use custom config location
python3 gpg_file_watcher.py --config ~/my-custom-config.yaml

# With cloud service
python3 gpg_file_watcher.py --config ~/my-config.yaml --dropbox
```

### Debug Mode
```bash
# See detailed logs
python3 gpg_file_watcher.py --debug

# With cloud service
python3 gpg_file_watcher.py --dropbox --debug
```

### Help
```bash
# Show all options
python3 gpg_file_watcher.py --help
```

---

## 🎯 Decision Tree

```
Need cloud backup?
  │
  ├─ No → Use Local Mode (no flag)
  │       Fast, private, no setup
  │
  └─ Yes → Choose cloud provider:
      │
      ├─ Have Google account?
      │   └─ Yes → Use Google Drive (--google-drive)
      │            15 GB free, OAuth 2.0
      │
      └─ Have Dropbox account?
          └─ Yes → Use Dropbox (--dropbox)
                   2 GB free, simple token auth
```

---

## 📝 Quick Setup Summary

### Local Storage (0 minutes)
```bash
# Already works out of the box
python3 gpg_file_watcher.py
```

### Google Drive (~15 minutes)
```bash
# 1. Create Google Cloud project
# 2. Enable Drive API
# 3. Download OAuth credentials
# 4. Run and authenticate in browser
python3 gpg_file_watcher.py --google-drive
```

### Dropbox (~5 minutes)
```bash
# 1. Create Dropbox app
# 2. Generate access token
# 3. Add token to config
python3 gpg_file_watcher.py --dropbox
```

---

## 🔗 Documentation Links

- **Local Setup**: README.md
- **Google Drive**: GOOGLE_DRIVE_SETUP.md, GOOGLE_DRIVE_QUICK_REF.md
- **Dropbox**: DROPBOX_SETUP.md, DROPBOX_QUICK_START.md
- **Full Docs**: README.md

---

## ⚡ One-Line Commands

```bash
# Local only
python3 gpg_file_watcher.py

# Google Drive
python3 gpg_file_watcher.py --google-drive

# Dropbox
python3 gpg_file_watcher.py --dropbox

# Custom config + Dropbox
python3 gpg_file_watcher.py --config ~/my.yaml --dropbox

# Debug mode
python3 gpg_file_watcher.py --dropbox --debug

# Help
python3 gpg_file_watcher.py --help
```

---

**Version**: 2.1.0  
**Updated**: 2025-10-29  
**Author**: bva (scourgethetracker/bt7474)
