# GPG File Watcher

A Python3 wrapper that monitors a directory for new files and automatically encrypts them using GPG, then moves them to a destination directory. Designed for macOS with comprehensive error handling, structured logging, and configurable behavior.

## Features

- **Automatic File Monitoring**: Watches a specified directory for new files in real-time
- **GPG Encryption**: Encrypts files using your GPG key automatically
- **Google Drive Upload**: Optional automatic upload to Google Drive via API (v2.0)
- **Dropbox Upload**: Optional automatic upload to Dropbox via API (NEW in v2.1)
- **Configurable**: YAML-based configuration in `~/.config/gpg-file-watcher/`
- **File Extension Filtering**: Optional filtering by file extensions
- **Rich Console Output**: Beautiful terminal UI with status updates
- **Comprehensive Logging**: Structured logging with file and console output
- **Error Handling**: Robust error handling and validation
- **Conflict Resolution**: Handles duplicate filenames automatically

## Prerequisites

### macOS Requirements

1. **Python 3.12+** (requires Python 3.12 or later)
   ```bash
   python3 --version
   ```

2. **GPG (GnuPG)** - Install via Homebrew:
   ```bash
   brew install gnupg
   ```

3. **GPG Key Pair** - Generate if you don't have one:
   ```bash
   gpg --full-generate-key
   ```
   Follow the prompts to create your key. Use RSA with 4096 bits for maximum security.

4. **List your GPG keys** to find your key ID or email:
   ```bash
   gpg --list-keys
   ```

5. **Optional: Google Drive API Setup** (for Google Drive upload)
   - See [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) for detailed instructions
   - Requires Google Cloud Platform project and OAuth credentials
   - Skip this step if you don't need Google Drive upload

6. **Optional: Dropbox API Setup** (for Dropbox upload)
   - See [DROPBOX_SETUP.md](DROPBOX_SETUP.md) for detailed instructions
   - Requires Dropbox app and access token
   - Skip this step if you don't need Dropbox upload
   - **Note**: Cannot use both Google Drive and Dropbox simultaneously

## Installation

### 1. Clone or Download Files

Place the following files in a directory:
- `gpg_file_watcher.py`
- `requirements.txt`
- `config.yaml.example`

### 2. Install Python Dependencies

Using pip:
```bash
pip3 install -r requirements.txt
```

Or using a virtual environment (recommended):
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Create Configuration File

```bash
# Create config directory
mkdir -p ~/.config/gpg-file-watcher

# Copy example config
cp config.yaml.example ~/.config/gpg-file-watcher/config.yaml

# Edit configuration
nano ~/.config/gpg-file-watcher/config.yaml
```

### 4. Configure the Watcher

Edit `~/.config/gpg-file-watcher/config.yaml`:

```yaml
# Your GPG key (email, key ID, or fingerprint)
gpg_key_id: "your-email@example.com"

# Directory to watch for new files
watch_directory: "~/Documents/to_encrypt"

# Directory where encrypted files will be moved
destination_directory: "~/Documents/encrypted"

# Logging settings
log_level: "INFO"
log_file: "~/.local/share/gpg-file-watcher/watcher.log"

# Optional: Filter by extensions (null = watch all files)
file_extensions: null
# file_extensions: [".txt", ".pdf", ".docx"]

# Delete original file after encryption?
delete_original: true
```

### 5. Create Required Directories

```bash
# Create watch and destination directories
mkdir -p ~/Documents/to_encrypt
mkdir -p ~/Documents/encrypted

# Create log directory (if using file logging)
mkdir -p ~/.local/share/gpg-file-watcher
```

## Usage

### Running Manually

```bash
# Basic usage (no cloud storage)
python3 gpg_file_watcher.py

# With Google Drive upload
python3 gpg_file_watcher.py --google-drive

# With Dropbox upload
python3 gpg_file_watcher.py --dropbox

# Use custom config file
python3 gpg_file_watcher.py --config ~/my-config.yaml

# Cloud storage with custom config
python3 gpg_file_watcher.py --config ~/my-config.yaml --dropbox
```

Or if using a virtual environment:
```bash
source venv/bin/activate

# Basic usage
python3 gpg_file_watcher.py

# With cloud storage
python3 gpg_file_watcher.py --google-drive
# OR
python3 gpg_file_watcher.py --dropbox
```

### Running with Debug Output

```bash
python3 gpg_file_watcher.py --debug

# With cloud storage and debug
python3 gpg_file_watcher.py --dropbox --debug
```

### Command Line Arguments

- `--google-drive`: Enable Google Drive upload (requires configuration)
- `--dropbox`: Enable Dropbox upload (requires configuration)
- `--config PATH`: Use custom configuration file
- `--debug`: Enable debug mode with verbose output
- `--help`: Show help message

**Note**: Cannot use both `--google-drive` and `--dropbox` simultaneously. Choose one cloud provider.

### Running as a Background Service

#### Option 1: Using launchd (macOS Native)

Create a Launch Agent plist file at `~/Library/LaunchAgents/com.user.gpg-file-watcher.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.gpg-file-watcher</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/gpg_file_watcher.py</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/tmp/gpg-file-watcher.stdout</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/gpg-file-watcher.stderr</string>
</dict>
</plist>
```

Then load the service:
```bash
# Load the service
launchctl load ~/Library/LaunchAgents/com.user.gpg-file-watcher.plist

# Verify it's running
launchctl list | grep gpg-file-watcher

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.user.gpg-file-watcher.plist
```

#### Option 2: Using tmux/screen

```bash
# Start a tmux session
tmux new -s gpg-watcher

# Run the script
python3 gpg_file_watcher.py

# Detach from session: Press Ctrl+B, then D

# Reattach later
tmux attach -t gpg-watcher
```

#### Option 3: Using nohup

```bash
# Run in background
nohup python3 gpg_file_watcher.py > /tmp/gpg-watcher.log 2>&1 &

# Check if running
ps aux | grep gpg_file_watcher

# Stop the process
pkill -f gpg_file_watcher.py
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_gpg_file_watcher.py -v

# Run with coverage report
pytest test_gpg_file_watcher.py -v --cov=gpg_file_watcher --cov-report=term-missing

# Run specific test class
pytest test_gpg_file_watcher.py::TestConfig -v
```

## Configuration Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `gpg_key_id` | string | Yes | GPG key ID, fingerprint, or email |
| `watch_directory` | string | Yes | Directory to monitor for new files |
| `destination_directory` | string | Yes | Where to move encrypted files (when NOT using cloud storage) |
| `log_level` | string | No | DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO) |
| `log_file` | string | No | Path to log file (optional) |
| `file_extensions` | list | No | File extensions to watch (null = all files) |
| `gpg_home` | string | No | Custom GPG home directory (optional) |
| `delete_original` | boolean | No | Delete original after encryption (default: true) |
| `google_drive_enabled` | boolean | No | Enable Google Drive upload (default: false) |
| `google_drive_folder_id` | string | No | Google Drive folder ID (null = root folder) |
| `google_drive_credentials_file` | string | No* | Path to Google Drive credentials JSON (* required if enabled) |
| `google_drive_token_file` | string | No | Path to store auth token (auto-generated) |
| `dropbox_enabled` | boolean | No | Enable Dropbox upload (default: false) |
| `dropbox_access_token` | string | No* | Dropbox API access token (* required if enabled) |
| `dropbox_folder_path` | string | No | Dropbox folder path (default: "/") |

**Important**: 
- When using `--google-drive` or `--dropbox` flags, encrypted files are uploaded directly to cloud storage and are NOT saved to `destination_directory`. 
- Cannot enable both Google Drive and Dropbox simultaneously - choose one.

## How It Works

### Without Cloud Storage (Local Storage)
1. **Initialization**: The script loads configuration and validates all settings
2. **GPG Verification**: Verifies the specified GPG key exists
3. **Directory Monitoring**: Uses watchdog to monitor the watch directory
4. **File Detection**: When a new file appears:
   - Checks if it matches extension filter (if configured)
   - Waits briefly to ensure file is fully written
   - Reads the file content
5. **Encryption**: Encrypts the file using GPG with the specified key
6. **Local Storage**: Moves encrypted file (with .gpg extension) to destination directory
7. **Cleanup**: Optionally deletes the original unencrypted file

### With Google Drive (Cloud Storage)
1. **Initialization**: Same as above, plus Google Drive OAuth authentication
2. **GPG Verification**: Verifies the specified GPG key exists
3. **Directory Monitoring**: Uses watchdog to monitor the watch directory
4. **File Detection**: Same as above
5. **Encryption**: Encrypts the file using GPG with the specified key
6. **Cloud Upload**: Uploads encrypted file directly to Google Drive
7. **Cleanup**: Deletes local encrypted file after successful upload, plus optionally deletes original unencrypted file

### With Dropbox (Cloud Storage)
1. **Initialization**: Same as above, plus Dropbox access token authentication
2. **GPG Verification**: Verifies the specified GPG key exists
3. **Directory Monitoring**: Uses watchdog to monitor the watch directory
4. **File Detection**: Same as above
5. **Encryption**: Encrypts the file using GPG with the specified key
6. **Cloud Upload**: Uploads encrypted file directly to Dropbox
7. **Cleanup**: Deletes local encrypted file after successful upload, plus optionally deletes original unencrypted file

**Key Difference**: When using `--google-drive` or `--dropbox`, encrypted files go directly to cloud storage without being saved to the local destination directory.

## Troubleshooting

### GPG Key Not Found

```bash
# List all available GPG keys
gpg --list-keys

# List secret keys
gpg --list-secret-keys

# Import a key if needed
gpg --import path/to/key.asc
```

### Permission Denied Errors

```bash
# Check directory permissions
ls -la ~/Documents/to_encrypt
ls -la ~/Documents/encrypted

# Fix permissions if needed
chmod 755 ~/Documents/to_encrypt
chmod 755 ~/Documents/encrypted
```

### Files Not Being Detected

1. Verify the watch directory path in config
2. Check log file for errors: `~/.local/share/gpg-file-watcher/watcher.log`
3. Run with DEBUG log level to see detailed output
4. Ensure file extensions match filter (if configured)

### Encryption Fails

1. Verify GPG key is valid: `gpg --list-keys`
2. Test GPG encryption manually:
   ```bash
   echo "test" | gpg --encrypt --recipient your-email@example.com
   ```
3. Check GPG agent is running: `gpg-agent`
4. Restart GPG agent: `gpgconf --kill gpg-agent`

### Google Drive Issues

**Authentication Fails**:
```bash
# Delete token and re-authenticate
rm ~/.config/gpg-file-watcher/gdrive_token.json
python3 gpg_file_watcher.py --google-drive
```

**Upload Fails**:
1. Check credentials file exists and is valid
2. Verify Google Drive API is enabled in Cloud Console
3. Check folder ID is correct (if specified)
4. Review logs: `tail -f ~/.local/share/gpg-file-watcher/watcher.log`

**"Google hasn't verified this app" warning**:
- This is normal for personal projects
- Click "Advanced" → "Go to GPG File Watcher (unsafe)"
- The app is safe because you created and control it

**Missing Google Drive libraries**:
```bash
pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Dropbox Issues

**Invalid Access Token**:
```bash
# Verify token is correct (no extra spaces)
# Generate new token if needed
# Go to: https://www.dropbox.com/developers/apps
```

**Upload Fails**:
1. Check access token is set correctly in config
2. Verify app permissions are enabled (files.metadata.write, files.content.write)
3. Check folder path format (must start with "/")
4. Review logs: `tail -f ~/.local/share/gpg-file-watcher/watcher.log`

**Permission Denied**:
1. Go to app Permissions tab in Dropbox App Console
2. Enable required permissions
3. Click Submit
4. Generate NEW access token (old one won't get new permissions)

**Missing Dropbox library**:
```bash
pip3 install dropbox
```

**Cannot Use Both Google Drive and Dropbox**:
- This is by design
- Choose one cloud provider
- Use either `--google-drive` OR `--dropbox`, not both

For detailed Dropbox setup, see [DROPBOX_SETUP.md](DROPBOX_SETUP.md)

## Security Considerations

- **Key Security**: Ensure your GPG private key is properly secured with a passphrase
- **File Permissions**: Set appropriate permissions on watch and destination directories
- **Log Files**: Log files may contain filenames; secure accordingly
- **Original Files**: Consider the `delete_original` setting based on your security requirements
- **Network Storage**: Be cautious when using network-mounted directories

## Uninstallation

```bash
# Stop any running instances
pkill -f gpg_file_watcher.py

# Remove launchd service (if configured)
launchctl unload ~/Library/LaunchAgents/com.user.gpg-file-watcher.plist
rm ~/Library/LaunchAgents/com.user.gpg-file-watcher.plist

# Remove configuration
rm -rf ~/.config/gpg-file-watcher

# Remove logs
rm -rf ~/.local/share/gpg-file-watcher

# Remove virtual environment (if used)
rm -rf venv

# Uninstall Python packages (if not using virtual environment)
pip3 uninstall -y watchdog python-gnupg pydantic PyYAML rich
```

## License

This script is provided as-is for personal and commercial use.

## Author

@author: bva (scourgethetracker/bt7474)  
@version: 1.0.0  
@date: 2025-10-28

## Support

For issues, questions, or contributions, please refer to the source repository or contact the author.
