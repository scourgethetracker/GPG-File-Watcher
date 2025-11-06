#!/usr/bin/env python3

"""
GPG File Watcher - Monitors directory for new files and encrypts them with GPG

Features:
* Watches a specified directory for new files using watchdog
* Automatically encrypts files using GPG with specified key
* Moves encrypted files to destination directory
* Optional Google Drive upload via API
* Optional Dropbox upload via API
* Configurable via YAML config file in ~/.config/gpg-file-watcher/
* Structured logging with file and console output
* Comprehensive error handling and validation

@author: bva (scourgethetracker/bt7474)
@version: 2.1.0
@date: 2025-10-29
@python-version: 3.12+

Version History:
* 2.1.0 (2025-10-29): Added Dropbox API integration
* 2.0.0 (2025-10-29): Added Google Drive API integration
* 1.0.0 (2025-10-28): Initial release
"""

import sys
import time
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import gnupg
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from pydantic import BaseModel, Field, field_validator, ValidationError

# Google Drive imports (optional)
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

# Dropbox imports (optional)
try:
    import dropbox
    from dropbox.files import WriteMode
    from dropbox.exceptions import ApiError, AuthError
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

# Dropbox imports (optional)
try:
    import dropbox
    from dropbox.files import WriteMode
    from dropbox.exceptions import ApiError, AuthError
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

# Dropbox imports (optional)
try:
    import dropbox
    from dropbox.exceptions import ApiError, AuthError
    from dropbox.files import WriteMode
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False


# Initialize rich console for formatted output
console = Console()


class Config(BaseModel):
    """Configuration model with validation."""
    
    gpg_key_id: str = Field(..., description="GPG key ID or email for encryption")
    watch_directory: Path = Field(..., description="Directory to watch for new files")
    destination_directory: Path = Field(..., description="Directory for encrypted files")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[Path] = Field(default=None, description="Optional log file path")
    file_extensions: Optional[list[str]] = Field(
        default=None, 
        description="List of file extensions to watch (e.g., ['.txt', '.pdf']). None = all files"
    )
    gpg_home: Optional[Path] = Field(
        default=None, 
        description="GPG home directory (defaults to system default)"
    )
    delete_original: bool = Field(
        default=True, 
        description="Delete original file after encryption"
    )
    
    # Google Drive settings
    google_drive_enabled: bool = Field(
        default=False,
        description="Enable Google Drive upload"
    )
    google_drive_folder_id: Optional[str] = Field(
        default=None,
        description="Google Drive folder ID for uploads (None = root)"
    )
    google_drive_credentials_file: Optional[Path] = Field(
        default=None,
        description="Path to Google Drive credentials JSON file"
    )
    google_drive_token_file: Optional[Path] = Field(
        default=None,
        description="Path to store Google Drive token"
    )
    
    # Dropbox settings
    dropbox_enabled: bool = Field(
        default=False,
        description="Enable Dropbox upload"
    )
    dropbox_access_token: Optional[str] = Field(
        default=None,
        description="Dropbox API access token"
    )
    dropbox_folder_path: Optional[str] = Field(
        default="/",
        description="Dropbox folder path for uploads (default: root /)"
    )
    
    # Dropbox settings
    dropbox_enabled: bool = Field(
        default=False,
        description="Enable Dropbox upload"
    )
    dropbox_access_token: Optional[str] = Field(
        default=None,
        description="Dropbox API access token"
    )
    dropbox_folder_path: Optional[str] = Field(
        default="/",
        description="Dropbox folder path for uploads (default: root)"
    )
    
    # Dropbox settings
    dropbox_enabled: bool = Field(
        default=False,
        description="Enable Dropbox upload"
    )
    dropbox_access_token: Optional[str] = Field(
        default=None,
        description="Dropbox API access token"
    )
    dropbox_folder_path: Optional[str] = Field(
        default="/",
        description="Dropbox folder path for uploads (e.g., /encrypted)"
    )
    
    @field_validator('watch_directory', 'destination_directory')
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        """Validate and expand directory paths."""
        expanded_path = Path(v).expanduser().resolve()
        if not expanded_path.exists():
            raise ValueError(f"Directory does not exist: {expanded_path}")
        if not expanded_path.is_dir():
            raise ValueError(f"Path is not a directory: {expanded_path}")
        return expanded_path
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    @field_validator('gpg_home')
    @classmethod
    def validate_gpg_home(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate GPG home directory."""
        if v is None:
            return None
        expanded_path = Path(v).expanduser().resolve()
        if not expanded_path.exists():
            raise ValueError(f"GPG home directory does not exist: {expanded_path}")
        return expanded_path
    
    @field_validator('dropbox_folder_path')
    @classmethod
    def validate_dropbox_folder_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate Dropbox folder path."""
        if v is None:
            return "/"
        # Ensure path starts with /
        if not v.startswith('/'):
            v = '/' + v
        # Remove trailing slash unless it's root
        if v != '/' and v.endswith('/'):
            v = v.rstrip('/')
        return v


class GoogleDriveUploader:
    """Handle Google Drive API authentication and file uploads."""
    
    # Google Drive API scopes
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(
        self, 
        config: Config, 
        logger: logging.Logger
    ) -> None:
        """
        Initialize Google Drive uploader.
        
        Args:
            config: Configuration object
            logger: Logger instance
            
        Raises:
            RuntimeError: If Google Drive libraries not available
            ValueError: If configuration is invalid
        """
        if not GOOGLE_DRIVE_AVAILABLE:
            raise RuntimeError(
                "Google Drive libraries not installed. "
                "Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
        
        self.config = config
        self.logger = logger
        self.service = None
        
        # Validate configuration
        if not config.google_drive_credentials_file:
            raise ValueError("google_drive_credentials_file must be set when Google Drive is enabled")
        
        credentials_path = Path(config.google_drive_credentials_file).expanduser().resolve()
        if not credentials_path.exists():
            raise ValueError(f"Google Drive credentials file not found: {credentials_path}")
        
        self.credentials_file = credentials_path
        
        # Token file location
        if config.google_drive_token_file:
            self.token_file = Path(config.google_drive_token_file).expanduser().resolve()
        else:
            self.token_file = Path.home() / '.config' / 'gpg-file-watcher' / 'gdrive_token.json'
        
        # Ensure token directory exists
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
    
    def authenticate(self) -> None:
        """
        Authenticate with Google Drive API.
        
        Raises:
            RuntimeError: If authentication fails
        """
        try:
            creds = None
            
            # Load existing token if available
            if self.token_file.exists():
                self.logger.info(f"Loading existing Google Drive token from: {self.token_file}")
                creds = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing Google Drive credentials")
                    creds.refresh(Request())
                else:
                    self.logger.info("Starting Google Drive OAuth flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), 
                        self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(self.token_file, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
                self.logger.info(f"Saved Google Drive token to: {self.token_file}")
            
            # Build service
            self.service = build('drive', 'v3', credentials=creds)
            self.logger.info("Successfully authenticated with Google Drive")
        
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Google Drive: {e}", exc_info=True)
            raise RuntimeError(f"Google Drive authentication failed: {e}") from e
    
    def upload_file(
        self, 
        file_path: Path, 
        folder_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to file to upload
            folder_id: Optional folder ID to upload to
            
        Returns:
            File ID on success, None on failure
        """
        try:
            if not self.service:
                raise RuntimeError("Not authenticated with Google Drive")
            
            self.logger.info(f"Uploading to Google Drive: {file_path.name}")
            
            # Prepare file metadata
            file_metadata: Dict[str, Any] = {
                'name': file_path.name
            }
            
            # Set parent folder if specified
            if folder_id:
                file_metadata['parents'] = [folder_id]
            elif self.config.google_drive_folder_id:
                file_metadata['parents'] = [self.config.google_drive_folder_id]
            
            # Create media upload
            media = MediaFileUpload(
                str(file_path),
                mimetype='application/octet-stream',
                resumable=True
            )
            
            # Upload file
            file_obj = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            file_id = file_obj.get('id')
            web_link = file_obj.get('webViewLink', 'N/A')
            
            self.logger.info(
                f"Successfully uploaded to Google Drive: {file_path.name} "
                f"(ID: {file_id}, Link: {web_link})"
            )
            
            return file_id
        
        except HttpError as e:
            self.logger.error(
                f"Google Drive API error uploading {file_path}: {e}",
                exc_info=True
            )
            return None
        
        except Exception as e:
            self.logger.error(
                f"Failed to upload {file_path} to Google Drive: {e}",
                exc_info=True
            )
            return None
    
    def verify_folder_access(self, folder_id: str) -> bool:
        """
        Verify that the specified folder exists and is accessible.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            if not self.service:
                raise RuntimeError("Not authenticated with Google Drive")
            
            folder = self.service.files().get(
                fileId=folder_id,
                fields='id, name, mimeType'
            ).execute()
            
            if folder.get('mimeType') != 'application/vnd.google-apps.folder':
                self.logger.error(f"ID {folder_id} is not a folder")
                return False
            
            self.logger.info(f"Verified access to Google Drive folder: {folder.get('name')}")
            return True
        
        except HttpError as e:
            self.logger.error(f"Cannot access Google Drive folder {folder_id}: {e}")
            return False
        
        except Exception as e:
            self.logger.error(f"Error verifying folder access: {e}", exc_info=True)
            return False


class DropboxUploader:
    """Handle Dropbox API authentication and file uploads."""
    
    def __init__(
        self, 
        config: Config, 
        logger: logging.Logger
    ) -> None:
        """
        Initialize Dropbox uploader.
        
        Args:
            config: Configuration object
            logger: Logger instance
            
        Raises:
            RuntimeError: If Dropbox library not available
            ValueError: If configuration is invalid
        """
        if not DROPBOX_AVAILABLE:
            raise RuntimeError(
                "Dropbox library not installed. "
                "Install with: pip install dropbox"
            )
        
        self.config = config
        self.logger = logger
        self.dbx = None
        
        # Validate configuration
        if not config.dropbox_access_token:
            raise ValueError("dropbox_access_token must be set when Dropbox is enabled")
        
        self.access_token = config.dropbox_access_token
        self.folder_path = config.dropbox_folder_path or "/"
        
        # Ensure folder path starts with /
        if not self.folder_path.startswith('/'):
            self.folder_path = '/' + self.folder_path
        
        # Remove trailing slash unless it's root
        if self.folder_path != '/' and self.folder_path.endswith('/'):
            self.folder_path = self.folder_path.rstrip('/')
    
    def authenticate(self) -> None:
        """
        Authenticate with Dropbox API using access token.
        
        Raises:
            RuntimeError: If authentication fails
        """
        try:
            self.logger.info("Authenticating with Dropbox...")
            self.dbx = dropbox.Dropbox(self.access_token)
            
            # Test authentication by getting account info
            account = self.dbx.users_get_current_account()
            self.logger.info(
                f"Successfully authenticated with Dropbox as: {account.name.display_name} "
                f"({account.email})"
            )
        
        except AuthError as e:
            self.logger.error(f"Dropbox authentication failed: {e}", exc_info=True)
            raise RuntimeError(f"Dropbox authentication failed: {e}") from e
        
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Dropbox: {e}", exc_info=True)
            raise RuntimeError(f"Dropbox authentication failed: {e}") from e
    
    def upload_file(
        self, 
        file_path: Path, 
        folder_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to Dropbox.
        
        Args:
            file_path: Path to file to upload
            folder_path: Optional folder path to upload to
            
        Returns:
            File path in Dropbox on success, None on failure
        """
        try:
            if not self.dbx:
                raise RuntimeError("Not authenticated with Dropbox")
            
            self.logger.info(f"Uploading to Dropbox: {file_path.name}")
            
            # Determine target path
            target_folder = folder_path if folder_path else self.folder_path
            if target_folder == '/':
                dropbox_path = f"/{file_path.name}"
            else:
                dropbox_path = f"{target_folder}/{file_path.name}"
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload file
            file_size = len(file_data)
            
            if file_size <= 150 * 1024 * 1024:  # 150 MB limit for single upload
                # Use regular upload for files under 150 MB
                result = self.dbx.files_upload(
                    file_data,
                    dropbox_path,
                    mode=WriteMode('overwrite'),
                    autorename=True
                )
            else:
                # Use upload session for larger files
                self.logger.info(f"Large file detected ({file_size} bytes), using chunked upload")
                CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB chunks
                
                # Start upload session
                session_start = self.dbx.files_upload_session_start(file_data[:CHUNK_SIZE])
                cursor = dropbox.files.UploadSessionCursor(
                    session_id=session_start.session_id,
                    offset=CHUNK_SIZE
                )
                
                # Upload chunks
                while cursor.offset < file_size:
                    chunk_end = min(cursor.offset + CHUNK_SIZE, file_size)
                    chunk = file_data[cursor.offset:chunk_end]
                    
                    if chunk_end == file_size:
                        # Final chunk
                        commit = dropbox.files.CommitInfo(
                            path=dropbox_path,
                            mode=WriteMode('overwrite'),
                            autorename=True
                        )
                        result = self.dbx.files_upload_session_finish(chunk, cursor, commit)
                    else:
                        # Intermediate chunk
                        self.dbx.files_upload_session_append_v2(chunk, cursor)
                        cursor.offset = chunk_end
            
            self.logger.info(
                f"Successfully uploaded to Dropbox: {file_path.name} "
                f"(Path: {result.path_display})"
            )
            
            return result.path_display
        
        except ApiError as e:
            self.logger.error(
                f"Dropbox API error uploading {file_path}: {e}",
                exc_info=True
            )
            return None
        
        except Exception as e:
            self.logger.error(
                f"Failed to upload {file_path} to Dropbox: {e}",
                exc_info=True
            )
            return None
    
    def verify_folder_access(self, folder_path: str) -> bool:
        """
        Verify that the specified folder exists and is accessible.
        
        Args:
            folder_path: Dropbox folder path
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            if not self.dbx:
                raise RuntimeError("Not authenticated with Dropbox")
            
            # Root folder always exists
            if folder_path == '/':
                return True
            
            # Try to get folder metadata
            try:
                metadata = self.dbx.files_get_metadata(folder_path)
                
                if isinstance(metadata, dropbox.files.FolderMetadata):
                    self.logger.info(f"Verified access to Dropbox folder: {folder_path}")
                    return True
                else:
                    self.logger.error(f"Path {folder_path} is not a folder")
                    return False
            
            except ApiError as e:
                if e.error.is_path() and e.error.get_path().is_not_found():
                    # Folder doesn't exist, try to create it
                    self.logger.info(f"Folder {folder_path} doesn't exist, creating it...")
                    try:
                        self.dbx.files_create_folder_v2(folder_path)
                        self.logger.info(f"Created Dropbox folder: {folder_path}")
                        return True
                    except Exception as create_error:
                        self.logger.error(f"Failed to create folder {folder_path}: {create_error}")
                        return False
                else:
                    raise
        
        except Exception as e:
            self.logger.error(f"Error verifying folder access: {e}", exc_info=True)
            return False


class DropboxUploader:
    """Handle Dropbox API authentication and file uploads."""
    
    def __init__(
        self, 
        config: Config, 
        logger: logging.Logger
    ) -> None:
        """
        Initialize Dropbox uploader.
        
        Args:
            config: Configuration object
            logger: Logger instance
            
        Raises:
            RuntimeError: If Dropbox library not available
            ValueError: If configuration is invalid
        """
        if not DROPBOX_AVAILABLE:
            raise RuntimeError(
                "Dropbox library not installed. "
                "Install with: pip install dropbox"
            )
        
        self.config = config
        self.logger = logger
        self.dbx = None
        
        # Validate configuration
        if not config.dropbox_access_token:
            raise ValueError("dropbox_access_token must be set when Dropbox is enabled")
        
        self.access_token = config.dropbox_access_token
        self.folder_path = config.dropbox_folder_path or "/"
    
    def authenticate(self) -> None:
        """
        Authenticate with Dropbox API using access token.
        
        Raises:
            RuntimeError: If authentication fails
        """
        try:
            self.logger.info("Authenticating with Dropbox...")
            self.dbx = dropbox.Dropbox(self.access_token)
            
            # Verify authentication by getting account info
            account = self.dbx.users_get_current_account()
            self.logger.info(
                f"Successfully authenticated with Dropbox as: {account.name.display_name} "
                f"({account.email})"
            )
        
        except AuthError as e:
            self.logger.error(f"Dropbox authentication failed: {e}", exc_info=True)
            raise RuntimeError(
                f"Dropbox authentication failed: {e}\n"
                "Please check your access token is valid."
            ) from e
        
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Dropbox: {e}", exc_info=True)
            raise RuntimeError(f"Dropbox authentication failed: {e}") from e
    
    def upload_file(
        self, 
        file_path: Path, 
        folder_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to Dropbox.
        
        Args:
            file_path: Path to file to upload
            folder_path: Optional folder path to upload to
            
        Returns:
            File path in Dropbox on success, None on failure
        """
        try:
            if not self.dbx:
                raise RuntimeError("Not authenticated with Dropbox")
            
            self.logger.info(f"Uploading to Dropbox: {file_path.name}")
            
            # Determine destination path
            upload_folder = folder_path or self.folder_path
            if upload_folder == '/':
                dropbox_path = f"/{file_path.name}"
            else:
                dropbox_path = f"{upload_folder}/{file_path.name}"
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload file
            # Use WriteMode.overwrite to handle existing files
            result = self.dbx.files_upload(
                file_data,
                dropbox_path,
                mode=WriteMode('overwrite'),
                autorename=False
            )
            
            self.logger.info(
                f"Successfully uploaded to Dropbox: {result.path_display} "
                f"(Rev: {result.rev})"
            )
            
            return result.path_display
        
        except ApiError as e:
            self.logger.error(
                f"Dropbox API error uploading {file_path}: {e}",
                exc_info=True
            )
            return None
        
        except Exception as e:
            self.logger.error(
                f"Failed to upload {file_path} to Dropbox: {e}",
                exc_info=True
            )
            return None
    
    def verify_folder_access(self, folder_path: str) -> bool:
        """
        Verify that the specified folder exists and is accessible.
        
        Args:
            folder_path: Dropbox folder path
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            if not self.dbx:
                raise RuntimeError("Not authenticated with Dropbox")
            
            # Root folder always exists
            if folder_path == '/':
                return True
            
            # Try to get folder metadata
            metadata = self.dbx.files_get_metadata(folder_path)
            
            # Check if it's actually a folder
            if not isinstance(metadata, dropbox.files.FolderMetadata):
                self.logger.error(f"Path {folder_path} is not a folder")
                return False
            
            self.logger.info(f"Verified access to Dropbox folder: {metadata.path_display}")
            return True
        
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                self.logger.error(f"Dropbox folder not found: {folder_path}")
            else:
                self.logger.error(f"Cannot access Dropbox folder {folder_path}: {e}")
            return False
        
        except Exception as e:
            self.logger.error(f"Error verifying folder access: {e}", exc_info=True)
            return False
    
    def create_folder(self, folder_path: str) -> bool:
        """
        Create a folder in Dropbox.
        
        Args:
            folder_path: Path of folder to create
            
        Returns:
            True if created or already exists, False on error
        """
        try:
            if not self.dbx:
                raise RuntimeError("Not authenticated with Dropbox")
            
            # Root folder can't be created
            if folder_path == '/':
                return True
            
            self.dbx.files_create_folder_v2(folder_path)
            self.logger.info(f"Created Dropbox folder: {folder_path}")
            return True
        
        except ApiError as e:
            # Folder already exists is not an error
            if e.error.is_path() and e.error.get_path().is_conflict():
                self.logger.debug(f"Dropbox folder already exists: {folder_path}")
                return True
            else:
                self.logger.error(f"Failed to create Dropbox folder {folder_path}: {e}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error creating folder: {e}", exc_info=True)
            return False


class GPGFileHandler(FileSystemEventHandler):
    """Handler for file system events that encrypts and moves files."""
    
    def __init__(
        self, 
        config: Config, 
        gpg: gnupg.GPG, 
        logger: logging.Logger,
        gdrive_uploader: Optional[GoogleDriveUploader] = None,
        dropbox_uploader: Optional[DropboxUploader] = None
    ) -> None:
        """
        Initialize the file handler.
        
        Args:
            config: Configuration object
            gpg: GPG instance
            logger: Logger instance
            gdrive_uploader: Optional Google Drive uploader instance
            dropbox_uploader: Optional Dropbox uploader instance
        """
        super().__init__()
        self.config = config
        self.gpg = gpg
        self.logger = logger
        self.gdrive_uploader = gdrive_uploader
        self.dropbox_uploader = dropbox_uploader
        self.processing_files: set[Path] = set()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events.
        
        Args:
            event: File system event
        """
        # Ignore directories
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file extension matches filter (if configured)
        if self.config.file_extensions:
            if file_path.suffix.lower() not in self.config.file_extensions:
                self.logger.debug(f"Ignoring file with unmatched extension: {file_path}")
                return
        
        # Skip if already processing this file
        if file_path in self.processing_files:
            return
        
        self.logger.info(f"New file detected: {file_path}")
        self.process_file(file_path)
    
    def process_file(self, file_path: Path) -> None:
        """
        Encrypt and move a file.
        
        Args:
            file_path: Path to the file to process
        """
        try:
            self.processing_files.add(file_path)
            
            # Wait a moment to ensure file is fully written
            time.sleep(0.5)
            
            # Verify file still exists and is readable
            if not file_path.exists():
                self.logger.warning(f"File disappeared before processing: {file_path}")
                return
            
            # Encrypt the file
            encrypted_file_path = self.encrypt_file(file_path)
            
            if encrypted_file_path:
                # Determine workflow based on cloud configuration
                if self.config.google_drive_enabled and self.gdrive_uploader:
                    # Google Drive workflow: upload directly, skip local destination
                    self.upload_to_google_drive(encrypted_file_path, file_path.name)
                elif self.config.dropbox_enabled and self.dropbox_uploader:
                    # Dropbox workflow: upload directly, skip local destination
                    self.upload_to_dropbox(encrypted_file_path, file_path.name)
                else:
                    # Local workflow: move to destination directory
                    self.move_encrypted_file(encrypted_file_path, file_path.name)
                
                # Delete original file if configured
                if self.config.delete_original:
                    try:
                        file_path.unlink()
                        self.logger.info(f"Deleted original file: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete original file {file_path}: {e}")
                
                console.print(
                    Panel(
                        f"✓ Successfully encrypted: [green]{file_path.name}[/green]",
                        border_style="green"
                    )
                )
        
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
            console.print(
                Panel(
                    f"✗ Failed to process: [red]{file_path.name}[/red]\nError: {e}",
                    border_style="red"
                )
            )
        
        finally:
            self.processing_files.discard(file_path)
    
    def encrypt_file(self, file_path: Path) -> Optional[Path]:
        """
        Encrypt a file using GPG.
        
        Args:
            file_path: Path to the file to encrypt
            
        Returns:
            Path to encrypted file or None on failure
        """
        try:
            self.logger.info(f"Encrypting file: {file_path}")
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Encrypt the data
            encrypted_data = self.gpg.encrypt(
                file_data,
                self.config.gpg_key_id,
                always_trust=True
            )
            
            if not encrypted_data.ok:
                raise RuntimeError(f"GPG encryption failed: {encrypted_data.status}")
            
            # Write encrypted data to temporary file
            encrypted_file_path = file_path.with_suffix(file_path.suffix + '.gpg')
            with open(encrypted_file_path, 'wb') as f:
                f.write(encrypted_data.data)
            
            self.logger.info(f"File encrypted successfully: {encrypted_file_path}")
            return encrypted_file_path
        
        except Exception as e:
            self.logger.error(f"Failed to encrypt file {file_path}: {e}", exc_info=True)
            return None
    
    def move_encrypted_file(self, encrypted_file_path: Path, original_name: str) -> None:
        """
        Move encrypted file to destination directory (local workflow only).
        
        Args:
            encrypted_file_path: Path to encrypted file
            original_name: Original filename
        """
        try:
            destination_path = self.config.destination_directory / f"{original_name}.gpg"
            
            # Handle existing file at destination
            if destination_path.exists():
                counter = 1
                while destination_path.exists():
                    destination_path = self.config.destination_directory / f"{original_name}.{counter}.gpg"
                    counter += 1
                self.logger.warning(f"File exists at destination, using: {destination_path.name}")
            
            encrypted_file_path.rename(destination_path)
            self.logger.info(f"Moved encrypted file to: {destination_path}")
        
        except Exception as e:
            self.logger.error(
                f"Failed to move encrypted file {encrypted_file_path} to destination: {e}",
                exc_info=True
            )
            raise
    
    def upload_to_google_drive(self, encrypted_file_path: Path, original_name: str) -> None:
        """
        Upload encrypted file directly to Google Drive and clean up local file.
        
        Args:
            encrypted_file_path: Path to encrypted file
            original_name: Original filename
        """
        try:
            if not self.gdrive_uploader:
                raise RuntimeError("Google Drive uploader not initialized")
            
            self.logger.info(f"Uploading {original_name}.gpg directly to Google Drive...")
            file_id = self.gdrive_uploader.upload_file(encrypted_file_path)
            
            if file_id:
                console.print(
                    Panel(
                        f"✓ Uploaded to Google Drive: [cyan]{encrypted_file_path.name}[/cyan]\n"
                        f"File ID: [green]{file_id}[/green]",
                        border_style="cyan"
                    )
                )
                
                # Delete local encrypted file after successful upload
                try:
                    encrypted_file_path.unlink()
                    self.logger.info(
                        f"Deleted local encrypted file after upload: {encrypted_file_path}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Failed to delete local encrypted file {encrypted_file_path}: {e}"
                    )
            else:
                self.logger.error(f"Failed to upload {encrypted_file_path.name} to Google Drive")
                console.print(
                    Panel(
                        f"✗ Google Drive upload failed: [red]{encrypted_file_path.name}[/red]\n"
                        f"Local encrypted file kept at: {encrypted_file_path}",
                        border_style="red"
                    )
                )
        
        except Exception as e:
            self.logger.error(
                f"Failed to upload {encrypted_file_path} to Google Drive: {e}",
                exc_info=True
            )
            console.print(
                Panel(
                    f"✗ Google Drive upload failed: [red]{encrypted_file_path.name}[/red]\n"
                    f"Error: {e}\n"
                    f"Local encrypted file kept at: {encrypted_file_path}",
                    border_style="red"
                )
            )
            raise
    
    def upload_to_dropbox(self, encrypted_file_path: Path, original_name: str) -> None:
        """
        Upload encrypted file directly to Dropbox and clean up local file.
        
        Args:
            encrypted_file_path: Path to encrypted file
            original_name: Original filename
        """
        try:
            if not self.dropbox_uploader:
                raise RuntimeError("Dropbox uploader not initialized")
            
            self.logger.info(f"Uploading {original_name}.gpg directly to Dropbox...")
            dropbox_path = self.dropbox_uploader.upload_file(encrypted_file_path)
            
            if dropbox_path:
                console.print(
                    Panel(
                        f"✓ Uploaded to Dropbox: [cyan]{encrypted_file_path.name}[/cyan]\n"
                        f"Path: [green]{dropbox_path}[/green]",
                        border_style="cyan"
                    )
                )
                
                # Delete local encrypted file after successful upload
                try:
                    encrypted_file_path.unlink()
                    self.logger.info(
                        f"Deleted local encrypted file after upload: {encrypted_file_path}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Failed to delete local encrypted file {encrypted_file_path}: {e}"
                    )
            else:
                self.logger.error(f"Failed to upload {encrypted_file_path.name} to Dropbox")
                console.print(
                    Panel(
                        f"✗ Dropbox upload failed: [red]{encrypted_file_path.name}[/red]\n"
                        f"Local encrypted file kept at: {encrypted_file_path}",
                        border_style="red"
                    )
                )
        
        except Exception as e:
            self.logger.error(
                f"Failed to upload {encrypted_file_path} to Dropbox: {e}",
                exc_info=True
            )
            console.print(
                Panel(
                    f"✗ Dropbox upload failed: [red]{encrypted_file_path.name}[/red]\n"
                    f"Error: {e}\n"
                    f"Local encrypted file kept at: {encrypted_file_path}",
                    border_style="red"
                )
            )
            raise


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Optional path to config file. 
                     Defaults to ~/.config/gpg-file-watcher/config.yaml
    
    Returns:
        Config object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config is invalid
        yaml.YAMLError: If YAML parsing fails
    """
    if config_path is None:
        config_path = Path.home() / '.config' / 'gpg-file-watcher' / 'config.yaml'
    
    config_path = Path(config_path).expanduser().resolve()
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create a config file at this location."
        )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return Config(**config_data)


def setup_logging(config: Config) -> logging.Logger:
    """
    Set up structured logging.
    
    Args:
        config: Configuration object
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger('gpg_file_watcher')
    logger.setLevel(getattr(logging, config.log_level))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with rich formatting
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False
    )
    console_handler.setLevel(getattr(logging, config.log_level))
    logger.addHandler(console_handler)
    
    # File handler if configured
    if config.log_file:
        log_file_path = Path(config.log_file).expanduser().resolve()
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def verify_gpg_key(gpg: gnupg.GPG, key_id: str, logger: logging.Logger) -> bool:
    """
    Verify that GPG key exists.
    
    Args:
        gpg: GPG instance
        key_id: Key ID or email to verify
        logger: Logger instance
        
    Returns:
        True if key exists, False otherwise
    """
    try:
        keys = gpg.list_keys()
        for key in keys:
            if key_id in key['uids'][0] or key_id == key['keyid'] or key_id == key['fingerprint']:
                logger.info(f"Found GPG key: {key['uids'][0]}")
                return True
        
        logger.error(f"GPG key not found: {key_id}")
        logger.info("Available keys:")
        for key in keys:
            logger.info(f"  - {key['uids'][0]} (ID: {key['keyid']})")
        return False
    
    except Exception as e:
        logger.error(f"Error verifying GPG key: {e}", exc_info=True)
        return False


def main() -> int:
    """
    Main entry point for the GPG file watcher.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='GPG File Watcher - Encrypt files and optionally upload to Google Drive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  %(prog)s
  
  # Enable Google Drive upload
  %(prog)s --google-drive
  
  # Enable Dropbox upload
  %(prog)s --dropbox
  
  # Use custom config file
  %(prog)s --config ~/my-config.yaml --google-drive
  
  # Debug mode
  %(prog)s --debug
        """
    )
    parser.add_argument(
        '--google-drive',
        action='store_true',
        help='Enable Google Drive upload (requires configuration)'
    )
    parser.add_argument(
        '--dropbox',
        action='store_true',
        help='Enable Dropbox upload (requires configuration)'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=None,
        help='Path to configuration file (default: ~/.config/gpg-file-watcher/config.yaml)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        console.print(Panel("GPG File Watcher v2.0", style="bold blue"))
        console.print("Loading configuration...")
        config = load_config(args.config)
        
        # Override cloud service settings if specified via command line
        if args.google_drive:
            config.google_drive_enabled = True
            config.dropbox_enabled = False  # Disable Dropbox if Google Drive specified
        
        if args.dropbox:
            config.dropbox_enabled = True
            config.google_drive_enabled = False  # Disable Google Drive if Dropbox specified
        
        # Validate that only one cloud service is enabled
        if config.google_drive_enabled and config.dropbox_enabled:
            console.print(
                Panel(
                    "[red]Error: Cannot enable both Google Drive and Dropbox simultaneously[/red]\n"
                    "Please use only one of: --google-drive or --dropbox",
                    border_style="red",
                    title="Configuration Error"
                )
            )
            return 1
        
        # Setup logging
        logger = setup_logging(config)
        logger.info("GPG File Watcher v2.0 started")
        
        # Initialize GPG
        gpg_kwargs: Dict[str, Any] = {}
        if config.gpg_home:
            gpg_kwargs['gnupghome'] = str(config.gpg_home)
        gpg = gnupg.GPG(**gpg_kwargs)
        
        # Verify GPG key exists
        if not verify_gpg_key(gpg, config.gpg_key_id, logger):
            console.print(
                Panel(
                    f"[red]GPG key not found: {config.gpg_key_id}[/red]\n"
                    "Please ensure the key is imported and available.",
                    border_style="red",
                    title="Error"
                )
            )
            return 1
        
        # Initialize Google Drive uploader if enabled
        gdrive_uploader: Optional[GoogleDriveUploader] = None
        if config.google_drive_enabled:
            console.print("[cyan]Initializing Google Drive...[/cyan]")
            
            if not GOOGLE_DRIVE_AVAILABLE:
                console.print(
                    Panel(
                        "[red]Google Drive libraries not installed[/red]\n"
                        "Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib",
                        border_style="red",
                        title="Error"
                    )
                )
                return 1
            
            try:
                gdrive_uploader = GoogleDriveUploader(config, logger)
                gdrive_uploader.authenticate()
                
                # Verify folder access if specified
                if config.google_drive_folder_id:
                    if not gdrive_uploader.verify_folder_access(config.google_drive_folder_id):
                        console.print(
                            Panel(
                                f"[red]Cannot access Google Drive folder: {config.google_drive_folder_id}[/red]",
                                border_style="red",
                                title="Error"
                            )
                        )
                        return 1
                
                console.print(
                    Panel(
                        "[green]✓ Google Drive connected successfully[/green]",
                        border_style="green"
                    )
                )
            
            except Exception as e:
                console.print(
                    Panel(
                        f"[red]Failed to initialize Google Drive:[/red]\n{e}",
                        border_style="red",
                        title="Error"
                    )
                )
                if args.debug:
                    raise
                return 1
        
        # Initialize Dropbox uploader if enabled
        dropbox_uploader: Optional[DropboxUploader] = None
        if config.dropbox_enabled:
            console.print("[cyan]Initializing Dropbox...[/cyan]")
            
            if not DROPBOX_AVAILABLE:
                console.print(
                    Panel(
                        "[red]Dropbox library not installed[/red]\n"
                        "Install with: pip install dropbox",
                        border_style="red",
                        title="Error"
                    )
                )
                return 1
            
            try:
                dropbox_uploader = DropboxUploader(config, logger)
                dropbox_uploader.authenticate()
                
                # Verify folder access if specified
                if config.dropbox_folder_path and config.dropbox_folder_path != '/':
                    if not dropbox_uploader.verify_folder_access(config.dropbox_folder_path):
                        console.print(
                            Panel(
                                f"[red]Cannot access Dropbox folder: {config.dropbox_folder_path}[/red]",
                                border_style="red",
                                title="Error"
                            )
                        )
                        return 1
                
                console.print(
                    Panel(
                        "[green]✓ Dropbox connected successfully[/green]",
                        border_style="green"
                    )
                )
            
            except Exception as e:
                console.print(
                    Panel(
                        f"[red]Failed to initialize Dropbox:[/red]\n{e}",
                        border_style="red",
                        title="Error"
                    )
                )
                if args.debug:
                    raise
                return 1
        
        # Display configuration
        config_display = (
            f"[cyan]Watch Directory:[/cyan] {config.watch_directory}\n"
            f"[cyan]GPG Key:[/cyan] {config.gpg_key_id}\n"
            f"[cyan]Log Level:[/cyan] {config.log_level}\n"
            f"[cyan]Delete Original:[/cyan] {config.delete_original}"
        )
        
        if config.google_drive_enabled:
            config_display += (
                f"\n[cyan]Destination:[/cyan] [yellow]Google Drive (direct upload)[/yellow]\n"
                f"[cyan]GDrive Folder:[/cyan] {config.google_drive_folder_id or 'Root'}"
            )
        elif config.dropbox_enabled:
            config_display += (
                f"\n[cyan]Destination:[/cyan] [yellow]Dropbox (direct upload)[/yellow]\n"
                f"[cyan]Dropbox Path:[/cyan] {config.dropbox_folder_path}"
            )
        else:
            config_display += (
                f"\n[cyan]Destination Directory:[/cyan] {config.destination_directory}\n"
                f"[cyan]Cloud Storage:[/cyan] [yellow]Disabled[/yellow]"
            )
        
        console.print(Panel(
            config_display,
            title="Configuration",
            border_style="cyan"
        ))
        
        # Set up file system observer
        event_handler = GPGFileHandler(config, gpg, logger, gdrive_uploader, dropbox_uploader)
        observer = Observer()
        observer.schedule(
            event_handler, 
            str(config.watch_directory), 
            recursive=False
        )
        
        # Start watching
        observer.start()
        logger.info(f"Watching directory: {config.watch_directory}")
        
        watch_message = "[green]Watching for new files...[/green]\nPress Ctrl+C to stop"
        if config.google_drive_enabled:
            watch_message = (
                "[green]Watching for new files...[/green]\n"
                "[cyan]Files will be encrypted and uploaded directly to Google Drive[/cyan]\n"
                "[yellow]Note: Files will NOT be saved to local destination directory[/yellow]\n"
                "Press Ctrl+C to stop"
            )
        elif config.dropbox_enabled:
            watch_message = (
                "[green]Watching for new files...[/green]\n"
                "[cyan]Files will be encrypted and uploaded directly to Dropbox[/cyan]\n"
                "[yellow]Note: Files will NOT be saved to local destination directory[/yellow]\n"
                "Press Ctrl+C to stop"
            )
        
        console.print(Panel(watch_message, border_style="green"))
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping watcher...[/yellow]")
            observer.stop()
        
        observer.join()
        logger.info("GPG File Watcher stopped")
        console.print(Panel("[blue]GPG File Watcher stopped[/blue]", border_style="blue"))
        
        return 0
    
    except ValidationError as e:
        console.print(
            Panel(
                f"[red]Configuration validation error:[/red]\n{e}",
                border_style="red",
                title="Error"
            )
        )
        return 1
    
    except FileNotFoundError as e:
        console.print(
            Panel(
                f"[red]{e}[/red]",
                border_style="red",
                title="Error"
            )
        )
        return 1
    
    except Exception as e:
        console.print(
            Panel(
                f"[red]Unexpected error:[/red]\n{e}",
                border_style="red",
                title="Error"
            )
        )
        if args.debug:
            raise
        return 1


if __name__ == '__main__':
    sys.exit(main())
