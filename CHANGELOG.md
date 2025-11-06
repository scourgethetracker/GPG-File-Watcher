# Changelog

All notable changes to GPG File Watcher will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-10-29

### Added
- **Dropbox API Integration**: Automatic upload of encrypted files to Dropbox
  - Access token authentication (simpler than OAuth)
  - Support for uploading to specific folders via folder path
  - Automatic folder creation if path doesn't exist
  - Chunked upload support for files >150MB
  - Comprehensive error handling for API failures
- **Command-Line Argument**:
  - `--dropbox`: Enable Dropbox upload (files go directly to cloud)
- **New Configuration Options**:
  - `dropbox_enabled`: Toggle Dropbox functionality
  - `dropbox_access_token`: Dropbox API access token for authentication
  - `dropbox_folder_path`: Target folder path for uploads
- **DropboxUploader Class**:
  - Handles authentication with access token
  - Provides file upload functionality
  - Folder access verification and creation
  - Support for large files via chunked upload
- **Mutual Exclusivity**: Prevents enabling both Google Drive and Dropbox simultaneously
- **Documentation**:
  - DROPBOX_SETUP.md: Complete setup guide for Dropbox API
  - DROPBOX_QUICK_START.md: 3-minute quick start guide
  - Updated README.md with Dropbox sections
  - Updated configuration examples

### Changed
- **Main Script Version**: Updated from 2.0.0 to 2.1.0
- **GPGFileHandler Class**: Enhanced to support Dropbox uploader
- **Configuration Model**: Added Dropbox fields to Config class
- **Requirements**: Added Dropbox Python SDK
- **Argument Parser**: Added `--dropbox` flag with examples

### Enhanced
- Startup validation prevents using both cloud services simultaneously
- Configuration display shows active cloud service (Google Drive, Dropbox, or None)
- Error messages specific to Dropbox API failures
- Console output includes Dropbox upload status with file paths
- Logging includes detailed Dropbox operation information

### Dependencies
- Added `dropbox>=11.36.0`

### Security
- Access token stored in config file with recommended 600 permissions
- Files encrypted before upload to Dropbox
- Scoped API permissions (files.metadata.write, files.content.write)
- No OAuth complexity - simpler token-based auth

### Notes
- Dropbox library is optional; script works without it if not using upload
- Access tokens don't expire by default (long-lived)
- Simpler setup than Google Drive (no OAuth flow)
- **Important**: Cannot use both Google Drive and Dropbox in same run

## [2.0.0] - 2025-10-29

### Added
- **Google Drive API Integration**: Automatic upload of encrypted files to Google Drive
  - OAuth 2.0 authentication with token caching
  - Support for uploading to specific folders via folder ID
  - Comprehensive error handling for API failures
  - Rate limiting and retry logic
- **Command-Line Arguments**:
  - `--google-drive`: Enable Google Drive upload (files go directly to cloud)
  - `--config PATH`: Specify custom configuration file location
  - `--debug`: Enable debug mode with verbose output
  - `--help`: Display help message with usage examples
- **New Configuration Options**:
  - `google_drive_enabled`: Toggle Google Drive functionality
  - `google_drive_folder_id`: Target folder for uploads
  - `google_drive_credentials_file`: Path to OAuth credentials
  - `google_drive_token_file`: Path to stored authentication token
- **GoogleDriveUploader Class**: 
  - Handles authentication and token management
  - Provides file upload functionality
  - Folder access verification
  - Automatic credential refresh
- **Documentation**:
  - GOOGLE_DRIVE_SETUP.md: Complete setup guide for Google Drive API
  - GOOGLE_DRIVE_QUICK_REF.md: Quick reference for common operations
  - QUICK_START_GDRIVE.md: 5-minute quick start guide
  - GOOGLE_DRIVE_FEATURE.md: Feature overview and use cases
  - Updated README.md with Google Drive sections
  - Updated configuration examples

### Changed
- **Workflow Behavior**: When `--google-drive` flag is used, encrypted files are uploaded directly to Google Drive and are NOT saved to `destination_directory`. This provides cloud-only storage.
- **Main Script Version**: Updated from 1.0.0 to 2.0.0
- **GPGFileHandler Class**: 
  - Split workflow into two paths: local vs cloud
  - Added `upload_to_google_drive()` method for direct cloud upload
  - Modified `move_encrypted_file()` to only handle local storage
  - Enhanced `process_file()` to route to appropriate workflow
- **Configuration Model**: Added Google Drive fields to Config class
- **Requirements**: Added Google API Python client libraries
- **Setup Script**: Added optional Google Drive configuration step
- **LaunchAgent Template**: Updated to support `--google-drive` flag

### Removed
- **Configuration Option**: `google_drive_delete_local` (no longer needed with direct upload)

### Enhanced
- Error messages now more descriptive for Google Drive failures
- Console output clearly indicates cloud-only vs local storage mode
- Logging includes detailed Google Drive operation information
- Configuration validation ensures Google Drive requirements met
- Startup message warns when files won't be saved locally

### Dependencies
- Added `google-api-python-client>=2.108.0`
- Added `google-auth-httplib2>=0.2.0`
- Added `google-auth-oauthlib>=1.2.0`

### Security
- OAuth 2.0 token stored securely with proper file permissions
- Limited OAuth scope: `https://www.googleapis.com/auth/drive.file`
- Credentials and token files protected with 600 permissions
- No plaintext storage of sensitive data

### Notes
- Google Drive libraries are optional; script works without them if not using upload
- First-time authentication requires user interaction via browser
- Token refresh is automatic when expired
- **Important**: Using `--google-drive` changes behavior - files go to cloud only, not local destination

## [1.0.0] - 2025-10-28

### Added
- **Initial Release**
- GPG encryption of files using python-gnupg
- Real-time directory monitoring with watchdog
- YAML-based configuration in `~/.config/gpg-file-watcher/`
- Comprehensive logging with rich formatting
- File extension filtering
- Configurable behaviors:
  - Watch directory
  - Destination directory
  - GPG key selection
  - Original file deletion
  - Custom GPG home directory
- Pydantic-based configuration validation
- Type hints throughout codebase
- Comprehensive error handling
- Rich console output with panels and colors
- Automatic handling of filename conflicts
- Support for multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Optional file logging
- macOS compatibility
- LaunchAgent template for running as service
- Automated setup script
- Comprehensive test suite with pytest
- Complete documentation:
  - README.md with installation and usage
  - config.yaml.example with all options
  - test_gpg_file_watcher.py with test cases
  - MANIFEST.md with file descriptions

### Features
- File system events handled efficiently
- GPG key validation before starting
- Safe file processing with waiting period
- Detailed logging of all operations
- Graceful shutdown on Ctrl+C
- Version information in header

### Code Quality
- Python 3.12+ compatible
- PEP8 compliant
- Type hints on all functions
- Comprehensive docstrings (Google style)
- Error handling with specific exception types
- Input validation and sanitization

### Documentation
- Complete README with examples
- Configuration file with inline comments
- Setup script with interactive prompts
- Test suite with multiple test cases
- File manifest for easy reference

## [Unreleased]

### Planned
- Support for multiple watch directories
- Email notifications on errors
- Web dashboard for monitoring
- Dropbox and OneDrive integration
- S3 bucket upload support
- Scheduled encryption jobs
- Compression before encryption option
- Multi-user support with separate configs
- Webhook notifications
- REST API for remote control

## Version History Summary

- **v2.1.0**: Added Dropbox integration with access token authentication
- **v2.0.0**: Added Google Drive integration, command-line arguments
- **v1.0.0**: Initial release with GPG encryption and directory watching

---

## Upgrade Guide

### From v2.0.0 to v2.1.0

No breaking changes. All v2.0.0 configurations continue to work.

**New Optional Feature - Dropbox:**

1. Install Dropbox library (optional):
   ```bash
   pip3 install dropbox
   ```

2. Get Dropbox access token:
   - Go to https://www.dropbox.com/developers/apps
   - Create app with "Scoped access" and "Full Dropbox"
   - Enable permissions: files.metadata.write, files.content.write
   - Generate access token
   - See [DROPBOX_SETUP.md](DROPBOX_SETUP.md) for detailed steps

3. Add Dropbox configuration to your config file (optional):
   ```yaml
   dropbox_enabled: false  # Set true or use --dropbox flag
   dropbox_access_token: "sl.B...your-token..."
   dropbox_folder_path: "/"  # or "/encrypted" for specific folder
   ```

4. Use new command-line argument (optional):
   ```bash
   # Enable Dropbox (cloud-only)
   python3 gpg_file_watcher.py --dropbox
   ```

**Choosing Between Google Drive and Dropbox:**
- **Cannot use both simultaneously** - pick one
- **Google Drive**: More complex setup (OAuth), better for enterprise
- **Dropbox**: Simpler setup (token), faster to get started
- Both work the same way: direct cloud upload, no local encrypted copies

**Backward Compatibility:**
- All v2.0.0 commands work without changes
- Google Drive functionality unchanged
- Dropbox is completely optional
- No configuration changes required to continue using v2.0.0 features

### From v1.0.0 to v2.0.0

No breaking changes for existing workflows. All v1.0.0 configurations continue to work.

**Important Behavioral Change:**
When using the new `--google-drive` flag, encrypted files are uploaded directly to Google Drive and are NOT saved to the local `destination_directory`. This is by design for cloud-only storage.

**To maintain v1.0 behavior (local storage only):**
- Simply don't use the `--google-drive` flag
- Run: `python3 gpg_file_watcher.py` (as before)
- Files continue going to `destination_directory`

**To use cloud-only storage:**
- Run: `python3 gpg_file_watcher.py --google-drive`
- Files go directly to Google Drive
- No local encrypted copies created

**To have BOTH local and cloud storage:**
- Run two separate instances with different configurations
- Or: Run once without flag (local), then manually upload from destination directory

**New Optional Features:**
1. Install Google Drive dependencies:
   ```bash
   pip3 install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. Add Google Drive configuration to your config file (optional):
   ```yaml
   google_drive_enabled: false  # Set true or use --google-drive flag
   google_drive_credentials_file: "~/.config/gpg-file-watcher/gdrive_credentials.json"
   google_drive_token_file: "~/.config/gpg-file-watcher/gdrive_token.json"
   google_drive_folder_id: null
   ```

3. Use new command-line arguments (optional):
   ```bash
   # Enable Google Drive (cloud-only)
   python3 gpg_file_watcher.py --google-drive
   
   # Custom config
   python3 gpg_file_watcher.py --config ~/my-config.yaml
   
   # Debug mode
   python3 gpg_file_watcher.py --debug
   ```

**Removed Configuration:**
- `google_drive_delete_local`: No longer needed. When using `--google-drive`, local encrypted files are automatically cleaned up after successful upload.

**Backward Compatibility:**
- All v1.0.0 commands work without changes
- Google Drive is disabled by default
- No configuration changes required to continue using v1.0.0 features
- The `destination_directory` setting still works (when not using `--google-drive`)

---

@author: bva (scourgethetracker/bt7474)
