"""
Test for rate limiting vulnerability.

This test examines whether the application properly implements
rate limiting to prevent abuse of expensive operations.
"""

import asyncio
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import aiohttp
import pytest
import requests


class TestRateLimiting:
    """Test rate limiting vulnerability."""
    
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
    
    def test_create_job_rate_limiting(self, supabase_config, auth_headers):
        """
        Test if create_job endpoint has rate limiting.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Prepare multiple requests
        requests_to_send = 20  # Send 20 requests rapidly
        responses = []
        
        payload = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        # Send requests rapidly
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for i in range(requests_to_send):
                # Use different idempotency keys to avoid idempotency protection
                headers_with_key = auth_headers.copy()
                headers_with_key["x-idempotency-key"] = f"test-key-{i}-{int(time.time())}"
                
                future = executor.submit(
                    self._send_request,
                    create_job_endpoint,
                    payload,
                    headers_with_key
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures, timeout=30):
                try:
                    response = future.result()
                    responses.append(response.status_code)
                except Exception as e:
                    responses.append(f"Error: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze responses
        success_count = sum(1 for r in responses if r in [200, 201])
        rate_limited_count = sum(1 for r in responses if r == 429)  # Too Many Requests
        error_count = len(responses) - success_count - rate_limited_count
        
        print(f"Sent {requests_to_send} requests in {total_time:.2f} seconds")
        print(f"Successful: {success_count}, Rate limited: {rate_limited_count}, Errors: {error_count}")
        
        # VULNERABILITY: If all requests succeed, there's no rate limiting
        if success_count == requests_to_send and rate_limited_count == 0:
            pytest.fail(
                f"VULNERABILITY CONFIRMED: No rate limiting detected on create_job endpoint. "
                f"All {requests_to_send} requests succeeded in {total_time:.2f} seconds."
            )
        
        # If some requests were rate limited, that's good
        if rate_limited_count > 0:
            print(f"INFO: Rate limiting is working - {rate_limited_count} requests were rate limited")
    
    def test_upload_urls_rate_limiting(self, supabase_config, auth_headers):
        """
        Test if get_upload_urls endpoint has rate limiting.
        """
        upload_urls_endpoint = f"{supabase_config['url']}/functions/v1/get_upload_urls"
        
        payload = {
            "count": 10,  # Request 10 upload URLs each time
            "contentTypes": ["image/jpeg"] * 10
        }
        
        # Send multiple requests rapidly
        requests_to_send = 15
        responses = []
        
        start_time = time.time()
        
        for i in range(requests_to_send):
            try:
                response = requests.post(
                    upload_urls_endpoint,
                    json=payload,
                    headers=auth_headers,
                    timeout=5
                )
                responses.append(response.status_code)
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                responses.append(f"Error: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        success_count = sum(1 for r in responses if r in [200, 201])
        rate_limited_count = sum(1 for r in responses if r == 429)
        
        print(f"Upload URLs - Successful: {success_count}, Rate limited: {rate_limited_count}")
        
        # Check for rate limiting
        if success_count == requests_to_send and rate_limited_count == 0:
            print(f"WARNING: No rate limiting detected on get_upload_urls endpoint")
    
    def test_result_urls_rate_limiting(self, supabase_config, auth_headers):
        """
        Test if get_result_urls endpoint has rate limiting.
        """
        result_urls_endpoint = f"{supabase_config['url']}/functions/v1/get_result_urls"
        
        # Use a random job ID (will likely return 404, but tests rate limiting)
        payload = {
            "jobId": str(uuid.uuid4())
        }
        
        requests_to_send = 15
        responses = []
        
        for i in range(requests_to_send):
            try:
                response = requests.post(
                    result_urls_endpoint,
                    json=payload,
                    headers=auth_headers,
                    timeout=5
                )
                responses.append(response.status_code)
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                responses.append(f"Error: {e}")
        
        # Count different response types
        success_count = sum(1 for r in responses if r in [200, 201])
        not_found_count = sum(1 for r in responses if r == 404)
        rate_limited_count = sum(1 for r in responses if r == 429)
        
        print(f"Result URLs - Success: {success_count}, Not found: {not_found_count}, Rate limited: {rate_limited_count}")
        
        # Even 404s should be rate limited to prevent enumeration
        total_processed = success_count + not_found_count
        if total_processed == requests_to_send and rate_limited_count == 0:
            print(f"WARNING: No rate limiting on get_result_urls endpoint")
    
    def _send_request(self, url, payload, headers):
        """Helper method to send a single request."""
        return requests.post(url, json=payload, headers=headers, timeout=10)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_async(self, supabase_config, auth_headers):
        """
        Test concurrent requests using async HTTP client.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        payload = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        async def send_async_request(session, request_id):
            headers = auth_headers.copy()
            headers["x-idempotency-key"] = f"async-test-{request_id}-{int(time.time())}"
            
            try:
                async with session.post(
                    create_job_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status
            except Exception as e:
                return f"Error: {e}"
        
        # Send 25 concurrent requests
        concurrent_requests = 25
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                send_async_request(session, i)
                for i in range(concurrent_requests)
            ]
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
        
        # Analyze results
        success_count = sum(1 for r in responses if r in [200, 201])
        rate_limited_count = sum(1 for r in responses if r == 429)
        error_count = len(responses) - success_count - rate_limited_count
        
        total_time = end_time - start_time
        
        print(f"Async test - {concurrent_requests} requests in {total_time:.2f}s")
        print(f"Success: {success_count}, Rate limited: {rate_limited_count}, Errors: {error_count}")
        
        # Check if rate limiting is working
        if success_count == concurrent_requests and rate_limited_count == 0:
            print("WARNING: No rate limiting detected in concurrent async requests")
    
    def test_per_user_rate_limiting(self, supabase_config):
        """
        Test if rate limiting is applied per user or globally.
        """
        # This test would require multiple user tokens to be effective
        # For now, we'll test with different API keys if available
        
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        # Test with anonymous key (simulating different users)
        headers1 = {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key'],
            "User-Agent": "TestClient1"
        }
        
        headers2 = {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key'],
            "User-Agent": "TestClient2"
        }
        
        payload = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        # Send requests from "different users"
        responses1 = []
        responses2 = []
        
        for i in range(10):
            try:
                # User 1 request
                headers1["x-idempotency-key"] = f"user1-{i}-{int(time.time())}"
                r1 = requests.post(create_job_endpoint, json=payload, headers=headers1, timeout=5)
                responses1.append(r1.status_code)
                
                # User 2 request
                headers2["x-idempotency-key"] = f"user2-{i}-{int(time.time())}"
                r2 = requests.post(create_job_endpoint, json=payload, headers=headers2, timeout=5)
                responses2.append(r2.status_code)
                
                time.sleep(0.2)  # Small delay
                
            except requests.exceptions.RequestException:
                continue
        
        # Analyze if rate limiting affects both "users" equally
        user1_success = sum(1 for r in responses1 if r in [200, 201])
        user2_success = sum(1 for r in responses2 if r in [200, 201])
        
        print(f"User 1 successful requests: {user1_success}")
        print(f"User 2 successful requests: {user2_success}")
        
        # If both users are equally affected, rate limiting might be global
        # If one user is less affected, it might be per-user
        if abs(user1_success - user2_success) > 3:
            print("INFO: Rate limiting appears to be applied differently per user")
        else:
            print("INFO: Rate limiting appears to be global or similar per user")
    
    def test_burst_vs_sustained_rate_limiting(self, supabase_config, auth_headers):
        """
        Test if the system handles burst requests differently from sustained load.
        """
        create_job_endpoint = f"{supabase_config['url']}/functions/v1/create_job"
        
        payload = {
            "answerKeyId": str(uuid.uuid4()),
            "templateId": str(uuid.uuid4()),
            "items": [{"originalStoragePath": "test/file.jpg"}]
        }
        
        # Test 1: Burst requests (10 requests in quick succession)
        print("Testing burst requests...")
        burst_responses = []
        
        for i in range(10):
            headers = auth_headers.copy()
            headers["x-idempotency-key"] = f"burst-{i}-{int(time.time())}"
            
            try:
                response = requests.post(
                    create_job_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=5
                )
                burst_responses.append(response.status_code)
            except requests.exceptions.RequestException:
                burst_responses.append("Error")
        
        burst_success = sum(1 for r in burst_responses if r in [200, 201])
        burst_rate_limited = sum(1 for r in burst_responses if r == 429)
        
        # Test 2: Sustained requests (10 requests with delays)
        print("Testing sustained requests...")
        sustained_responses = []
        
        for i in range(10):
            headers = auth_headers.copy()
            headers["x-idempotency-key"] = f"sustained-{i}-{int(time.time())}"
            
            try:
                response = requests.post(
                    create_job_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=5
                )
                sustained_responses.append(response.status_code)
                time.sleep(1)  # 1 second delay between requests
            except requests.exceptions.RequestException:
                sustained_responses.append("Error")
        
        sustained_success = sum(1 for r in sustained_responses if r in [200, 201])
        sustained_rate_limited = sum(1 for r in sustained_responses if r == 429)
        
        print(f"Burst: {burst_success} success, {burst_rate_limited} rate limited")
        print(f"Sustained: {sustained_success} success, {sustained_rate_limited} rate limited")
        
        # Analyze the difference
        if burst_rate_limited > sustained_rate_limited:
            print("INFO: System properly handles burst vs sustained load")
        elif burst_success == 10 and sustained_success == 10:
            print("WARNING: No rate limiting detected for either burst or sustained requests")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])