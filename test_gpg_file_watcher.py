#!/usr/bin/env python3

"""
Test suite for GPG File Watcher

@author: bva (scourgethetracker/bt7474)
@version: 1.0.0
@date: 2025-10-28
@python-version: 3.12+
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import yaml
from pydantic import ValidationError

# Import from main module
import sys
sys.path.insert(0, str(Path(__file__).parent))

from gpg_file_watcher import (
    Config,
    GPGFileHandler,
    load_config,
    setup_logging,
    verify_gpg_key
)


@pytest.fixture
def temp_directories():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as watch_dir, \
         tempfile.TemporaryDirectory() as dest_dir:
        yield Path(watch_dir), Path(dest_dir)


@pytest.fixture
def sample_config_data(temp_directories):
    """Create sample configuration data."""
    watch_dir, dest_dir = temp_directories
    return {
        'gpg_key_id': 'test@example.com',
        'watch_directory': str(watch_dir),
        'destination_directory': str(dest_dir),
        'log_level': 'INFO',
        'delete_original': True
    }


@pytest.fixture
def config_file(sample_config_data):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_config_data, f)
        config_path = Path(f.name)
    
    yield config_path
    
    # Cleanup
    config_path.unlink(missing_ok=True)


class TestConfig:
    """Test configuration validation."""
    
    def test_valid_config(self, sample_config_data):
        """Test creating a valid configuration."""
        config = Config(**sample_config_data)
        assert config.gpg_key_id == 'test@example.com'
        assert config.log_level == 'INFO'
        assert config.delete_original is True
    
    def test_invalid_directory(self, sample_config_data):
        """Test validation fails for non-existent directory."""
        sample_config_data['watch_directory'] = '/nonexistent/directory'
        with pytest.raises(ValidationError) as exc_info:
            Config(**sample_config_data)
        assert 'does not exist' in str(exc_info.value)
    
    def test_invalid_log_level(self, sample_config_data):
        """Test validation fails for invalid log level."""
        sample_config_data['log_level'] = 'INVALID'
        with pytest.raises(ValidationError) as exc_info:
            Config(**sample_config_data)
        assert 'Invalid log level' in str(exc_info.value)
    
    def test_optional_fields(self, sample_config_data):
        """Test optional configuration fields."""
        config = Config(**sample_config_data)
        assert config.log_file is None
        assert config.file_extensions is None
        assert config.gpg_home is None
    
    def test_file_extensions_filter(self, sample_config_data):
        """Test file extension filter configuration."""
        sample_config_data['file_extensions'] = ['.txt', '.pdf']
        config = Config(**sample_config_data)
        assert '.txt' in config.file_extensions
        assert '.pdf' in config.file_extensions


class TestLoadConfig:
    """Test configuration loading."""
    
    def test_load_config_success(self, config_file):
        """Test successfully loading config from file."""
        config = load_config(config_file)
        assert isinstance(config, Config)
        assert config.gpg_key_id == 'test@example.com'
    
    def test_load_config_missing_file(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(Path('/nonexistent/config.yaml'))
        assert 'not found' in str(exc_info.value)
    
    def test_load_config_invalid_yaml(self):
        """Test error when YAML is malformed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            invalid_config = Path(f.name)
        
        try:
            with pytest.raises(yaml.YAMLError):
                load_config(invalid_config)
        finally:
            invalid_config.unlink()


class TestGPGFileHandler:
    """Test file handling and encryption."""
    
    @pytest.fixture
    def mock_gpg(self):
        """Create a mock GPG object."""
        gpg = Mock()
        encrypted_result = Mock()
        encrypted_result.ok = True
        encrypted_result.data = b'encrypted_data'
        encrypted_result.status = 'encryption ok'
        gpg.encrypt.return_value = encrypted_result
        return gpg
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()
    
    @pytest.fixture
    def handler(self, sample_config_data, mock_gpg, mock_logger):
        """Create a GPGFileHandler instance."""
        config = Config(**sample_config_data)
        return GPGFileHandler(config, mock_gpg, mock_logger)
    
    def test_on_created_ignores_directories(self, handler):
        """Test that directory events are ignored."""
        event = Mock()
        event.is_directory = True
        event.src_path = '/some/directory'
        
        handler.on_created(event)
        handler.logger.info.assert_not_called()
    
    def test_on_created_filters_extensions(self, sample_config_data, mock_gpg, mock_logger):
        """Test file extension filtering."""
        sample_config_data['file_extensions'] = ['.txt']
        config = Config(**sample_config_data)
        handler = GPGFileHandler(config, mock_gpg, mock_logger)
        
        # Create a test file with wrong extension
        watch_dir = Path(sample_config_data['watch_directory'])
        test_file = watch_dir / 'test.pdf'
        test_file.touch()
        
        event = Mock()
        event.is_directory = False
        event.src_path = str(test_file)
        
        handler.on_created(event)
        mock_logger.debug.assert_called()
        
        # Clean up
        test_file.unlink()
    
    def test_encrypt_file_success(self, handler, temp_directories):
        """Test successful file encryption."""
        watch_dir, _ = temp_directories
        test_file = watch_dir / 'test.txt'
        test_file.write_text('test content')
        
        encrypted_path = handler.encrypt_file(test_file)
        
        assert encrypted_path is not None
        assert encrypted_path.exists()
        assert encrypted_path.suffix == '.gpg'
        handler.gpg.encrypt.assert_called_once()
        
        # Clean up
        if encrypted_path.exists():
            encrypted_path.unlink()
    
    def test_encrypt_file_gpg_failure(self, handler, temp_directories, mock_logger):
        """Test handling of GPG encryption failure."""
        watch_dir, _ = temp_directories
        test_file = watch_dir / 'test.txt'
        test_file.write_text('test content')
        
        # Make GPG encryption fail
        handler.gpg.encrypt.return_value.ok = False
        handler.gpg.encrypt.return_value.status = 'encryption failed'
        
        encrypted_path = handler.encrypt_file(test_file)
        
        assert encrypted_path is None
        handler.logger.error.assert_called()
    
    def test_move_encrypted_file_success(self, handler, temp_directories):
        """Test successfully moving encrypted file."""
        watch_dir, dest_dir = temp_directories
        encrypted_file = watch_dir / 'test.txt.gpg'
        encrypted_file.write_bytes(b'encrypted content')
        
        handler.move_encrypted_file(encrypted_file, 'test.txt')
        
        expected_dest = dest_dir / 'test.txt.gpg'
        assert expected_dest.exists()
        assert not encrypted_file.exists()
    
    def test_move_encrypted_file_conflict(self, handler, temp_directories):
        """Test handling of filename conflicts."""
        watch_dir, dest_dir = temp_directories
        
        # Create existing file at destination
        existing_file = dest_dir / 'test.txt.gpg'
        existing_file.write_bytes(b'existing content')
        
        # Create new encrypted file
        encrypted_file = watch_dir / 'test.txt.gpg'
        encrypted_file.write_bytes(b'new encrypted content')
        
        handler.move_encrypted_file(encrypted_file, 'test.txt')
        
        # Should create file with counter
        expected_dest = dest_dir / 'test.txt.1.gpg'
        assert expected_dest.exists()
        assert existing_file.exists()  # Original should remain
        handler.logger.warning.assert_called()


class TestSetupLogging:
    """Test logging setup."""
    
    def test_setup_logging_console_only(self, sample_config_data):
        """Test logging setup with console handler only."""
        config = Config(**sample_config_data)
        logger = setup_logging(config)
        
        assert logger.name == 'gpg_file_watcher'
        assert logger.level == 20  # INFO level
        assert len(logger.handlers) >= 1
    
    def test_setup_logging_with_file(self, sample_config_data):
        """Test logging setup with file handler."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as log_file:
            log_path = Path(log_file.name)
        
        try:
            sample_config_data['log_file'] = str(log_path)
            config = Config(**sample_config_data)
            logger = setup_logging(config)
            
            assert len(logger.handlers) >= 2
            logger.info("Test message")
            
            # Verify log file was created and written to
            assert log_path.exists()
            content = log_path.read_text()
            assert 'Test message' in content
        
        finally:
            log_path.unlink(missing_ok=True)


class TestVerifyGPGKey:
    """Test GPG key verification."""
    
    def test_verify_key_exists(self):
        """Test verification when key exists."""
        mock_gpg = Mock()
        mock_gpg.list_keys.return_value = [
            {
                'keyid': 'ABC123',
                'fingerprint': 'ABCD1234',
                'uids': ['Test User <test@example.com>']
            }
        ]
        mock_logger = Mock()
        
        result = verify_gpg_key(mock_gpg, 'test@example.com', mock_logger)
        assert result is True
    
    def test_verify_key_not_found(self):
        """Test verification when key doesn't exist."""
        mock_gpg = Mock()
        mock_gpg.list_keys.return_value = [
            {
                'keyid': 'ABC123',
                'fingerprint': 'ABCD1234',
                'uids': ['Other User <other@example.com>']
            }
        ]
        mock_logger = Mock()
        
        result = verify_gpg_key(mock_gpg, 'test@example.com', mock_logger)
        assert result is False
        mock_logger.error.assert_called()
    
    def test_verify_key_by_keyid(self):
        """Test verification using key ID."""
        mock_gpg = Mock()
        mock_gpg.list_keys.return_value = [
            {
                'keyid': 'ABC123',
                'fingerprint': 'ABCD1234',
                'uids': ['Test User <test@example.com>']
            }
        ]
        mock_logger = Mock()
        
        result = verify_gpg_key(mock_gpg, 'ABC123', mock_logger)
        assert result is True


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.slow
    def test_full_encryption_workflow(self, temp_directories, sample_config_data):
        """Test complete file encryption workflow."""
        watch_dir, dest_dir = temp_directories
        
        # Create config
        config = Config(**sample_config_data)
        
        # Create mock GPG
        mock_gpg = Mock()
        encrypted_result = Mock()
        encrypted_result.ok = True
        encrypted_result.data = b'encrypted_test_content'
        encrypted_result.status = 'encryption ok'
        mock_gpg.encrypt.return_value = encrypted_result
        
        # Create handler
        mock_logger = Mock()
        handler = GPGFileHandler(config, mock_gpg, mock_logger)
        
        # Create test file
        test_file = watch_dir / 'integration_test.txt'
        test_file.write_text('This is a test file for integration testing.')
        
        # Process the file
        handler.process_file(test_file)
        
        # Verify encrypted file exists in destination
        expected_encrypted = dest_dir / 'integration_test.txt.gpg'
        assert expected_encrypted.exists()
        
        # Verify original deleted (if configured)
        if config.delete_original:
            assert not test_file.exists()
        
        # Verify GPG was called
        mock_gpg.encrypt.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=gpg_file_watcher', '--cov-report=term-missing'])
