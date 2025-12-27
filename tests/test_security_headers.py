"""
Test for missing security headers vulnerability.

This test examines HTTP response headers to identify missing
security headers that could prevent various attacks.
"""

import os

import pytest
import requests


class TestSecurityHeaders:
    """Test missing security headers vulnerability."""
    
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
    
    def test_content_security_policy_header(self, supabase_config, auth_headers):
        """
        Test if Content Security Policy (CSP) header is present and properly configured.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls",
            "/functions/v1/get_result_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                csp_header = response.headers.get("Content-Security-Policy")
                
                if not csp_header:
                    print(f"WARNING: Missing Content-Security-Policy header on {endpoint}")
                else:
                    # Analyze CSP configuration
                    self._analyze_csp_header(csp_header, endpoint)
                
            except requests.exceptions.RequestException:
                continue
    
    def _analyze_csp_header(self, csp_header, endpoint):
        """Analyze CSP header for security issues."""
        csp_lower = csp_header.lower()
        
        # Check for unsafe configurations
        unsafe_patterns = [
            "'unsafe-inline'",
            "'unsafe-eval'",
            "data:",
            "*",
            "http:",
        ]
        
        found_unsafe = []
        for pattern in unsafe_patterns:
            if pattern in csp_lower:
                found_unsafe.append(pattern)
        
        if found_unsafe:
            print(f"WARNING: Unsafe CSP directives on {endpoint}: {found_unsafe}")
        
        # Check for missing important directives
        important_directives = [
            "default-src",
            "script-src",
            "object-src",
            "frame-ancestors"
        ]
        
        missing_directives = []
        for directive in important_directives:
            if directive not in csp_lower:
                missing_directives.append(directive)
        
        if missing_directives:
            print(f"INFO: Missing CSP directives on {endpoint}: {missing_directives}")
    
    def test_x_frame_options_header(self, supabase_config, auth_headers):
        """
        Test if X-Frame-Options header is present to prevent clickjacking.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                x_frame_options = response.headers.get("X-Frame-Options")
                
                if not x_frame_options:
                    print(f"WARNING: Missing X-Frame-Options header on {endpoint}")
                else:
                    # Check for proper values
                    valid_values = ["DENY", "SAMEORIGIN"]
                    if x_frame_options.upper() not in valid_values:
                        print(f"WARNING: Weak X-Frame-Options value on {endpoint}: {x_frame_options}")
                    else:
                        print(f"INFO: Good X-Frame-Options on {endpoint}: {x_frame_options}")
                
            except requests.exceptions.RequestException:
                continue
    
    def test_x_content_type_options_header(self, supabase_config, auth_headers):
        """
        Test if X-Content-Type-Options header is present to prevent MIME sniffing.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                x_content_type_options = response.headers.get("X-Content-Type-Options")
                
                if not x_content_type_options:
                    print(f"WARNING: Missing X-Content-Type-Options header on {endpoint}")
                elif x_content_type_options.lower() != "nosniff":
                    print(f"WARNING: Incorrect X-Content-Type-Options value on {endpoint}: {x_content_type_options}")
                else:
                    print(f"INFO: Good X-Content-Type-Options on {endpoint}")
                
            except requests.exceptions.RequestException:
                continue
    
    def test_strict_transport_security_header(self, supabase_config, auth_headers):
        """
        Test if Strict-Transport-Security (HSTS) header is present.
        """
        # Only test HSTS on HTTPS endpoints
        if not supabase_config['url'].startswith('https://'):
            pytest.skip("HSTS only applicable to HTTPS endpoints")
        
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                hsts_header = response.headers.get("Strict-Transport-Security")
                
                if not hsts_header:
                    print(f"WARNING: Missing Strict-Transport-Security header on {endpoint}")
                else:
                    # Analyze HSTS configuration
                    self._analyze_hsts_header(hsts_header, endpoint)
                
            except requests.exceptions.RequestException:
                continue
    
    def _analyze_hsts_header(self, hsts_header, endpoint):
        """Analyze HSTS header configuration."""
        hsts_lower = hsts_header.lower()
        
        # Check max-age value
        if "max-age=" in hsts_lower:
            try:
                max_age_part = [part for part in hsts_lower.split(';') if 'max-age=' in part][0]
                max_age_value = int(max_age_part.split('=')[1].strip())
                
                # Recommend at least 1 year (31536000 seconds)
                if max_age_value < 31536000:
                    print(f"WARNING: HSTS max-age too short on {endpoint}: {max_age_value} seconds")
                else:
                    print(f"INFO: Good HSTS max-age on {endpoint}: {max_age_value} seconds")
                    
            except (ValueError, IndexError):
                print(f"WARNING: Invalid HSTS max-age format on {endpoint}")
        else:
            print(f"WARNING: HSTS header missing max-age on {endpoint}")
        
        # Check for includeSubDomains
        if "includesubdomains" not in hsts_lower:
            print(f"INFO: HSTS missing includeSubDomains on {endpoint} (may be intentional)")
        
        # Check for preload
        if "preload" not in hsts_lower:
            print(f"INFO: HSTS missing preload on {endpoint} (may be intentional)")
    
    def test_referrer_policy_header(self, supabase_config, auth_headers):
        """
        Test if Referrer-Policy header is present and properly configured.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                referrer_policy = response.headers.get("Referrer-Policy")
                
                if not referrer_policy:
                    print(f"WARNING: Missing Referrer-Policy header on {endpoint}")
                else:
                    # Check for secure values
                    secure_values = [
                        "no-referrer",
                        "no-referrer-when-downgrade",
                        "strict-origin",
                        "strict-origin-when-cross-origin"
                    ]
                    
                    if referrer_policy.lower() not in [v.lower() for v in secure_values]:
                        print(f"WARNING: Potentially unsafe Referrer-Policy on {endpoint}: {referrer_policy}")
                    else:
                        print(f"INFO: Good Referrer-Policy on {endpoint}: {referrer_policy}")
                
            except requests.exceptions.RequestException:
                continue
    
    def test_permissions_policy_header(self, supabase_config, auth_headers):
        """
        Test if Permissions-Policy header is present to control browser features.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                permissions_policy = response.headers.get("Permissions-Policy")
                
                if not permissions_policy:
                    print(f"INFO: Missing Permissions-Policy header on {endpoint} (optional but recommended)")
                else:
                    print(f"INFO: Permissions-Policy present on {endpoint}: {permissions_policy[:100]}...")
                
            except requests.exceptions.RequestException:
                continue
    
    def test_server_information_disclosure(self, supabase_config, auth_headers):
        """
        Test if server headers disclose sensitive information.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                # Check for information disclosure headers
                disclosure_headers = [
                    "Server",
                    "X-Powered-By",
                    "X-AspNet-Version",
                    "X-AspNetMvc-Version",
                    "X-Version",
                    "X-Runtime"
                ]
                
                disclosed_info = []
                for header in disclosure_headers:
                    if header in response.headers:
                        disclosed_info.append(f"{header}: {response.headers[header]}")
                
                if disclosed_info:
                    print(f"WARNING: Information disclosure headers on {endpoint}: {disclosed_info}")
                
            except requests.exceptions.RequestException:
                continue
    
    def test_cors_security_configuration(self, supabase_config):
        """
        Test CORS configuration for security issues.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                # Send OPTIONS request to check CORS
                response = requests.options(url, timeout=10)
                
                # Check Access-Control-Allow-Origin
                allow_origin = response.headers.get("Access-Control-Allow-Origin")
                if allow_origin == "*":
                    print(f"WARNING: CORS allows all origins (*) on {endpoint}")
                elif allow_origin:
                    print(f"INFO: CORS origin restriction on {endpoint}: {allow_origin}")
                
                # Check Access-Control-Allow-Credentials
                allow_credentials = response.headers.get("Access-Control-Allow-Credentials")
                if allow_credentials == "true" and allow_origin == "*":
                    print(f"CRITICAL: CORS allows credentials with wildcard origin on {endpoint}")
                
                # Check Access-Control-Allow-Methods
                allow_methods = response.headers.get("Access-Control-Allow-Methods")
                if allow_methods:
                    if "DELETE" in allow_methods.upper() or "PUT" in allow_methods.upper():
                        print(f"INFO: CORS allows potentially dangerous methods on {endpoint}: {allow_methods}")
                
                # Check Access-Control-Max-Age
                max_age = response.headers.get("Access-Control-Max-Age")
                if max_age:
                    try:
                        max_age_seconds = int(max_age)
                        if max_age_seconds > 86400:  # More than 24 hours
                            print(f"WARNING: CORS preflight cache too long on {endpoint}: {max_age_seconds} seconds")
                    except ValueError:
                        pass
                
            except requests.exceptions.RequestException:
                continue
    
    def test_cache_control_headers(self, supabase_config, auth_headers):
        """
        Test if cache control headers are properly configured.
        """
        endpoints_to_test = [
            "/functions/v1/create_job",
            "/functions/v1/get_upload_urls"
        ]
        
        for endpoint in endpoints_to_test:
            url = f"{supabase_config['url']}{endpoint}"
            
            try:
                response = requests.post(
                    url,
                    json={"test": "data"},
                    headers=auth_headers,
                    timeout=10
                )
                
                # Check Cache-Control header
                cache_control = response.headers.get("Cache-Control")
                if not cache_control:
                    print(f"INFO: Missing Cache-Control header on {endpoint}")
                else:
                    # Check for sensitive data caching
                    if "no-cache" not in cache_control.lower() and "no-store" not in cache_control.lower():
                        print(f"WARNING: Response may be cached on {endpoint}: {cache_control}")
                    else:
                        print(f"INFO: Good cache control on {endpoint}: {cache_control}")
                
                # Check Pragma header (legacy)
                pragma = response.headers.get("Pragma")
                if pragma and pragma.lower() != "no-cache":
                    print(f"INFO: Pragma header on {endpoint}: {pragma}")
                
            except requests.exceptions.RequestException:
                continue
    
    def test_comprehensive_security_headers_report(self, supabase_config, auth_headers):
        """
        Generate a comprehensive security headers report.
        """
        endpoint = "/functions/v1/create_job"
        url = f"{supabase_config['url']}{endpoint}"
        
        try:
            response = requests.post(
                url,
                json={"test": "data"},
                headers=auth_headers,
                timeout=10
            )
            
            # Security headers to check
            security_headers = {
                "Content-Security-Policy": "Prevents XSS and data injection attacks",
                "X-Frame-Options": "Prevents clickjacking attacks",
                "X-Content-Type-Options": "Prevents MIME sniffing attacks",
                "Strict-Transport-Security": "Enforces HTTPS connections",
                "Referrer-Policy": "Controls referrer information leakage",
                "Permissions-Policy": "Controls browser feature access",
                "X-XSS-Protection": "Legacy XSS protection (deprecated but still useful)",
            }
            
            print(f"\n=== Security Headers Report for {endpoint} ===")
            
            present_headers = []
            missing_headers = []
            
            for header, description in security_headers.items():
                if header in response.headers:
                    present_headers.append(header)
                    print(f"✓ {header}: {response.headers[header][:50]}...")
                else:
                    missing_headers.append(header)
                    print(f"✗ {header}: MISSING - {description}")
            
            print(f"\nSummary: {len(present_headers)}/{len(security_headers)} security headers present")
            
            if len(missing_headers) > len(present_headers):
                print("WARNING: More security headers are missing than present")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during comprehensive test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])