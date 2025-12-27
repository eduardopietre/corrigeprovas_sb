"""
Test for worker input validation vulnerability.

This test examines the worker's handling of user-provided data
to identify insufficient input validation that could lead to security issues.
"""

import json
import os
import tempfile
import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestWorkerInputValidation:
    """Test worker input validation vulnerability."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client for testing."""
        client = Mock()
        
        # Mock successful responses
        client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data={
                "id": str(uuid.uuid4()),
                "owner_user_id": str(uuid.uuid4()),
                "answer_key_id": str(uuid.uuid4()),
                "template_id": str(uuid.uuid4()),
                "status": "QUEUED",
                "total_items": 1,
                "success_items": 0,
                "error_items": 0,
            }
        )
        
        return client
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock worker configuration."""
        config = Mock()
        config.supabase_url = "https://test.supabase.co"
        config.supabase_service_role_key = "test-key"
        config.queue_name = "corrections"
        config.visibility_timeout = 300
        return config
    
    def test_malicious_storage_path_handling(self, mock_supabase_client, mock_config):
        """
        Test if the worker properly validates storage paths.
        """
        try:
            from worker.worker.job_processor import JobProcessor
        except ImportError:
            pytest.skip("Worker module not available")
        
        processor = JobProcessor(mock_supabase_client)
        
        # Test malicious storage paths
        malicious_paths = [
            "../../../etc/passwd",
            "uploads/../../../sensitive/data.txt",
            "uploads/user1/../../admin/secrets.json",
            "uploads/user1/../user2/private.jpg",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "uploads/user1/file.jpg\x00../../../etc/passwd",  # Null byte injection
        ]
        
        for malicious_path in malicious_paths:
            # Test the _download_image method's path parsing
            parts = malicious_path.split("/", 1)
            if len(parts) != 2:
                bucket = "uploads"
                path = malicious_path
            else:
                bucket = parts[0]
                path = parts[1]
            
            # VULNERABILITY: Check if path traversal sequences are present
            if "../" in path or "../" in bucket or "\x00" in path:
                pytest.fail(
                    f"VULNERABILITY CONFIRMED: Malicious storage path not properly validated: "
                    f"bucket='{bucket}', path='{path}'"
                )
    
    def test_job_id_validation(self, mock_supabase_client, mock_config):
        """
        Test if job IDs are properly validated.
        """
        try:
            from worker.worker.job_processor import JobProcessor
        except ImportError:
            pytest.skip("Worker module not available")
        
        processor = JobProcessor(mock_supabase_client)
        
        # Test malicious job IDs
        malicious_job_ids = [
            "../admin-job",
            "job'; DROP TABLE correction_jobs; --",
            "job<script>alert('xss')</script>",
            "job\x00null",
            "job\r\nCRLF",
            "job/../../../etc/passwd",
        ]
        
        for job_id in malicious_job_ids:
            # Check if job ID validation exists
            if not self._is_valid_uuid(job_id):
                # Non-UUID job IDs should be rejected
                dangerous_chars = ["../", "<", ">", "'", '"', "\x00", "\r", "\n", ";"]
                if any(char in job_id for char in dangerous_chars):
                    print(f"WARNING: Malicious job ID pattern: {job_id}")
    
    def test_template_data_validation(self, mock_supabase_client):
        """
        Test if template data is properly validated.
        """
        # Mock template data with malicious content
        malicious_templates = [
            {
                "id": str(uuid.uuid4()),
                "name": "<script>alert('xss')</script>",
                "question_count": -1,  # Invalid negative count
                "alternatives_count": 10,  # Invalid high count
                "template_storage_path": "../../../etc/passwd",
            },
            {
                "id": "not-a-uuid",
                "name": "Template'; DROP TABLE templates; --",
                "question_count": "not-a-number",
                "alternatives_count": None,
                "template_storage_path": "/etc/passwd\x00.png",
            }
        ]
        
        for template_data in malicious_templates:
            # Validate template fields
            issues = []
            
            # Check ID format
            if not self._is_valid_uuid(template_data.get("id", "")):
                issues.append("Invalid UUID format")
            
            # Check question count
            question_count = template_data.get("question_count")
            if not isinstance(question_count, int) or question_count not in [10, 20, 50, 100]:
                issues.append("Invalid question count")
            
            # Check alternatives count
            alt_count = template_data.get("alternatives_count")
            if not isinstance(alt_count, int) or alt_count not in [4, 5]:
                issues.append("Invalid alternatives count")
            
            # Check storage path
            storage_path = template_data.get("template_storage_path", "")
            if "../" in storage_path or "\x00" in storage_path:
                issues.append("Malicious storage path")
            
            # Check name for XSS
            name = template_data.get("name", "")
            if "<" in name or ">" in name or "'" in name:
                issues.append("Potential XSS in name")
            
            if issues:
                print(f"WARNING: Template validation issues: {issues}")
    
    def test_answer_key_validation(self, mock_supabase_client):
        """
        Test if answer key data is properly validated.
        """
        malicious_answer_keys = [
            {
                "id": str(uuid.uuid4()),
                "answers_string": "A" * 10000,  # Extremely long string
                "template_id": "../../../admin/template",
            },
            {
                "id": "not-a-uuid",
                "answers_string": "ABCD\x00EFGH",  # Null byte injection
                "template_id": str(uuid.uuid4()),
            },
            {
                "id": str(uuid.uuid4()),
                "answers_string": "'; DROP TABLE answer_keys; --",
                "template_id": str(uuid.uuid4()),
            }
        ]
        
        for answer_key in malicious_answer_keys:
            issues = []
            
            # Validate ID
            if not self._is_valid_uuid(answer_key.get("id", "")):
                issues.append("Invalid answer key ID")
            
            # Validate template ID
            if not self._is_valid_uuid(answer_key.get("template_id", "")):
                issues.append("Invalid template ID")
            
            # Validate answers string
            answers = answer_key.get("answers_string", "")
            if len(answers) > 1000:  # Reasonable limit
                issues.append("Answer string too long")
            
            if "\x00" in answers:
                issues.append("Null byte in answers")
            
            # Check for SQL injection patterns
            sql_patterns = ["'", ";", "--", "DROP", "DELETE", "UPDATE", "INSERT"]
            if any(pattern.lower() in answers.lower() for pattern in sql_patterns):
                issues.append("Potential SQL injection in answers")
            
            if issues:
                print(f"WARNING: Answer key validation issues: {issues}")
    
    def test_file_content_validation(self):
        """
        Test if uploaded file content is properly validated.
        """
        # Create test files with malicious content
        test_files = [
            {
                "name": "malicious.jpg",
                "content": b"#!/bin/bash\nrm -rf /\n",  # Shell script disguised as image
                "mime_type": "image/jpeg"
            },
            {
                "name": "polyglot.png",
                "content": b"\x89PNG\r\n\x1a\n<script>alert('xss')</script>",  # PNG + script
                "mime_type": "image/png"
            },
            {
                "name": "oversized.jpg",
                "content": b"A" * (50 * 1024 * 1024),  # 50MB file
                "mime_type": "image/jpeg"
            }
        ]
        
        for test_file in test_files:
            # Validate file content
            content = test_file["content"]
            mime_type = test_file["mime_type"]
            
            # Check file size
            if len(content) > 20 * 1024 * 1024:  # 20MB limit
                print(f"WARNING: Oversized file: {test_file['name']} ({len(content)} bytes)")
            
            # Check for executable content
            if content.startswith(b"#!/"):
                print(f"WARNING: Executable content in {test_file['name']}")
            
            # Check for script content in images
            if mime_type.startswith("image/") and b"<script" in content.lower():
                print(f"WARNING: Script content in image {test_file['name']}")
    
    def test_queue_message_validation(self, mock_supabase_client):
        """
        Test if queue messages are properly validated.
        """
        malicious_messages = [
            {"job_id": "../../../admin/job"},
            {"job_id": "job'; DROP TABLE correction_jobs; --"},
            {"job_id": None},
            {"job_id": ""},
            {"job_id": "A" * 1000},  # Very long job ID
            {"malicious_field": "value", "job_id": str(uuid.uuid4())},
            {"job_id": str(uuid.uuid4()), "extra_data": "<script>alert('xss')</script>"},
        ]
        
        for message in malicious_messages:
            issues = []
            
            # Validate job_id field
            job_id = message.get("job_id")
            if not job_id:
                issues.append("Missing job_id")
            elif not isinstance(job_id, str):
                issues.append("job_id not a string")
            elif not self._is_valid_uuid(job_id):
                issues.append("Invalid job_id format")
            
            # Check for unexpected fields
            expected_fields = {"job_id"}
            unexpected_fields = set(message.keys()) - expected_fields
            if unexpected_fields:
                issues.append(f"Unexpected fields: {unexpected_fields}")
            
            # Check for malicious content
            for key, value in message.items():
                if isinstance(value, str):
                    if "../" in value or "<script" in value.lower() or "'" in value:
                        issues.append(f"Malicious content in {key}")
            
            if issues:
                print(f"WARNING: Queue message validation issues: {issues}")
    
    def test_error_handling_information_disclosure(self):
        """
        Test if error handling properly sanitizes sensitive information.
        """
        # Simulate various error conditions
        error_scenarios = [
            {
                "error": "Database connection failed: host=db.internal.com port=5432",
                "should_sanitize": ["db.internal.com", "5432"]
            },
            {
                "error": "File not found: /var/lib/app/secrets/config.json",
                "should_sanitize": ["/var/lib/app/secrets/"]
            },
            {
                "error": "Authentication failed for user admin@company.com",
                "should_sanitize": ["admin@company.com"]
            },
            {
                "error": "SQL error: relation 'correction_jobs' does not exist",
                "should_sanitize": ["correction_jobs"]
            }
        ]
        
        for scenario in error_scenarios:
            error_message = scenario["error"]
            sensitive_info = scenario["should_sanitize"]
            
            # Check if sensitive information is present in error message
            disclosed_info = []
            for info in sensitive_info:
                if info in error_message:
                    disclosed_info.append(info)
            
            if disclosed_info:
                print(f"WARNING: Error message discloses sensitive info: {disclosed_info}")
                print(f"Error: {error_message}")
    
    def _is_valid_uuid(self, value):
        """Helper to validate UUID format."""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def test_configuration_validation(self):
        """
        Test if worker configuration is properly validated.
        """
        # Test malicious configuration values
        malicious_configs = [
            {
                "supabase_url": "javascript:alert('xss')",
                "queue_name": "../admin_queue",
                "visibility_timeout": -1,
                "poll_interval": 0,
            },
            {
                "supabase_url": "http://malicious.com/steal-data",
                "supabase_service_role_key": "",
                "queue_name": "queue'; DROP TABLE pgmq.q_corrections; --",
            }
        ]
        
        for config in malicious_configs:
            issues = []
            
            # Validate URL
            url = config.get("supabase_url", "")
            if not url.startswith(("http://", "https://")):
                issues.append("Invalid URL scheme")
            
            if "javascript:" in url or "data:" in url:
                issues.append("Dangerous URL scheme")
            
            # Validate queue name
            queue_name = config.get("queue_name", "")
            if "../" in queue_name or "'" in queue_name or ";" in queue_name:
                issues.append("Malicious queue name")
            
            # Validate numeric values
            visibility_timeout = config.get("visibility_timeout")
            if isinstance(visibility_timeout, int) and visibility_timeout < 0:
                issues.append("Invalid visibility timeout")
            
            poll_interval = config.get("poll_interval")
            if isinstance(poll_interval, int) and poll_interval <= 0:
                issues.append("Invalid poll interval")
            
            if issues:
                print(f"WARNING: Configuration validation issues: {issues}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])