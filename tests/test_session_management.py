"""
Test for session management vulnerability.

This test examines session handling, token management, and authentication
security to identify potential session-related vulnerabilities.
"""

import os
import time
from datetime import datetime, timedelta

import jwt
import pytest
import requests


class TestSessionManagement:
    """Test session management vulnerability."""
    
    @pytest.fixture
    def supabase_config(self):
        """Get Supabase configuration."""
        url = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
        anon_key = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not anon_key:
            pytest.skip("Supabase configuration not available")
        
        return {"url": url, "anon_key": anon_key}
    
    def test_jwt_token_validation(self, supabase_config):
        """
        Test if JWT tokens are properly validated.
        """
        # Test with malformed JWT tokens
        malformed_tokens = [
            "invalid.jwt.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "Bearer ",
            "not-a-jwt-at-all",
            "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.",  # None algorithm
        ]
        
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        for token in malformed_tokens:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "apikey": supabase_config['anon_key']
            }
            
            payload = {
                "answerKeyId": "550e8400-e29b-41d4-a716-446655440000",
                "templateId": "550e8400-e29b-41d4-a716-446655440001",
                "items": [{"originalStoragePath": "test/file.jpg"}]
            }
            
            try:
                response = requests.post(
                    create_job_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                # Should reject invalid tokens
                if response.status_code == 200:
                    pytest.fail(
                        f"VULNERABILITY CONFIRMED: Invalid JWT token was accepted: {token[:50]}..."
                    )
                
                # Should return 401 Unauthorized
                if response.status_code != 401:
                    print(f"WARNING: Unexpected status code {response.status_code} for invalid token")
                
            except requests.exceptions.RequestException as e:
                pytest.skip(f"Network error during test: {e}")
    
    def test_expired_token_handling(self, supabase_config):
        """
        Test if expired JWT tokens are properly rejected.
        """
        # Create an expired JWT token (this is for testing purposes only)
        try:
            # Create a token that expired 1 hour ago
            expired_payload = {
                "sub": "test-user-id",
                "iat": int(time.time()) - 7200,  # Issued 2 hours ago
                "exp": int(time.time()) - 3600,  # Expired 1 hour ago
                "aud": "authenticated",
                "role": "authenticated"
            }
            
            # Note: In a real test, you'd need the actual JWT secret
            # This is just to demonstrate the test structure
            expired_token = "expired.jwt.token.placeholder"
            
            headers = {
                "Authorization": f"Bearer {expired_token}",
                "Content-Type": "application/json",
                "apikey": supabase_config['anon_key']
            }
            
            payload = {
                "answerKeyId": "550e8400-e29b-41d4-a716-446655440000",
                "templateId": "550e8400-e29b-41d4-a716-446655440001",
                "items": [{"originalStoragePath": "test/file.jpg"}]
            }
            
            create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
            
            response = requests.post(
                create_job_endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            # Should reject expired tokens
            if response.status_code == 200:
                print("WARNING: System might not be properly validating token expiration")
            
        except Exception as e:
            pytest.skip(f"Cannot create test expired token: {e}")
    
    def test_token_reuse_protection(self, supabase_config):
        """
        Test if the same token can be reused across different sessions/contexts.
        """
        # This test checks if tokens have proper binding to sessions
        
        headers = {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key']
        }
        
        # Test with different User-Agent headers (simulating different clients)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "TestClient/1.0",
            "curl/7.68.0"
        ]
        
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        payload = {
            "answerKeyId": "550e8400-e29b-41d4-a716-446655440000",
            "templateId": "550e8400-e29b-41d4-a716-446655440001",
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        responses = []
        
        for user_agent in user_agents:
            test_headers = headers.copy()
            test_headers["User-Agent"] = user_agent
            test_headers["x-idempotency-key"] = f"test-{user_agent.replace('/', '-')}"
            
            try:
                response = requests.post(
                    create_job_endpoint,
                    json=payload,
                    headers=test_headers,
                    timeout=10
                )
                responses.append(response.status_code)
                
            except requests.exceptions.RequestException:
                continue
        
        # Analyze if token works across different contexts
        success_count = sum(1 for r in responses if r in [200, 201])
        
        if success_count == len(user_agents):
            print("INFO: Token works across different User-Agent contexts")
        elif success_count == 0:
            print("INFO: Token rejected across all contexts (might be invalid)")
        else:
            print(f"INFO: Token worked in {success_count}/{len(user_agents)} contexts")
    
    def test_session_fixation_protection(self, supabase_config):
        """
        Test if the system is vulnerable to session fixation attacks.
        """
        # Test if providing a specific session ID in headers affects authentication
        
        headers = {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key'],
            "X-Session-ID": "attacker-controlled-session-id",
            "Cookie": "session_id=fixed_session_value"
        }
        
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        payload = {
            "answerKeyId": "550e8400-e29b-41d4-a716-446655440000",
            "templateId": "550e8400-e29b-41d4-a716-446655440001",
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        try:
            response = requests.post(
                create_job_endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            # Check if custom session headers are reflected in response
            response_headers = response.headers
            
            if "X-Session-ID" in response_headers:
                print("WARNING: Custom session ID header reflected in response")
            
            if "Set-Cookie" in response_headers:
                cookies = response_headers["Set-Cookie"]
                if "fixed_session_value" in cookies:
                    print("WARNING: Fixed session value accepted")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_concurrent_session_handling(self, supabase_config):
        """
        Test how the system handles concurrent requests with the same token.
        """
        import threading
        import time
        
        headers = {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key']
        }
        
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        results = []
        
        def make_request(request_id):
            payload = {
                "answerKeyId": "550e8400-e29b-41d4-a716-446655440000",
                "templateId": "550e8400-e29b-41d4-a716-446655440001",
                "items": [{"originalStoragePath": f"test/file{request_id}.jpg"}],
                "idempotencyKey": f"concurrent-test-{request_id}"
            }
            
            try:
                response = requests.post(
                    create_job_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                results.append({
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "timestamp": time.time()
                })
            except Exception as e:
                results.append({
                    "request_id": request_id,
                    "error": str(e),
                    "timestamp": time.time()
                })
        
        # Create 5 concurrent requests with the same token
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
        
        # Start all threads simultaneously
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=15)
        
        end_time = time.time()
        
        # Analyze results
        successful_requests = [r for r in results if r.get("status_code") in [200, 201]]
        failed_requests = [r for r in results if "error" in r or r.get("status_code", 0) >= 400]
        
        print(f"Concurrent session test: {len(successful_requests)} successful, {len(failed_requests)} failed")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        
        # Check if all requests succeeded (might indicate good concurrent handling)
        if len(successful_requests) == 5:
            print("INFO: All concurrent requests succeeded")
        elif len(successful_requests) == 0:
            print("WARNING: All concurrent requests failed - possible session locking issue")
    
    def test_token_information_disclosure(self, supabase_config):
        """
        Test if JWT tokens disclose sensitive information.
        """
        # Analyze the anonymous key JWT token structure
        anon_key = supabase_config['anon_key']
        
        try:
            # Decode JWT without verification to examine payload
            # Note: This is for security testing purposes only
            decoded = jwt.decode(anon_key, options={"verify_signature": False})
            
            # Check for sensitive information in the token
            sensitive_fields = [
                "email",
                "phone",
                "user_id",
                "admin",
                "secret",
                "password",
                "key",
                "private",
                "internal"
            ]
            
            disclosed_info = []
            for field in sensitive_fields:
                if field in str(decoded).lower():
                    disclosed_info.append(field)
            
            if disclosed_info:
                print(f"WARNING: JWT token may contain sensitive information: {disclosed_info}")
            
            # Check token expiration
            if "exp" in decoded:
                exp_timestamp = decoded["exp"]
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                now = datetime.now()
                
                if exp_datetime > now + timedelta(days=365):
                    print("WARNING: JWT token has very long expiration (>1 year)")
                elif exp_datetime < now:
                    print("INFO: JWT token is expired")
                else:
                    time_to_expire = exp_datetime - now
                    print(f"INFO: JWT token expires in {time_to_expire}")
            else:
                print("WARNING: JWT token has no expiration time")
            
            # Check for overly broad permissions
            if "role" in decoded:
                role = decoded["role"]
                if role in ["admin", "super_admin", "root"]:
                    print(f"WARNING: JWT token has high-privilege role: {role}")
            
        except jwt.InvalidTokenError:
            print("INFO: Cannot decode JWT token (might be encrypted or invalid format)")
        except Exception as e:
            print(f"INFO: JWT analysis failed: {e}")
    
    def test_refresh_token_security(self, supabase_config):
        """
        Test refresh token handling and security.
        """
        # This test would require actual user authentication to get refresh tokens
        # For now, we'll test the theoretical aspects
        
        # Test if refresh token endpoints exist and are properly secured
        auth_endpoints = [
            "/auth/v1/token",
            "/auth/v1/refresh",
            "/auth/v1/logout"
        ]
        
        for endpoint in auth_endpoints:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                # Test without authentication
                response = requests.post(url, json={}, timeout=5)
                
                if response.status_code == 200:
                    print(f"WARNING: {endpoint} accessible without authentication")
                elif response.status_code == 401:
                    print(f"INFO: {endpoint} properly requires authentication")
                
            except requests.exceptions.RequestException:
                continue
    
    def test_logout_effectiveness(self, supabase_config):
        """
        Test if logout properly invalidates tokens.
        """
        # This test would require a valid user session to test logout
        # For now, we'll test the logout endpoint accessibility
        
        logout_endpoint = f"{supabase_config['url']}/auth/v1/logout"
        
        headers = {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key']
        }
        
        try:
            response = requests.post(
                logout_endpoint,
                json={},
                headers=headers,
                timeout=10
            )
            
            print(f"Logout endpoint response: {response.status_code}")
            
            # Test if the same token still works after "logout"
            create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
            
            payload = {
                "answerKeyId": "550e8400-e29b-41d4-a716-446655440000",
                "templateId": "550e8400-e29b-41d4-a716-446655440001",
                "items": [{"originalStoragePath": "test/file.jpg"}]
            }
            
            post_logout_response = requests.post(
                create_job_endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if post_logout_response.status_code in [200, 201]:
                print("INFO: Token still works after logout attempt (expected for anon key)")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])