"""
Test for storage path traversal vulnerability.

This test attempts to exploit path traversal vulnerabilities in storage
path construction to access files outside user directories.
"""

import os
import uuid
from unittest.mock import Mock, patch

import pytest


class TestStoragePathTraversal:
    """Test storage path traversal vulnerability."""
    
    def test_path_traversal_in_upload_path(self):
        """
        Test if upload path construction is vulnerable to path traversal.
        """
        # Simulate malicious user ID with path traversal
        malicious_user_id = "../../../etc/passwd"
        filename = "test.jpg"
        
        # This is how paths are constructed in get_upload_urls
        constructed_path = f"{malicious_user_id}/{filename}"
        
        # VULNERABILITY: If not properly sanitized, this could access system files
        if "../" in constructed_path:
            pytest.fail(
                f"VULNERABILITY CONFIRMED: Path traversal possible in upload path: {constructed_path}"
            )
    
    def test_path_traversal_in_result_path(self):
        """
        Test if result path construction is vulnerable to path traversal.
        """
        # Simulate job processor path construction
        user_id = str(uuid.uuid4())
        malicious_job_id = "../../../sensitive_data"
        item_index = 1
        
        # This mimics the path construction in job_processor.py
        path = f"{user_id}/{malicious_job_id}/marked_{item_index:04d}.jpg"
        
        # VULNERABILITY: Job ID could contain path traversal sequences
        if "../" in path:
            pytest.fail(
                f"VULNERABILITY CONFIRMED: Path traversal possible in result path: {path}"
            )
    
    def test_filename_sanitization(self):
        """
        Test if filenames are properly sanitized to prevent path traversal.
        """
        # Test various malicious filename patterns
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "file.jpg/../../../sensitive.txt",
            "normal.jpg\x00../../../etc/passwd",  # Null byte injection
            "file.jpg%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
        ]
        
        for malicious_filename in malicious_filenames:
            # This simulates the sanitization in get_upload_urls
            import re
            sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', malicious_filename)[:50]
            
            # Check if sanitization is effective
            if "../" in sanitized or "\\" in sanitized:
                pytest.fail(
                    f"VULNERABILITY CONFIRMED: Filename sanitization ineffective for: {malicious_filename}"
                )
    
    def test_storage_bucket_validation(self):
        """
        Test if storage bucket names are properly validated.
        """
        # Test malicious bucket names
        malicious_buckets = [
            "../uploads",
            "../../etc",
            "uploads/../sensitive",
            "uploads\x00../etc",
        ]
        
        for bucket in malicious_buckets:
            # This simulates bucket validation that should exist
            if "../" in bucket or "\\" in bucket or "\x00" in bucket:
                print(f"WARNING: Malicious bucket name detected: {bucket}")
                # In a real system, this should be rejected
    
    @patch('worker.worker.job_processor.JobProcessor._download_image')
    def test_download_path_validation(self, mock_download):
        """
        Test if download path validation prevents accessing unauthorized files.
        """
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
            # This simulates the path parsing in _download_image
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
        Test if user IDs are properly validated to prevent path traversal.
        """
        # Test malicious user IDs
        malicious_user_ids = [
            "../admin",
            "../../root",
            "user/../../../etc/passwd",
            "user\x00../admin",
            "%2e%2e%2fadmin",  # URL encoded ../admin
        ]
        
        for user_id in malicious_user_ids:
            # This simulates user ID validation that should exist
            if not self._is_valid_uuid(user_id):
                if "../" in user_id or "\\" in user_id or "\x00" in user_id:
                    print(f"WARNING: Malicious user ID pattern detected: {user_id}")
                    # In a real system, this should be rejected
    
    def _is_valid_uuid(self, value):
        """Helper to validate UUID format."""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False
    
    def test_storage_policy_bypass_attempt(self):
        """
        Test if storage policies can be bypassed using path traversal.
        """
        # Simulate RLS policy check for storage access
        user_id = str(uuid.uuid4())
        
        # Test if malicious paths could bypass RLS policies
        malicious_storage_paths = [
            f"uploads/{user_id}/../other_user/secret.jpg",
            f"results/{user_id}/../../admin/config.xlsx",
            f"exports/{user_id}/../../../system/backup.zip",
        ]
        
        for path in malicious_storage_paths:
            # Extract the folder structure
            path_parts = path.split("/")
            
            # Check if path contains traversal sequences after user folder
            if len(path_parts) > 2:  # bucket/user_id/...
                remaining_path = "/".join(path_parts[2:])
                if "../" in remaining_path:
                    pytest.fail(
                        f"VULNERABILITY CONFIRMED: Storage policy bypass possible with path: {path}"
                    )
    
    def test_filename_length_validation(self):
        """
        Test if extremely long filenames are properly handled.
        """
        # Create extremely long filename
        long_filename = "A" * 1000 + ".jpg"
        
        # This simulates filename handling
        if len(long_filename) > 255:  # Typical filesystem limit
            print(f"WARNING: Long filename not truncated: {len(long_filename)} characters")
            # Should be truncated or rejected
    
    def test_special_character_handling(self):
        """
        Test handling of special characters in paths.
        """
        special_chars = [
            "file\x00.jpg",  # Null byte
            "file\r\n.jpg",  # CRLF injection
            "file;rm -rf /.jpg",  # Command injection attempt
            "file`whoami`.jpg",  # Command substitution
            "file$(whoami).jpg",  # Command substitution
        ]
        
        for filename in special_chars:
            # Check if special characters are properly handled
            if any(char in filename for char in ['\x00', '\r', '\n', ';', '`', '$']):
                print(f"WARNING: Special characters in filename: {repr(filename)}")
                # These should be sanitized or rejected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])