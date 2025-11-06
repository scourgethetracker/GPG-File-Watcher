#!/usr/bin/env bash

# GPG File Watcher - Setup Script for macOS
#
# Features:
# * Checks system requirements
# * Installs Python dependencies
# * Creates necessary directories
# * Sets up configuration file
# * Provides setup verification
#
# @author: bva (scourgethetracker/bt7474)
# @version: 1.0.0
# @date: 2025-10-28

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONFIG_DIR="${HOME}/.config/gpg-file-watcher"
CONFIG_FILE="${CONFIG_DIR}/config.yaml"
LOG_DIR="${HOME}/.local/share/gpg-file-watcher"
DEFAULT_WATCH_DIR="${HOME}/Documents/to_encrypt"
DEFAULT_DEST_DIR="${HOME}/Documents/encrypted"

# Helper functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  GPG File Watcher - Setup${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_requirement() {
    local cmd=$1
    local name=$2
    local install_hint=$3
    
    if command -v "${cmd}" &> /dev/null; then
        print_success "${name} is installed"
        return 0
    else
        print_error "${name} is not installed"
        if [ -n "${install_hint}" ]; then
            print_info "Install with: ${install_hint}"
        fi
        return 1
    fi
}

check_python_version() {
    if command -v python3 &> /dev/null; then
        local version=$(python3 --version | awk '{print $2}')
        local major=$(echo "${version}" | cut -d. -f1)
        local minor=$(echo "${version}" | cut -d. -f2)
        
        if [ "${major}" -ge 3 ] && [ "${minor}" -ge 12 ]; then
            print_success "Python ${version} meets requirements (3.12+)"
            return 0
        else
            print_error "Python ${version} is too old (need 3.12+)"
            print_info "Install newer Python with: brew install python@3.12"
            return 1
        fi
    else
        print_error "Python 3 is not installed"
        print_info "Install with: brew install python@3.12"
        return 1
    fi
}

# Main setup
main() {
    print_header
    
    echo "Step 1: Checking system requirements..."
    echo ""
    
    local all_requirements_met=true
    
    # Check Python
    if ! check_python_version; then
        all_requirements_met=false
    fi
    
    # Check GPG
    if ! check_requirement "gpg" "GnuPG" "brew install gnupg"; then
        all_requirements_met=false
    fi
    
    # Check pip
    if ! check_requirement "pip3" "pip3" ""; then
        all_requirements_met=false
    fi
    
    echo ""
    
    if [ "${all_requirements_met}" = false ]; then
        print_error "Some requirements are missing. Please install them and run this script again."
        exit 1
    fi
    
    echo "Step 2: Checking GPG keys..."
    echo ""
    
    local gpg_keys=$(gpg --list-keys 2>/dev/null | grep -c "^pub" || echo "0")
    if [ "${gpg_keys}" -eq 0 ]; then
        print_warning "No GPG keys found"
        print_info "Generate a key with: gpg --full-generate-key"
        echo ""
        read -p "Do you want to generate a GPG key now? (y/N): " -n 1 -r
        echo ""
        if [[ ${REPLY} =~ ^[Yy]$ ]]; then
            gpg --full-generate-key
        else
            print_error "GPG key is required. Setup cannot continue."
            exit 1
        fi
    else
        print_success "Found ${gpg_keys} GPG key(s)"
        echo ""
        print_info "Available keys:"
        gpg --list-keys | grep -E "^(pub|uid)" | sed 's/^/  /'
    fi
    
    echo ""
    echo "Step 3: Installing Python dependencies..."
    echo ""
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt --quiet
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    echo ""
    echo "Step 4: Creating directories..."
    echo ""
    
    # Create config directory
    mkdir -p "${CONFIG_DIR}"
    print_success "Created config directory: ${CONFIG_DIR}"
    
    # Create log directory
    mkdir -p "${LOG_DIR}"
    print_success "Created log directory: ${LOG_DIR}"
    
    # Ask user for watch and destination directories
    echo ""
    read -p "Enter watch directory path [${DEFAULT_WATCH_DIR}]: " watch_dir
    watch_dir=${watch_dir:-${DEFAULT_WATCH_DIR}}
    watch_dir="${watch_dir/#\~/${HOME}}"  # Expand tilde
    mkdir -p "${watch_dir}"
    print_success "Created watch directory: ${watch_dir}"
    
    read -p "Enter destination directory path [${DEFAULT_DEST_DIR}]: " dest_dir
    dest_dir=${dest_dir:-${DEFAULT_DEST_DIR}}
    dest_dir="${dest_dir/#\~/${HOME}}"  # Expand tilde
    mkdir -p "${dest_dir}"
    print_success "Created destination directory: ${dest_dir}"
    
    echo ""
    echo "Step 5: Configuring GPG File Watcher..."
    echo ""
    
    # Get GPG key from user
    echo "Available GPG keys:"
    gpg --list-keys --keyid-format=long | grep -E "^(pub|uid)" | sed 's/^/  /'
    echo ""
    read -p "Enter your GPG key ID or email: " gpg_key
    
    if [ -z "${gpg_key}" ]; then
        print_error "GPG key is required"
        exit 1
    fi
    
    # Create configuration file
    cat > "${CONFIG_FILE}" << EOF
# GPG File Watcher Configuration
# Generated on $(date '+%Y-%m-%d %H:%M:%S')

# GPG key ID, fingerprint, or email address to use for encryption
gpg_key_id: "${gpg_key}"

# Directory to watch for new files
watch_directory: "${watch_dir}"

# Directory where encrypted files will be moved
destination_directory: "${dest_dir}"

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level: "INFO"

# Path to log file
log_file: "${LOG_DIR}/watcher.log"

# Optional: Filter by file extensions (null = watch all files)
# Example: [".txt", ".pdf", ".docx", ".jpg"]
file_extensions: null

# Whether to delete original file after successful encryption
delete_original: true
EOF
    
    print_success "Created configuration file: ${CONFIG_FILE}"
    
    echo ""
    echo "Step 7: Google Drive Setup (Optional)..."
    echo ""
    
    read -p "Do you want to enable Google Drive upload? (y/N): " -n 1 -r
    echo ""
    
    if [[ ${REPLY} =~ ^[Yy]$ ]]; then
        print_info "To enable Google Drive, you need:"
        echo "  1. Google Cloud Platform project"
        echo "  2. Google Drive API enabled"
        echo "  3. OAuth 2.0 credentials JSON file"
        echo ""
        print_info "See GOOGLE_DRIVE_SETUP.md for detailed instructions"
        echo ""
        
        read -p "Do you have the credentials file ready? (y/N): " -n 1 -r
        echo ""
        
        if [[ ${REPLY} =~ ^[Yy]$ ]]; then
            read -p "Enter path to Google Drive credentials JSON: " creds_path
            creds_path="${creds_path/#\~/${HOME}}"
            
            if [ -f "${creds_path}" ]; then
                cp "${creds_path}" "${CONFIG_DIR}/gdrive_credentials.json"
                chmod 600 "${CONFIG_DIR}/gdrive_credentials.json"
                print_success "Copied credentials to: ${CONFIG_DIR}/gdrive_credentials.json"
                
                # Update config to enable Google Drive
                cat >> "${CONFIG_FILE}" << EOF

# Google Drive configuration (enabled)
google_drive_enabled: true
google_drive_credentials_file: "${CONFIG_DIR}/gdrive_credentials.json"
google_drive_token_file: "${CONFIG_DIR}/gdrive_token.json"
google_drive_folder_id: null
EOF
                print_success "Enabled Google Drive in configuration"
                print_info "Run with --google-drive flag to upload directly to cloud"
                print_info "Note: Files will NOT be saved locally when using --google-drive"
            else
                print_error "Credentials file not found: ${creds_path}"
                print_info "You can set up Google Drive later by editing ${CONFIG_FILE}"
            fi
        else
            print_info "Follow GOOGLE_DRIVE_SETUP.md to get credentials"
            print_info "Then edit ${CONFIG_FILE} to enable Google Drive"
        fi
    else
        print_info "Google Drive disabled. You can enable it later in ${CONFIG_FILE}"
    fi
    
    echo ""
    echo "Step 8: Verifying setup..."
    echo ""
    
    # Test configuration
    if python3 -c "
import yaml
from pathlib import Path
try:
    with open('${CONFIG_FILE}', 'r') as f:
        config = yaml.safe_load(f)
    print('Configuration is valid')
except Exception as e:
    print(f'Configuration error: {e}')
    exit(1)
" 2>&1; then
        print_success "Configuration file is valid"
    else
        print_error "Configuration file has errors"
        exit 1
    fi
    
    echo ""
    print_header
    print_success "Setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Review configuration: nano ${CONFIG_FILE}"
    echo "  2. Run the watcher: python3 gpg_file_watcher.py"
    if grep -q "google_drive_enabled: true" "${CONFIG_FILE}" 2>/dev/null; then
        echo "  3. Run with Google Drive: python3 gpg_file_watcher.py --google-drive"
        echo "  4. Test by copying a file to: ${watch_dir}"
    else
        echo "  3. Test by copying a file to: ${watch_dir}"
        echo "  4. To enable Google Drive later, see GOOGLE_DRIVE_SETUP.md"
    fi
    echo ""
    print_info "To run as a service, see the README.md for launchd instructions"
    echo ""
}

# Run main function
main "$@"
