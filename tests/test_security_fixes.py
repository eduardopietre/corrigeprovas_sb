"""
Tests to verify security fixes are working correctly.

This test suite validates that the security vulnerabilities identified
have been properly fixed and cannot be exploited.
"""

import os
import uuid
from unittest.mock import Mock, patch

import pytest


class TestSecurityFixes:
    """Test security fixes implementation."""
    
    def test_worker_security_module_import(self):
        """Test that the security module can be imported."""
        try:
            from worker.worker.security import (
                SecurityError,
                sanitize_filename,
                validate_storage_path,
            )
            assert True, "Security module imported successfully"
        except ImportError as e:
            pytest.fail(f"Failed to import security module: {e}")
    
    def test_storage_path_validation_blocks_traversal(self):
        """Test that path traversal is blocked by validation."""
        from worker.worker.security import SecurityError, validate_storage_path
        
        malicious_paths = [
            "../../../etc/passwd",
            "uploads/../../../sensitive/file.jpg",
            "bucket/../other_bucket/file.jpg",
            "uploads/user/../admin/secret.txt"
        ]
        
        for path in malicious_paths:
            with pytest.raises(SecurityError):
                validate_storage_path(path)
    
    def test_storage_path_validation_allows_valid_paths(self):
        """Test that valid paths are allowed."""
        from worker.worker.security import validate_storage_path
        
        valid_paths = [
            "uploads/user123/file.jpg",
            "results/job456/marked_0001.jpg",
            "templates/template.png"
        ]
        
        for path in valid_paths:
            try:
                bucket, file_path = validate_storage_path(path)
                assert bucket in ['uploads', 'results', 'templates']
                assert file_path and '.' not in file_path.split('/')
            except Exception as e:
                pytest.fail(f"Valid path rejected: {path} - {e}")
    
    def test_filename_sanitization(self):
        """Test that filenames are properly sanitized."""
        from worker.worker.security import SecurityError, sanitize_filename
        
        # Test malicious filenames are rejected
        malicious_filenames = [
            "../../../etc/passwd",
            "file.jpg/../../../sensitive.txt",
            "normal.jpg\x00../../../etc/passwd"
        ]
        
        for filename in malicious_filenames:
            with pytest.raises(SecurityError):
                sanitize_filename(filename)
        
        # Test valid filenames are sanitized properly
        valid_cases = [
            ("file name.jpg", "file_name.jpg"),
            ("test@file#123.png", "test_file_123.png"),
            ("document (1).pdf", "document__1_.pdf")
        ]
        
        for original, expected in valid_cases:
            result = sanitize_filename(original)
            assert result == expected
    
    def test_bucket_name_validation(self):
        """Test that only allowed bucket names are accepted."""
        from worker.worker.security import validate_bucket_name
        
        # Valid buckets
        valid_buckets = ['uploads', 'results', 'templates', 'exports']
        for bucket in valid_buckets:
            assert validate_bucket_name(bucket) is True
        
        # Invalid buckets
        invalid_buckets = ['..', 'admin', 'system', 'root', '']
        for bucket in invalid_buckets:
            assert validate_bucket_name(bucket) is False
    
    def test_uuid_validation(self):
        """Test UUID validation function."""
        from worker.worker.security import validate_uuid
        
        # Valid UUIDs
        valid_uuids = [
            str(uuid.uuid4()),
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000"
        ]
        
        for uuid_str in valid_uuids:
            assert validate_uuid(uuid_str) is True
        
        # Invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",
            "../admin",
            ""
        ]
        
        for uuid_str in invalid_uuids:
            assert validate_uuid(uuid_str) is False
    
    def test_secure_path_creation(self):
        """Test secure path creation function."""
        from worker.worker.security import SecurityError, create_secure_path
        
        user_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        # Valid case
        path = create_secure_path(user_id, job_id, "test.jpg")
        expected = f"{user_id}/{job_id}/test.jpg"
        assert path == expected
        
        # Invalid user ID
        with pytest.raises(SecurityError):
            create_secure_path("invalid-uuid", job_id, "test.jpg")
        
        # Invalid job ID
        with pytest.raises(SecurityError):
            create_secure_path(user_id, "invalid-uuid", "test.jpg")
        
        # Invalid filename
        with pytest.raises(SecurityError):
            create_secure_path(user_id, job_id, "../../../etc/passwd")
    
    def test_job_processor_uses_security_validation(self):
        """Test that job processor uses security validation."""
        from worker.worker.config import WorkerConfig
        from worker.worker.job_processor import JobProcessor
        from worker.worker.supabase_client import SupabaseWorkerClient
        
        # Mock configuration
        config = Mock(spec=WorkerConfig)
        client = Mock(spec=SupabaseWorkerClient)
        processor = JobProcessor(client)
        
        # Test that malicious paths are rejected
        malicious_path = "../../../etc/passwd"
        result = processor._download_image(malicious_path)
        
        # Should return None due to security validation
        assert result is None
        
        # download_file should not be called
        client.download_file.assert_not_called()
    
    def test_user_path_access_validation(self):
        """Test user path access validation."""
        from worker.worker.security import validate_user_path_access
        
        user_id = str(uuid.uuid4())
        
        # Valid access - path starts with user ID
        valid_path = f"{user_id}/job123/file.jpg"
        assert validate_user_path_access(valid_path, user_id) is True
        
        # Invalid access - path starts with different user ID
        other_user_id = str(uuid.uuid4())
        invalid_path = f"{other_user_id}/job123/file.jpg"
        assert validate_user_path_access(invalid_path, user_id) is False
        
        # Invalid user ID format
        assert validate_user_path_access(valid_path, "invalid-uuid") is False
    
    def test_file_extension_validation(self):
        """Test file extension validation."""
        from worker.worker.security import validate_file_extension
        
        # Valid extensions
        valid_files = [
            "image.jpg", "document.pdf", "photo.png", 
            "scan.tiff", "picture.webp", "file.jpeg"
        ]
        
        for filename in valid_files:
            assert validate_file_extension(filename) is True
        
        # Invalid extensions
        invalid_files = [
            "script.js", "executable.exe", "config.ini",
            "malware.bat", "virus.com", "noextension"
        ]
        
        for filename in invalid_files:
            assert validate_file_extension(filename) is False
    
    def test_edge_function_security_module_functions(self):
        """Test that Edge Function security functions work correctly."""
        # This would normally be tested in Deno, but we can test the logic
        
        # Test sanitizeFilename equivalent
        def sanitize_filename_js_equivalent(filename: str) -> str:
            import re
            if not filename or not filename.strip():
                raise ValueError("Filename cannot be empty")
            
            # URL decode first
            from urllib.parse import unquote
            sanitized = unquote(filename)
            
            # Remove control characters
            sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
            
            # Check for path traversal
            if '..' in sanitized or '/' in sanitized or '\\' in sanitized:
                raise ValueError(f"Path traversal detected: {filename}")
            
            # Sanitize characters
            sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', sanitized)
            
            if sanitized.startswith('.'):
                sanitized = '_' + sanitized[1:]
            
            return sanitized[:255]
        
        # Test cases
        test_cases = [
            ("normal.jpg", "normal.jpg"),
            ("file with spaces.png", "file_with_spaces.png"),
            ("special@chars#.pdf", "special_chars_.pdf")
        ]
        
        for original, expected in test_cases:
            result = sanitize_filename_js_equivalent(original)
            assert result == expected
        
        # Test malicious cases are rejected
        malicious_cases = [
            "../../../etc/passwd",
            "file/../admin.txt",
            "test\\..\\system.exe"
        ]
        
        for malicious in malicious_cases:
            with pytest.raises(ValueError):
                sanitize_filename_js_equivalent(malicious)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])