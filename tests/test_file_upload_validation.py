"""
Test for file upload validation vulnerability.

This test attempts to upload malicious files with valid MIME types
to test if the server properly validates file content.
"""

import io
import os

import pytest
import requests
from PIL import Image


class TestFileUploadValidation:
    """Test file upload validation vulnerability."""
    
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
        # This would normally require a valid user session
        # For testing, we'll simulate the headers
        return {
            "Authorization": f"Bearer {supabase_config['anon_key']}",
            "Content-Type": "application/json",
            "apikey": supabase_config['anon_key']
        }
    
    def create_malicious_file_with_image_header(self):
        """
        Create a malicious file that starts with valid image bytes
        but contains executable content.
        """
        # Start with valid JPEG header
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        
        # Add malicious content (simulated script)
        malicious_content = b'<script>alert("XSS")</script>' * 100
        
        return jpeg_header + malicious_content
    
    def create_executable_with_image_extension(self):
        """
        Create an executable file with image-like content.
        """
        # Simulate a shell script disguised as image
        content = b"""#!/bin/bash
# This looks like image metadata but is actually executable
echo "Malicious code executed"
rm -rf /tmp/test_file
"""
        return content
    
    def create_polyglot_file(self):
        """
        Create a polyglot file that's both a valid image and contains script.
        """
        # Create a small valid PNG
        img = Image.new('RGB', (1, 1), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()
        
        # Append script content
        script_content = b'\n<script>alert("polyglot")</script>'
        
        return img_bytes + script_content
    
    def test_malicious_file_with_valid_header(self, supabase_config, auth_headers):
        """
        Test uploading a malicious file with valid image header.
        """
        # Get upload URL
        upload_url_endpoint = f"{supabase_config['url']}/functions/v1/get_upload_urls"
        
        payload = {
            "count": 1,
            "contentTypes": ["image/jpeg"]
        }
        
        try:
            response = requests.post(
                upload_url_endpoint,
                json=payload,
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code != 200:
                pytest.skip(f"Cannot get upload URL: {response.status_code}")
            
            upload_data = response.json()
            
            if "urls" not in upload_data or not upload_data["urls"]:
                pytest.skip("No upload URLs returned")
            
            upload_url = upload_data["urls"][0]["signedUrl"]
            
            # Create malicious file
            malicious_file = self.create_malicious_file_with_image_header()
            
            # Attempt upload
            upload_response = requests.put(
                upload_url,
                data=malicious_file,
                headers={"Content-Type": "image/jpeg"},
                timeout=10
            )
            
            # VULNERABILITY: If upload succeeds, the server doesn't validate file content
            if upload_response.status_code == 200:
                pytest.fail(
                    "VULNERABILITY CONFIRMED: Malicious file with valid header was accepted. "
                    "Server should validate actual file content, not just headers."
                )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_executable_file_upload(self, supabase_config, auth_headers):
        """
        Test uploading an executable file with image MIME type.
        """
        upload_url_endpoint = f"{supabase_config['url']}/functions/v1/get_upload_urls"
        
        payload = {
            "count": 1,
            "contentTypes": ["image/png"]
        }
        
        try:
            response = requests.post(
                upload_url_endpoint,
                json=payload,
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code != 200:
                pytest.skip(f"Cannot get upload URL: {response.status_code}")
            
            upload_data = response.json()
            upload_url = upload_data["urls"][0]["signedUrl"]
            
            # Create executable file
            executable_file = self.create_executable_with_image_extension()
            
            # Attempt upload with image MIME type
            upload_response = requests.put(
                upload_url,
                data=executable_file,
                headers={"Content-Type": "image/png"},
                timeout=10
            )
            
            # VULNERABILITY: If upload succeeds, server accepts any content with valid MIME type
            if upload_response.status_code == 200:
                pytest.fail(
                    "VULNERABILITY CONFIRMED: Executable file was accepted with image MIME type. "
                    "Server should validate file magic bytes."
                )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_polyglot_file_upload(self, supabase_config, auth_headers):
        """
        Test uploading a polyglot file (valid image + script).
        """
        upload_url_endpoint = f"{supabase_config['url']}/functions/v1/get_upload_urls"
        
        payload = {
            "count": 1,
            "contentTypes": ["image/png"]
        }
        
        try:
            response = requests.post(
                upload_url_endpoint,
                json=payload,
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code != 200:
                pytest.skip(f"Cannot get upload URL: {response.status_code}")
            
            upload_data = response.json()
            upload_url = upload_data["urls"][0]["signedUrl"]
            
            # Create polyglot file
            polyglot_file = self.create_polyglot_file()
            
            # Attempt upload
            upload_response = requests.put(
                upload_url,
                data=polyglot_file,
                headers={"Content-Type": "image/png"},
                timeout=10
            )
            
            # This might be accepted since it's a valid image, but we should warn about it
            if upload_response.status_code == 200:
                print(
                    "WARNING: Polyglot file (image + script) was accepted. "
                    "Consider implementing content scanning for embedded scripts."
                )
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")
    
    def test_oversized_file_upload(self, supabase_config, auth_headers):
        """
        Test uploading a file that exceeds size limits.
        """
        upload_url_endpoint = f"{supabase_config['url']}/functions/v1/get_upload_urls"
        
        payload = {
            "count": 1,
            "contentTypes": ["image/jpeg"]
        }
        
        try:
            response = requests.post(
                upload_url_endpoint,
                json=payload,
                headers=auth_headers,
                timeout=10
            )
            
            if response.status_code != 200:
                pytest.skip(f"Cannot get upload URL: {response.status_code}")
            
            upload_data = response.json()
            upload_url = upload_data["urls"][0]["signedUrl"]
            
            # Create oversized file (25MB, limit is 20MB according to storage config)
            oversized_file = b'A' * (25 * 1024 * 1024)
            
            # Attempt upload
            upload_response = requests.put(
                upload_url,
                data=oversized_file,
                headers={"Content-Type": "image/jpeg"},
                timeout=30
            )
            
            # Should be rejected due to size limit
            if upload_response.status_code == 200:
                pytest.fail(
                    "VULNERABILITY CONFIRMED: Oversized file was accepted. "
                    "File size limits are not properly enforced."
                )
            
            # Expect 413 (Payload Too Large) or similar error
            assert upload_response.status_code in [413, 400, 403], \
                f"Expected size limit error, got {upload_response.status_code}"
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Network error during test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])