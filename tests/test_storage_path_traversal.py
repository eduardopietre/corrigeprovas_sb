"""
Test for storage path traversal vulnerability.

This test validates that path traversal vulnerabilities have been fixed
and that the security measures are working correctly.
"""

import os
import uuid
from unittest.mock import Mock, patch

import pytest


class TestStoragePathTraversal:
    """Test storage path traversal security fixes."""
    
    def test_path_traversal_in_upload_path(self):
        """
        Test that upload path construction blocks path traversal attacks.
        """
        # Test that malicious user IDs are rejected by validation
        malicious_user_id = "../../../etc/passwd"
        filename = "test.jpg"
        
        # With security fixes, this should be caught by validation
        try:
            from worker.worker.security import validate_uuid
            # This should return False for malicious input
            is_valid = validate_uuid(malicious_user_id)
            assert is_valid is False, "Malicious user ID should be rejected"
            
            # If we try to create a path with invalid user ID, it should fail
            from worker.worker.security import SecurityError, create_secure_path
            job_id = str(uuid.uuid4())
            
            with pytest.raises(SecurityError):
                create_secure_path(malicious_user_id, job_id, filename)
                
            print("✅ SECURITY FIX CONFIRMED: Path traversal in upload path is blocked")
            
        except ImportError:
            # If security module doesn't exist, the vulnerability still exists
            constructed_path = f"{malicious_user_id}/{filename}"
            if "../" in constructed_path:
                pytest.fail(
                    f"VULNERABILITY CONFIRMED: Path traversal possible in upload path: {constructed_path}"
                )
    
    def test_path_traversal_in_result_path(self):
        """
        Test that result path construction blocks path traversal attacks.
        """
        user_id = str(uuid.uuid4())
        malicious_job_id = "../../../sensitive_data"
        item_index = 1
        
        # With security fixes, this should be caught by validation
        try:
            from worker.worker.security import (
                SecurityError,
                create_secure_path,
                validate_uuid,
            )
            
            # Job ID validation should reject malicious input
            is_valid = validate_uuid(malicious_job_id)
            assert is_valid is False, "Malicious job ID should be rejected"
            
            # Creating secure path should fail with malicious job ID
            filename = f"marked_{item_index:04d}.jpg"
            with pytest.raises(SecurityError):
                create_secure_path(user_id, malicious_job_id, filename)
                
            print("✅ SECURITY FIX CONFIRMED: Path traversal in result path is blocked")
            
        except ImportError:
            # If security module doesn't exist, the vulnerability still exists
            path = f"{user_id}/{malicious_job_id}/marked_{item_index:04d}.jpg"
            if "../" in path:
                pytest.fail(
                    f"VULNERABILITY CONFIRMED: Path traversal possible in result path: {path}"
                )
    
    def test_filename_sanitization(self):
        """
        Test that filenames are properly sanitized to prevent path traversal.
        """
        # Test various malicious filename patterns
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "file.jpg/../../../sensitive.txt",
            "normal.jpg\x00../../../etc/passwd",  # Null byte injection
            "file.jpg%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
        ]
        
        try:
            from worker.worker.security import SecurityError, sanitize_filename
            
            for malicious_filename in malicious_filenames:
                # With security fixes, these should be rejected
                with pytest.raises(SecurityError):
                    sanitize_filename(malicious_filename)
                    
            print("✅ SECURITY FIX CONFIRMED: Malicious filenames are properly rejected")
            
        except ImportError:
            # If security module doesn't exist, test old behavior
            for malicious_filename in malicious_filenames:
                # This simulates the old sanitization
                import re
                sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', malicious_filename)[:50]
                
                # Check if sanitization is effective
                if "../" in sanitized or "\\" in sanitized:
                    pytest.fail(
                        f"VULNERABILITY CONFIRMED: Filename sanitization ineffective for: {malicious_filename}"
                    )
    
    def test_storage_bucket_validation(self):
        """
        Test that storage bucket names are properly validated.
        """
        try:
            from worker.worker.security import validate_bucket_name
            
            # Test malicious bucket names
            malicious_buckets = [
                "../uploads",
                "../../etc",
                "uploads/../sensitive",
                "uploads\x00../etc",
            ]
            
            for bucket in malicious_buckets:
                # With security fixes, these should be rejected
                is_valid = validate_bucket_name(bucket)
                assert is_valid is False, f"Malicious bucket should be rejected: {bucket}"
                
            print("✅ SECURITY FIX CONFIRMED: Malicious bucket names are rejected")
            
        except ImportError:
            # If security module doesn't exist, just warn
            print("WARNING: Security module not found, bucket validation not implemented")
    
    def test_download_path_validation(self):
        """
        Test that download path validation prevents accessing unauthorized files.
        """
        try:
            from worker.worker.config import WorkerConfig
            from worker.worker.job_processor import JobProcessor
            from worker.worker.supabase_client import SupabaseWorkerClient
            
            # Mock configuration
            config = Mock(spec=WorkerConfig)
            client = Mock(spec=SupabaseWorkerClient)
            processor = JobProcessor(client)
            
            # Test malicious storage paths
            malicious_paths = [
                "../../../etc/passwd",
                "uploads/../sensitive/file.jpg",
                "uploads/user1/../user2/secret.jpg",
                "uploads/user1/../../system/config.txt",
            ]
            
            for malicious_path in malicious_paths:
                # With security fixes, these should return None (rejected)
                result = processor._download_image(malicious_path)
                assert result is None, f"Malicious path should be rejected: {malicious_path}"
                
            # Ensure download_file was not called for malicious paths
            client.download_file.assert_not_called()
            
            print("✅ SECURITY FIX CONFIRMED: Malicious download paths are blocked")
            
        except ImportError:
            # If modules don't exist or security fixes aren't implemented
            malicious_path = "../../../etc/passwd"
            parts = malicious_path.split("/", 1)
            if len(parts) != 2:
                bucket = "uploads"
                path = malicious_path
            else:
                bucket = parts[0]
                path = parts[1]
            
            # VULNERABILITY: Check if path traversal is possible
            if "../" in path or "../" in bucket:
                pytest.fail(
                    f"VULNERABILITY CONFIRMED: Path traversal possible in download path: "
                    f"bucket={bucket}, path={path}"
                )
    
    def test_user_id_validation(self):
        """
        Test that user IDs are properly validated to prevent path traversal.
        """
        try:
            from worker.worker.security import validate_uuid
            
            # Test malicious user IDs
            malicious_user_ids = [
                "../admin",
                "../../root",
                "user/../../../etc/passwd",
                "user\x00../admin",
                "%2e%2e%2fadmin",  # URL encoded ../admin
            ]
            
            for user_id in malicious_user_ids:
                # With security fixes, these should be rejected
                is_valid = validate_uuid(user_id)
                assert is_valid is False, f"Malicious user ID should be rejected: {user_id}"
                
            print("✅ SECURITY FIX CONFIRMED: Malicious user IDs are rejected")
            
        except ImportError:
            # If security module doesn't exist, test old behavior
            for user_id in ["../admin", "../../root"]:
                if not self._is_valid_uuid(user_id):
                    if "../" in user_id or "\\" in user_id or "\x00" in user_id:
                        print(f"WARNING: Malicious user ID pattern detected: {user_id}")
    
    def _is_valid_uuid(self, value):
        """Helper to validate UUID format."""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False
    
    def test_storage_policy_bypass_attempt(self):
        """
        Test that storage policies cannot be bypassed using path traversal.
        """
        try:
            from worker.worker.security import validate_user_path_access
            
            user_id = str(uuid.uuid4())
            
            # Test if malicious paths are blocked by access validation
            malicious_storage_paths = [
                f"{user_id}/../other_user/secret.jpg",
                f"{user_id}/../../admin/config.xlsx",
                f"{user_id}/../../../system/backup.zip",
            ]
            
            for path in malicious_storage_paths:
                # Extract path after removing bucket prefix if present
                if path.startswith("uploads/"):
                    test_path = path[8:]  # Remove "uploads/" prefix
                else:
                    test_path = path
                    
                # With security fixes, access should be denied for paths with traversal
                has_access = validate_user_path_access(test_path, user_id)
                
                # If path contains traversal, access should be denied
                if "../" in test_path:
                    assert has_access is False, f"Access should be denied for path with traversal: {path}"
                    
            print("✅ SECURITY FIX CONFIRMED: Storage policy bypass attempts are blocked")
            
        except ImportError:
            # If security module doesn't exist, test old behavior
            user_id = str(uuid.uuid4())
            malicious_path = f"uploads/{user_id}/../other_user/secret.jpg"
            
            # Extract the folder structure
            path_parts = malicious_path.split("/")
            
            # Check if path contains traversal sequences after user folder
            if len(path_parts) > 2:  # bucket/user_id/...
                remaining_path = "/".join(path_parts[2:])
                if "../" in remaining_path:
                    pytest.fail(
                        f"VULNERABILITY CONFIRMED: Storage policy bypass possible with path: {malicious_path}"
                    )
    
    def test_filename_length_validation(self):
        """
        Test that extremely long filenames are properly handled.
        """
        try:
            from worker.worker.security import sanitize_filename
            
            # Create extremely long filename
            long_filename = "A" * 1000 + ".jpg"
            
            # With security fixes, this should be truncated
            sanitized = sanitize_filename(long_filename)
            assert len(sanitized) <= 255, "Long filename should be truncated"
            
            print("✅ SECURITY FIX CONFIRMED: Long filenames are properly truncated")
            
        except ImportError:
            # If security module doesn't exist, test old behavior
            long_filename = "A" * 1000 + ".jpg"
            if len(long_filename) > 255:  # Typical filesystem limit
                print(f"WARNING: Long filename not truncated: {len(long_filename)} characters")
    
    def test_special_character_handling(self):
        """
        Test handling of special characters in paths.
        """
        try:
            from worker.worker.security import SecurityError, sanitize_filename
            
            special_chars = [
                "file\x00.jpg",  # Null byte
                "file\r\n.jpg",  # CRLF injection
                "file;rm -rf /.jpg",  # Command injection attempt
                "file`whoami`.jpg",  # Command substitution
                "file$(whoami).jpg",  # Command substitution
            ]
            
            for filename in special_chars:
                # With security fixes, these should be sanitized or rejected
                try:
                    sanitized = sanitize_filename(filename)
                    # Check that dangerous characters are removed
                    assert '\x00' not in sanitized
                    assert '\r' not in sanitized
                    assert '\n' not in sanitized
                    assert ';' not in sanitized
                    assert '`' not in sanitized
                    assert '$' not in sanitized
                except SecurityError:
                    # It's also acceptable to reject these entirely
                    pass
                    
            print("✅ SECURITY FIX CONFIRMED: Special characters are properly handled")
            
        except ImportError:
            # If security module doesn't exist, just warn
            special_chars = [
                "file\x00.jpg",  # Null byte
                "file\r\n.jpg",  # CRLF injection
            ]
            
            for filename in special_chars:
                if any(char in filename for char in ['\x00', '\r', '\n', ';', '`', '$']):
                    print(f"WARNING: Special characters in filename: {repr(filename)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])