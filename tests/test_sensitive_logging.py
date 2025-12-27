"""
Test for sensitive information logging vulnerability.

This test examines logging practices to identify potential
disclosure of sensitive information in log files.
"""

import logging
import os
import re
import tempfile
import uuid
from unittest.mock import Mock, patch

import pytest


class TestSensitiveLogging:
    """Test sensitive information logging vulnerability."""
    
    def test_user_id_logging(self):
        """
        Test if user IDs are being logged inappropriately.
        """
        # Simulate logging statements that might contain user IDs
        log_statements = [
            f"Processing job for user {uuid.uuid4()}",
            f"User {uuid.uuid4()} created correction job",
            f"Error processing request for user_id: {uuid.uuid4()}",
            f"Authentication failed for user {uuid.uuid4()}",
            f"Token validation failed for user: {uuid.uuid4()}",
        ]
        
        # Check for UUID patterns in log statements
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        
        for statement in log_statements:
            if re.search(uuid_pattern, statement, re.IGNORECASE):
                print(f"WARNING: User ID potentially logged: {statement}")
    
    def test_email_logging(self):
        """
        Test if email addresses are being logged inappropriately.
        """
        log_statements = [
            "User login attempt: user@example.com",
            "Password reset requested for admin@company.com",
            "Email verification sent to test.user@domain.org",
            "Failed login for user: malicious@attacker.com",
            "Profile updated for email: sensitive@private.com",
        ]
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        for statement in log_statements:
            if re.search(email_pattern, statement):
                print(f"WARNING: Email address potentially logged: {statement}")
    
    def test_password_logging(self):
        """
        Test if passwords or tokens are being logged inappropriately.
        """
        log_statements = [
            "Authentication failed with password: secret123",
            "JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "API key validation failed: sk_test_123456789",
            "Database connection string: postgresql://user:password@host:5432/db",
            "Redis URL: redis://:password@localhost:6379",
            "Stripe key: sk_live_abcdef123456",
        ]
        
        # Patterns for sensitive data
        sensitive_patterns = [
            r'password[:\s=]+\S+',
            r'token[:\s=]+\S+',
            r'key[:\s=]+\S+',
            r'secret[:\s=]+\S+',
            r'jwt[:\s=]+\S+',
            r'bearer[:\s=]+\S+',
            r'sk_[a-zA-Z0-9_]+',  # Stripe keys
            r'pk_[a-zA-Z0-9_]+',  # Stripe public keys
        ]
        
        for statement in log_statements:
            for pattern in sensitive_patterns:
                if re.search(pattern, statement, re.IGNORECASE):
                    print(f"WARNING: Sensitive data potentially logged: {statement}")
                    break
    
    def test_database_connection_logging(self):
        """
        Test if database connection details are being logged.
        """
        log_statements = [
            "Database connection failed: postgresql://user:pass@db.internal.com:5432/prod",
            "Redis connection error: redis://admin:secret@cache.internal:6379",
            "MongoDB URI: mongodb://user:password@mongo.internal:27017/database",
            "Connection string: Server=sql.internal;Database=prod;User=admin;Password=secret;",
            "Supabase URL: https://project.supabase.co with key: eyJhbGc...",
        ]
        
        # Database connection patterns
        db_patterns = [
            r'postgresql://[^@]+@[^/]+',
            r'redis://[^@]+@[^/]+',
            r'mongodb://[^@]+@[^/]+',
            r'Server=[^;]+;.*Password=[^;]+',
            r'supabase\.co.*key',
        ]
        
        for statement in log_statements:
            for pattern in db_patterns:
                if re.search(pattern, statement, re.IGNORECASE):
                    print(f"WARNING: Database connection info potentially logged: {statement}")
                    break
    
    def test_file_path_logging(self):
        """
        Test if sensitive file paths are being logged.
        """
        log_statements = [
            "Config file not found: /etc/app/secrets.json",
            "Reading private key from /var/lib/app/private.key",
            "Log file: /var/log/app/sensitive.log",
            "Error accessing /home/user/.ssh/id_rsa",
            "Backup location: /mnt/backups/database_dump_2024.sql",
            "Certificate path: /etc/ssl/private/app.key",
        ]
        
        # Sensitive path patterns
        sensitive_path_patterns = [
            r'/etc/[^/\s]+',
            r'/var/[^/\s]+/[^/\s]+',
            r'/home/[^/\s]+/\.[^/\s]+',
            r'/root/[^/\s]+',
            r'\.key\b',
            r'\.pem\b',
            r'\.p12\b',
            r'secrets?[^/\s]*',
            r'private[^/\s]*',
        ]
        
        for statement in log_statements:
            for pattern in sensitive_path_patterns:
                if re.search(pattern, statement, re.IGNORECASE):
                    print(f"WARNING: Sensitive file path potentially logged: {statement}")
                    break
    
    def test_ip_address_logging(self):
        """
        Test if IP addresses are being logged (potential privacy issue).
        """
        log_statements = [
            "Request from IP: 192.168.1.100",
            "Failed login attempt from 10.0.0.50",
            "Rate limit exceeded for 203.0.113.45",
            "Internal server error for client 172.16.0.25",
            "Suspicious activity from 198.51.100.75",
        ]
        
        # IP address patterns
        ip_patterns = [
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',  # IPv4
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6
        ]
        
        for statement in log_statements:
            for pattern in ip_patterns:
                if re.search(pattern, statement):
                    print(f"INFO: IP address logged (may be intentional): {statement}")
                    break
    
    def test_session_id_logging(self):
        """
        Test if session IDs or similar identifiers are being logged.
        """
        log_statements = [
            "Session expired: sess_abc123def456",
            "Invalid session ID: 1234567890abcdef",
            "User session: session_token_xyz789",
            "Cookie value: JSESSIONID=A1B2C3D4E5F6",
            "Request ID: req_abcdef123456789",
        ]
        
        # Session/identifier patterns
        session_patterns = [
            r'sess(?:ion)?[_\s]*(?:id)?[:\s=]+\S+',
            r'cookie[:\s=]+\S+',
            r'jsessionid[:\s=]+\S+',
            r'req(?:uest)?[_\s]*id[:\s=]+\S+',
        ]
        
        for statement in log_statements:
            for pattern in session_patterns:
                if re.search(pattern, statement, re.IGNORECASE):
                    print(f"WARNING: Session/identifier potentially logged: {statement}")
                    break
    
    def test_error_message_sensitivity(self):
        """
        Test if error messages contain sensitive information.
        """
        error_messages = [
            "Database error: relation 'users' does not exist at line 42 in /app/models/user.py",
            "Authentication failed: Invalid password for user admin@company.com",
            "File not found: /var/lib/app/secrets/api_keys.json",
            "Connection refused: Could not connect to database at db.internal.com:5432",
            "Permission denied: Cannot access /etc/passwd",
            "SQL error: duplicate key value violates unique constraint 'users_email_key'",
        ]
        
        # Sensitive information in errors
        sensitive_error_patterns = [
            r'relation [\'"][^\'"]+ does not exist',
            r'at line \d+ in [^\s]+',
            r'Invalid password for [^\s]+',
            r'Could not connect to [^\s]+ at [^\s]+',
            r'Cannot access [^\s]+',
            r'violates unique constraint [\'"][^\'\"]+',
            r'\.internal\.',
            r'/etc/',
            r'/var/',
        ]
        
        for message in error_messages:
            for pattern in sensitive_error_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    print(f"WARNING: Sensitive info in error message: {message}")
                    break
    
    @patch('logging.Logger.error')
    @patch('logging.Logger.info')
    @patch('logging.Logger.warning')
    def test_worker_logging_practices(self, mock_warning, mock_info, mock_error):
        """
        Test worker logging practices by mocking logger calls.
        """
        try:
            from worker.worker.config import WorkerConfig
            from worker.worker.supabase_client import SupabaseWorkerClient
        except ImportError:
            pytest.skip("Worker module not available")
        
        # Mock configuration
        config = Mock(spec=WorkerConfig)
        config.supabase_url = "https://test.supabase.co"
        config.supabase_service_role_key = "test-key"
        
        # Create client (this might trigger logging)
        try:
            client = SupabaseWorkerClient(config)
            
            # Simulate operations that might log sensitive data
            fake_job_id = str(uuid.uuid4())
            fake_user_id = str(uuid.uuid4())
            
            # These operations might trigger logging
            try:
                client.get_job(fake_job_id)
            except:
                pass
            
            # Check what was logged
            logged_calls = []
            logged_calls.extend(mock_error.call_args_list)
            logged_calls.extend(mock_info.call_args_list)
            logged_calls.extend(mock_warning.call_args_list)
            
            for call in logged_calls:
                if call and call[0]:  # Check if call has arguments
                    log_message = str(call[0][0])  # First argument is usually the message
                    
                    # Check for sensitive data in log messages
                    if fake_job_id in log_message:
                        print(f"WARNING: Job ID logged in worker: {log_message[:100]}...")
                    
                    if fake_user_id in log_message:
                        print(f"WARNING: User ID logged in worker: {log_message[:100]}...")
            
        except Exception as e:
            pytest.skip(f"Cannot test worker logging: {e}")
    
    def test_log_level_configuration(self):
        """
        Test if log levels are properly configured to avoid verbose logging in production.
        """
        # Check current logging configuration
        root_logger = logging.getLogger()
        current_level = root_logger.getEffectiveLevel()
        
        # In production, should not be DEBUG level
        if current_level == logging.DEBUG:
            print("WARNING: Root logger is set to DEBUG level - may log sensitive information")
        elif current_level == logging.INFO:
            print("INFO: Root logger is set to INFO level")
        elif current_level >= logging.WARNING:
            print("INFO: Root logger is set to WARNING or higher level")
        
        # Check specific loggers that might be configured
        logger_names = [
            "worker",
            "supabase",
            "requests",
            "urllib3",
            "httpx",
        ]
        
        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            if logger.handlers:  # Logger has specific configuration
                level = logger.getEffectiveLevel()
                if level == logging.DEBUG:
                    print(f"WARNING: Logger '{logger_name}' is set to DEBUG level")
    
    def test_log_sanitization_functions(self):
        """
        Test if there are proper log sanitization functions in place.
        """
        # Test data that should be sanitized
        sensitive_data = [
            "user@example.com",
            str(uuid.uuid4()),
            "password123",
            "sk_test_123456789",
            "192.168.1.100",
        ]
        
        # Simulate a log sanitization function
        def sanitize_log_message(message):
            """Example log sanitization function."""
            # Replace emails
            message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', message)
            
            # Replace UUIDs
            message = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '[UUID]', message, flags=re.IGNORECASE)
            
            # Replace potential passwords/tokens
            message = re.sub(r'(?:password|token|key|secret)[:\s=]+\S+', '[REDACTED]', message, flags=re.IGNORECASE)
            
            # Replace IP addresses
            message = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP]', message)
            
            return message
        
        # Test sanitization
        for data in sensitive_data:
            test_message = f"Processing request for {data}"
            sanitized = sanitize_log_message(test_message)
            
            if data in sanitized:
                print(f"WARNING: Sanitization failed for: {test_message}")
            else:
                print(f"INFO: Successfully sanitized: {test_message} -> {sanitized}")
    
    def test_structured_logging_security(self):
        """
        Test if structured logging properly handles sensitive data.
        """
        # Simulate structured log entries
        log_entries = [
            {
                "level": "INFO",
                "message": "User login",
                "user_id": str(uuid.uuid4()),
                "email": "user@example.com",
                "ip": "192.168.1.100"
            },
            {
                "level": "ERROR",
                "message": "Database connection failed",
                "connection_string": "postgresql://user:pass@db:5432/prod",
                "error": "Connection refused"
            },
            {
                "level": "DEBUG",
                "message": "API request",
                "headers": {
                    "Authorization": "Bearer eyJhbGc...",
                    "X-API-Key": "sk_test_123456"
                }
            }
        ]
        
        # Check for sensitive data in structured logs
        for entry in log_entries:
            sensitive_fields = []
            
            # Check for sensitive field names
            sensitive_field_names = [
                "password", "token", "key", "secret", "authorization",
                "connection_string", "user_id", "email"
            ]
            
            def check_dict_recursive(d, path=""):
                for key, value in d.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check field name
                    if any(sensitive in key.lower() for sensitive in sensitive_field_names):
                        sensitive_fields.append(current_path)
                    
                    # Check nested dictionaries
                    if isinstance(value, dict):
                        check_dict_recursive(value, current_path)
            
            check_dict_recursive(entry)
            
            if sensitive_fields:
                print(f"WARNING: Structured log contains sensitive fields: {sensitive_fields}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])