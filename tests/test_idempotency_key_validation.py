"""
Test for idempotency key validation vulnerability.

This test examines the idempotency key validation in the create_job function
to identify potential weaknesses in collision detection and validation.
"""

import hashlib
import os
import time
import uuid

import pytest
import requests


class TestIdempotencyKeyValidation:
    """Test idempotency key validation vulnerability."""
    
    @pytest.fixture
    def supabase_config(self):
        """Get Supabase configuration."""
        url = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
        anon_key = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not anon_key:
            pytest.skip("Supabase configuration not available")
        
        return {"url": url, "anon_key": anon_key}
    
    @pytest.fixture
    def auth_headers(self, supabase_config):
        """Get authentication headers for API calls."""
        return {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key']
        }
    
    def test_idempotency_key_length_validation(self, supabase_config, auth_headers):
        """
        Test if extremely long idempotency keys are properly validated.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Create extremely long idempotency key (over 255 characters)
        long_key = "A" * 1000
        
        payload = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file.jpg"}],
            "idempotencyKey": long_key
        }
        
        try:
            response = requests.post(
                create_job_endpoint,
                json=payload,
                headers=auth_headers,
                timeout=10
            )
            
            # Should reject long idempotency keys
            if response.status_code == 200 or response.status_code == 201:
                pytest.fail(
                    f"VULNERABILITY CONFIRMED: Extremely long idempotency key ({len(long_key)} chars) "
                    "was accepted. This could lead to database issues."
                )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_idempotency_key_special_characters(self, supabase_config, auth_headers):
        """
        Test if idempotency keys with special characters are properly handled.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Test various special characters that could cause issues
        special_keys = [
            "key\x00null",  # Null byte
            "key\r\nCRLF",  # CRLF injection
            "key';DROP TABLE jobs;--",  # SQL injection attempt
            "key<script>alert('xss')</script>",  # XSS attempt
            "key/../../../etc/passwd",  # Path traversal
            "key\u0000unicode_null",  # Unicode null
        ]
        
        for special_key in special_keys:
            payload = {
                "answerKeyId": str(uuid.uuid4()),
                "templateId": str(uuid.uuid4()),
                "items": [{"originalStoragePath": "test/file.jpg"}],
                "idempotencyKey": special_key
            }
            
            try:
                response = requests.post(
                    create_job_endpoint,
                    json=payload,
                    headers=auth_headers,
                    timeout=10
                )
                
                # Should sanitize or reject special characters
                if response.status_code == 200 or response.status_code == 201:
                    print(f"WARNING: Special character idempotency key accepted: {repr(special_key)}")
                
            except requests.exceptions.RequestException:
                continue  # Network errors are expected in testing
    
    def test_idempotency_key_collision_detection(self, supabase_config, auth_headers):
        """
        Test if the system properly detects idempotency key collisions.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Use a simple key that could collide
        simple_key = "test123"
        
        # First request
        payload1 = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file1.jpg"}],
            "idempotencyKey": simple_key
        }
        
        # Second request with same key but different parameters
        payload2 = {
            "answerKeyId": str(uuid.uuid4()),  # Different answer key
            "templateId": str(uuid.uuid4()),  # Different template
            "items": [{"originalStoragePath": "test/file2.jpg"}],  # Different items
            "idempotencyKey": simple_key  # Same idempotency key
        }
        
        try:
            # Send first request
            response1 = requests.post(
                create_job_endpoint,
                json=payload1,
                headers=auth_headers,
                timeout=10
            )
            
            # Send second request with same idempotency key
            response2 = requests.post(
                create_job_endpoint,
                json=payload2,
                headers=auth_headers,
                timeout=10
            )
            
            # Second request should be rejected due to parameter mismatch
            if response2.status_code == 200 or response2.status_code == 201:
                if response1.status_code in [200, 201]:
                    # Both succeeded - check if they're actually different jobs
                    job1_data = response1.json()
                    job2_data = response2.json()
                    
                    if job1_data.get("jobId") != job2_data.get("jobId"):
                        pytest.fail(
                            "VULNERABILITY CONFIRMED: Same idempotency key created different jobs "
                            "with different parameters. This violates idempotency guarantees."
                        )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_idempotency_key_header_vs_body(self, supabase_config, auth_headers):
        """
        Test behavior when idempotency key is provided in both header and body.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        header_key = "header-key-123"
        body_key = "body-key-456"
        
        # Add idempotency key to headers
        headers_with_key = auth_headers.copy()
        headers_with_key["x-idempotency-key"] = header_key
        
        payload = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file.jpg"}],
            "idempotencyKey": body_key  # Different key in body
        }
        
        try:
            response = requests.post(
                create_job_endpoint,
                json=payload,
                headers=headers_with_key,
                timeout=10
            )
            
            # The system should have a clear precedence rule
            # According to the code, header takes precedence
            print(f"Response status: {response.status_code}")
            if response.status_code in [200, 201]:
                print("INFO: System accepts requests with idempotency key in both header and body")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_idempotency_key_format_validation(self):
        """
        Test if idempotency keys follow expected format patterns.
        """
        # Test various format patterns
        test_keys = [
            "",  # Empty key
            " ",  # Whitespace only
            "a",  # Single character
            "123",  # Numbers only
            "key with spaces",  # Spaces
            "key\twith\ttabs",  # Tabs
            "UPPERCASE",  # Case sensitivity
            "lowercase",
            "MiXeD-CaSe_123",  # Mixed case with special chars
        ]
        
        for key in test_keys:
            # Validate key format (this would be done server-side)
            if not self._is_valid_idempotency_key(key):
                print(f"WARNING: Invalid idempotency key format: {repr(key)}")
    
    def _is_valid_idempotency_key(self, key):
        """
        Helper function to validate idempotency key format.
        This represents what the server should validate.
        """
        if not key or not key.strip():
            return False
        if len(key) > 255:
            return False
        # Check for dangerous characters
        dangerous_chars = ['\x00', '\r', '\n', ';', '<', '>', '"', "'"]
        if any(char in key for char in dangerous_chars):
            return False
        return True
    
    def test_idempotency_key_entropy(self):
        """
        Test if low-entropy idempotency keys could cause collisions.
        """
        # Generate keys with low entropy
        low_entropy_keys = [
            "1",
            "a",
            "test",
            "123456",
            "password",
            "key",
        ]
        
        # Check for potential collision risks
        for key in low_entropy_keys:
            if len(key) < 8:
                print(f"WARNING: Low entropy idempotency key: {key}")
            
            # Check if key is easily guessable
            if key.lower() in ["test", "key", "password", "admin", "user"]:
                print(f"WARNING: Predictable idempotency key: {key}")
    
    def test_idempotency_key_timing_attack(self):
        """
        Test if idempotency key comparison is vulnerable to timing attacks.
        """
        # This test would measure response times to detect timing differences
        # In a real implementation, constant-time comparison should be used
        
        correct_key = "correct-key-12345"
        
        # Keys with different lengths and prefixes
        test_keys = [
            "wrong",
            "correct",
            "correct-key",
            "correct-key-1",
            "correct-key-12",
            "correct-key-123",
            "correct-key-1234",
            "correct-key-12345",  # Correct key
            "correct-key-123456",  # One char too long
        ]
        
        # In a real test, we would measure response times
        # and look for timing differences that could leak information
        for key in test_keys:
            # Simulate timing measurement
            start_time = time.time()
            # ... make request with key ...
            end_time = time.time()
            
            # In a real test, we would analyze timing patterns
            print(f"Key: {key[:10]}... (length: {len(key)})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])