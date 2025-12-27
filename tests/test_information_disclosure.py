"""
Test for information disclosure vulnerability.

This test examines error messages and responses to identify
information leakage that could aid attackers.
"""

import json
import os
import uuid

import pytest
import requests


class TestInformationDisclosure:
    """Test information disclosure vulnerability."""
    
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
    
    def test_error_message_information_leakage(self, supabase_config, auth_headers):
        """
        Test if error messages leak sensitive system information.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Test with non-existent answer key ID
        payload = {
            "answerKeyId": str(uuid.uuid4()),  # Random UUID that doesn't exist
            "templateId": str(uuid.uuid4()),   # Random UUID that doesn't exist
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        try:
            response = requests.post(
                create_job_endpoint,
                json=payload,
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code >= 400:
                error_data = response.json()
                error_message = str(error_data)
                
                # Check for information disclosure in error messages
                sensitive_info = [
                    "template_id",  # Database column names
                    "answer_key_id",
                    "owner_user_id",
                    "institution_id",
                    "PGRST116",  # PostgREST error codes
                    "relation",  # Database relation names
                    "does not exist",  # Database existence info
                    "permission denied",  # Access control details
                    "RLS",  # Row Level Security references
                    "pg_",  # PostgreSQL internal references
                    "/var/",  # File system paths
                    "localhost",  # Internal hostnames
                    "127.0.0.1",  # Internal IPs
                ]
                
                disclosed_info = []
                for info in sensitive_info:
                    if info.lower() in error_message.lower():
                        disclosed_info.append(info)
                
                if disclosed_info:
                    pytest.fail(
                        f"VULNERABILITY CONFIRMED: Error message discloses sensitive information: "
                        f"{disclosed_info}. Full error: {error_message[:200]}..."
                    )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_stack_trace_disclosure(self, supabase_config, auth_headers):
        """
        Test if stack traces are exposed in error responses.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Send malformed request to trigger server error
        malformed_payload = {
            "answerKeyId": "not-a-uuid",  # Invalid UUID format
            "templateId": None,  # Null value
            "items": "not-an-array"  # Wrong type
        }
        
        try:
            response = requests.post(
                create_job_endpoint,
                json=malformed_payload,
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code >= 400:
                error_text = response.text
                
                # Check for stack trace indicators
                stack_trace_indicators = [
                    "at ",  # JavaScript stack trace
                    "Error:",  # Error object
                    "TypeError:",
                    "ReferenceError:",
                    "function",  # Function names in stack
                    "line ",  # Line numbers
                    ".ts:",  # TypeScript file references
                    ".js:",  # JavaScript file references
                    "deno:",  # Deno runtime references
                    "file://",  # File URLs
                ]
                
                disclosed_traces = []
                for indicator in stack_trace_indicators:
                    if indicator in error_text:
                        disclosed_traces.append(indicator)
                
                if disclosed_traces:
                    pytest.fail(
                        f"VULNERABILITY CONFIRMED: Stack trace information disclosed: "
                        f"{disclosed_traces}. This reveals internal system structure."
                    )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_database_schema_disclosure(self, supabase_config, auth_headers):
        """
        Test if database schema information is disclosed in responses.
        """
        # Test various endpoints for schema disclosure
        endpoints = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls",
            "/functions/v1/get_result_urls",
        ]
        
        for endpoint in endpoints:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                # Send request with invalid data to trigger validation errors
                response = requests.post(
                    url,
                    json={"invalid": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                if response.status_code >= 400:
                    response_text = response.text.lower()
                    
                    # Check for database schema information
                    schema_info = [
                        "correction_jobs",  # Table names
                        "correction_items",
                        "answer_keys",
                        "templates",
                        "profiles",
                        "subscriptions",
                        "usage_ledger",
                        "column",  # Column references
                        "constraint",  # Database constraints
                        "foreign key",  # FK references
                        "primary key",  # PK references
                        "unique",  # Unique constraints
                        "not null",  # NULL constraints
                    ]
                    
                    disclosed_schema = []
                    for info in schema_info:
                        if info in response_text:
                            disclosed_schema.append(info)
                    
                    if disclosed_schema:
                        print(f"WARNING: Database schema info disclosed in {endpoint}: {disclosed_schema}")
            
            except requests.exceptions.RequestException:
                continue
    
    def test_internal_id_disclosure(self, supabase_config, auth_headers):
        """
        Test if internal IDs or system information is disclosed.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Valid request to see what information is returned
        payload = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        try:
            response = requests.post(
                create_job_endpoint,
                json=payload,
                headers=auth_headers,
                timeout=10
            )
            
            # Check response headers for information disclosure
            sensitive_headers = [
                "x-powered-by",  # Technology stack info
                "server",  # Server software info
                "x-version",  # Version information
                "x-request-id",  # Internal request tracking
                "x-trace-id",  # Tracing information
            ]
            
            disclosed_headers = []
            for header in sensitive_headers:
                if header in response.headers:
                    disclosed_headers.append(f"{header}: {response.headers[header]}")
            
            if disclosed_headers:
                print(f"INFO: Potentially sensitive headers disclosed: {disclosed_headers}")
            
            # Check response body for internal information
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    
                    # Look for internal system information
                    if isinstance(response_data, dict):
                        internal_fields = [
                            "internal_id",
                            "system_id",
                            "worker_id",
                            "node_id",
                            "instance_id",
                            "debug_info",
                            "trace_id",
                        ]
                        
                        disclosed_fields = []
                        for field in internal_fields:
                            if field in response_data:
                                disclosed_fields.append(field)
                        
                        if disclosed_fields:
                            print(f"WARNING: Internal system fields disclosed: {disclosed_fields}")
                
                except json.JSONDecodeError:
                    pass
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_timing_information_disclosure(self, supabase_config, auth_headers):
        """
        Test if response timing reveals information about system state.
        """
        import time
        
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Test with existing vs non-existing resources
        test_cases = [
            {
                "name": "non_existing_answer_key",
                "payload": {
                    "answerKeyId": str(uuid.uuid4()),
                    "templateId": str(uuid.uuid4()),
                    "items": [{"originalStoragePath": "test/file.jpg"}]
                }
            },
            {
                "name": "malformed_uuid",
                "payload": {
                    "answerKeyId": "not-a-uuid",
                    "templateId": "also-not-a-uuid",
                    "items": [{"originalStoragePath": "test/file.jpg"}]
                }
            }
        ]
        
        timing_results = {}
        
        for test_case in test_cases:
            try:
                start_time = time.time()
                response = requests.post(
                    create_job_endpoint,
                    json=test_case["payload"],
                    headers=auth_headers,
                    timeout=10
                )
                end_time = time.time()
                
                timing_results[test_case["name"]] = {
                    "duration": end_time - start_time,
                    "status_code": response.status_code
                }
                
            except requests.exceptions.RequestException:
                continue
        
        # Analyze timing differences
        if len(timing_results) >= 2:
            durations = [result["duration"] for result in timing_results.values()]
            max_duration = max(durations)
            min_duration = min(durations)
            
            # If there's a significant timing difference, it might reveal information
            if max_duration > min_duration * 2:  # More than 2x difference
                print(f"WARNING: Significant timing differences detected: {timing_results}")
                print("This could reveal information about resource existence or system state")
    
    def test_cors_header_information_disclosure(self, supabase_config):
        """
        Test if CORS headers reveal sensitive information.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        try:
            # Send OPTIONS request to check CORS headers
            response = requests.options(
                create_job_endpoint,
                timeout=10
            )
            
            cors_headers = {
                key: value for key, value in response.headers.items()
                if key.lower().startswith('access-control-')
            }
            
            # Check for overly permissive CORS settings
            if cors_headers.get('Access-Control-Allow-Origin') == '*':
                print("WARNING: CORS allows all origins (*) - this might be too permissive")
            
            # Check for exposed headers
            exposed_headers = cors_headers.get('Access-Control-Expose-Headers', '')
            if exposed_headers:
                print(f"INFO: CORS exposes headers: {exposed_headers}")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])