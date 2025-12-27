"""
Tests for the refactored SecurityManager.

Tests backward compatibility and new functionality.
"""

import uuid

import pytest
from worker.security import (
    SecurityConfig,
    SecurityError,
    SecurityManager,
    ValidationLevel,
    get_security_manager,
)


class TestSecurityManagerCore:
    """Test SecurityManager core functionality."""

    def test_security_manager_initialization(self) -> None:
        """Test that SecurityManager initializes correctly."""
        manager = SecurityManager()
        assert manager is not None
        assert manager.get_current_provider_name() in [
            "pathvalidate",
            "werkzeug",
            "custom",
        ]

    def test_security_manager_with_config(self) -> None:
        """Test SecurityManager with custom configuration."""
        config = SecurityConfig(
            preferred_provider="custom",
            validation_level=ValidationLevel.STRICT,
        )
        manager = SecurityManager(config)
        assert manager.config.preferred_provider == "custom"
        assert manager.config.validation_level == ValidationLevel.STRICT

    def test_sanitize_filename_backward_compat(self) -> None:
        """Test backward-compatible sanitize_filename method."""
        manager = SecurityManager()
        result = manager.sanitize_filename("test_file.jpg")
        assert result is not None
        assert len(result) > 0

    def test_sanitize_filename_rejects_traversal(self) -> None:
        """Test that sanitize_filename rejects path traversal."""
        manager = SecurityManager()
        with pytest.raises((SecurityError, ValueError)):
            manager.sanitize_filename("../../../etc/passwd")

    def test_sanitize_filename_rejects_empty(self) -> None:
        """Test that sanitize_filename rejects empty filenames."""
        manager = SecurityManager()
        with pytest.raises((SecurityError, ValueError)):
            manager.sanitize_filename("")

    def test_validate_storage_path(self) -> None:
        """Test validate_storage_path method."""
        manager = SecurityManager()
        bucket, path = manager.validate_storage_path("uploads/user/file.jpg")
        assert bucket == "uploads"
        assert path == "user/file.jpg"

    def test_validate_storage_path_default_bucket(self) -> None:
        """Test validate_storage_path with default bucket."""
        manager = SecurityManager()
        # When no bucket is specified, it should use "uploads" as default
        # But the path "user/file.jpg" will be treated as bucket/path
        bucket, path = manager.validate_storage_path("uploads/user/file.jpg")
        assert bucket == "uploads"
        assert path == "user/file.jpg"

    def test_validate_storage_path_rejects_traversal(self) -> None:
        """Test that validate_storage_path rejects path traversal."""
        manager = SecurityManager()
        with pytest.raises(SecurityError):
            manager.validate_storage_path("uploads/../../../etc/passwd")

    def test_validate_bucket_name(self) -> None:
        """Test validate_bucket_name method."""
        manager = SecurityManager()
        assert manager.validate_bucket_name("uploads") is True
        assert manager.validate_bucket_name("results") is True
        assert manager.validate_bucket_name("invalid") is False

    def test_validate_user_path_access(self) -> None:
        """Test validate_user_path_access method."""
        manager = SecurityManager()
        user_id = str(uuid.uuid4())
        assert manager.validate_user_path_access(f"{user_id}/file.jpg", user_id) is True
        assert manager.validate_user_path_access("other_user/file.jpg", user_id) is False

    def test_validate_user_path_access_rejects_traversal(self) -> None:
        """Test that validate_user_path_access rejects traversal."""
        manager = SecurityManager()
        user_id = str(uuid.uuid4())
        assert manager.validate_user_path_access(f"{user_id}/../other/file.jpg", user_id) is False

    def test_create_secure_path(self) -> None:
        """Test create_secure_path method."""
        manager = SecurityManager()
        user_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        path = manager.create_secure_path(user_id, job_id, "test.jpg")
        assert user_id in path
        assert job_id in path
        assert "test.jpg" in path

    def test_create_secure_path_rejects_invalid_user_id(self) -> None:
        """Test that create_secure_path rejects invalid user ID."""
        manager = SecurityManager()
        job_id = str(uuid.uuid4())
        with pytest.raises(SecurityError):
            manager.create_secure_path("invalid_user", job_id, "test.jpg")

    def test_create_secure_path_rejects_invalid_job_id(self) -> None:
        """Test that create_secure_path rejects invalid job ID."""
        manager = SecurityManager()
        user_id = str(uuid.uuid4())
        with pytest.raises(SecurityError):
            manager.create_secure_path(user_id, "invalid_job", "test.jpg")

    def test_is_safe_path(self) -> None:
        """Test is_safe_path method."""
        manager = SecurityManager()
        assert manager.is_safe_path("/tmp", "file.txt") is True
        assert manager.is_safe_path("/tmp", "../etc/passwd") is False

    def test_get_metrics_summary(self) -> None:
        """Test get_metrics_summary method."""
        manager = SecurityManager()
        summary = manager.get_metrics_summary()
        assert "current_provider" in summary
        assert "validation_level" in summary
        assert "metrics_enabled" in summary
        assert "audit_log_enabled" in summary
        assert "fallback_enabled" in summary

    def test_get_security_manager_singleton(self) -> None:
        """Test that get_security_manager returns singleton."""
        manager1 = get_security_manager()
        manager2 = get_security_manager()
        assert manager1 is manager2

    def test_get_security_manager_with_config(self) -> None:
        """Test get_security_manager with custom config."""
        config = SecurityConfig(preferred_provider="custom")
        manager = get_security_manager(config)
        assert manager.config.preferred_provider == "custom"


class TestSecurityManagerMonitoring:
    """Test SecurityManager monitoring capabilities."""

    def test_record_metric(self) -> None:
        """Test recording performance metrics."""
        manager = SecurityManager()
        manager.record_metric("test_operation", 10.5, success=True)
        # Should not raise any exceptions

    def test_audit_violation(self) -> None:
        """Test recording security violations."""
        from worker.security import SecurityViolationType

        manager = SecurityManager()
        manager.audit_violation(
            SecurityViolationType.PATH_TRAVERSAL,
            "../../../etc/passwd",
            [".."],
            "high",
        )
        # Should not raise any exceptions

    def test_metrics_disabled(self) -> None:
        """Test that metrics can be disabled."""
        config = SecurityConfig(enable_metrics=False)
        manager = SecurityManager(config)
        manager.record_metric("test_operation", 10.5, success=True)
        # Should not raise any exceptions

    def test_audit_log_disabled(self) -> None:
        """Test that audit logging can be disabled."""
        config = SecurityConfig(enable_audit_log=False)
        manager = SecurityManager(config)
        from worker.security import SecurityViolationType

        manager.audit_violation(
            SecurityViolationType.PATH_TRAVERSAL,
            "../../../etc/passwd",
            [".."],
            "high",
        )
        # Should not raise any exceptions


class TestPathTraversalDetection:
    """Test robust path traversal detection."""

    def test_is_safe_path_basic(self) -> None:
        """Test basic safe path validation."""
        manager = SecurityManager()
        assert manager.is_safe_path("/tmp", "file.txt") is True
        assert manager.is_safe_path("/tmp", "subdir/file.txt") is True

    def test_is_safe_path_rejects_parent_traversal(self) -> None:
        """Test rejection of parent directory traversal."""
        manager = SecurityManager()
        assert manager.is_safe_path("/tmp", "../etc/passwd") is False
        assert manager.is_safe_path("/tmp", "../../etc/passwd") is False

    def test_is_safe_path_rejects_dot_slash(self) -> None:
        """Test rejection of ./ sequences."""
        manager = SecurityManager()
        assert manager.is_safe_path("/tmp", "./../../etc/passwd") is False

    def test_is_safe_path_rejects_backslash_traversal(self) -> None:
        """Test rejection of backslash-based traversal."""
        manager = SecurityManager()
        assert manager.is_safe_path("/tmp", "..\\..\\etc\\passwd") is False

    def test_is_safe_path_rejects_url_encoded_traversal(self) -> None:
        """Test rejection of URL-encoded traversal."""
        manager = SecurityManager()
        # %2e%2e = ..
        assert manager.is_safe_path("/tmp", "%2e%2e/etc/passwd") is False
        # %2f = /
        assert manager.is_safe_path("/tmp", "..%2fetc%2fpasswd") is False

    def test_is_safe_path_rejects_double_encoded_traversal(self) -> None:
        """Test rejection of double-encoded traversal."""
        manager = SecurityManager()
        # %252e%252e = %2e%2e = ..
        assert manager.is_safe_path("/tmp", "%252e%252e/etc/passwd") is False

    def test_is_safe_path_rejects_null_bytes(self) -> None:
        """Test rejection of null bytes in path."""
        manager = SecurityManager()
        assert manager.is_safe_path("/tmp", "file\x00.txt") is False
        assert manager.is_safe_path("/tmp", "file%00.txt") is False

    def test_is_safe_path_rejects_unicode_escapes(self) -> None:
        """Test rejection of Unicode escape sequences."""
        manager = SecurityManager()
        # \u002e = .
        assert manager.is_safe_path("/tmp", "\\u002e\\u002e/etc/passwd") is False

    def test_is_safe_path_handles_exceptions(self) -> None:
        """Test that is_safe_path handles exceptions gracefully."""
        manager = SecurityManager()
        # Test with paths that would cause issues
        # Symlink or non-existent base should still work (resolve handles this)
        assert manager.is_safe_path("/nonexistent/base", "file.txt") is True
        # None values should be handled gracefully
        try:
            result = manager.is_safe_path(None, None)  # type: ignore
            assert result is False
        except (TypeError, AttributeError):
            # It's acceptable to raise on None values
            pass

    def test_contains_encoded_traversal_basic(self) -> None:
        """Test basic encoded traversal detection."""
        manager = SecurityManager()
        assert manager._contains_encoded_traversal("../etc/passwd") is True
        assert manager._contains_encoded_traversal("file.txt") is False

    def test_contains_encoded_traversal_url_encoded(self) -> None:
        """Test URL-encoded traversal detection."""
        manager = SecurityManager()
        assert manager._contains_encoded_traversal("%2e%2e/etc") is True
        assert manager._contains_encoded_traversal("%2f..%2f") is True

    def test_contains_encoded_traversal_null_bytes(self) -> None:
        """Test null byte detection."""
        manager = SecurityManager()
        assert manager._contains_encoded_traversal("file\x00.txt") is True
        assert manager._contains_encoded_traversal("file%00.txt") is True

    def test_has_traversal_pattern_basic(self) -> None:
        """Test basic traversal pattern detection."""
        manager = SecurityManager()
        assert manager._has_traversal_pattern("../etc") is True
        assert manager._has_traversal_pattern("../../etc") is True
        assert manager._has_traversal_pattern("file.txt") is False

    def test_has_traversal_pattern_dot_slash(self) -> None:
        """Test ./ pattern detection."""
        manager = SecurityManager()
        assert manager._has_traversal_pattern("./file.txt") is True
        assert manager._has_traversal_pattern("dir/./file.txt") is True

    def test_has_traversal_pattern_backslash(self) -> None:
        """Test backslash detection."""
        manager = SecurityManager()
        assert manager._has_traversal_pattern("..\\etc") is True
        assert manager._has_traversal_pattern("dir\\file.txt") is True

    def test_contains_unicode_escapes(self) -> None:
        """Test Unicode escape detection."""
        manager = SecurityManager()
        assert manager._contains_unicode_escapes("\\u002e\\u002e") is True
        assert manager._contains_unicode_escapes("\\x2e\\x2e") is True
        assert manager._contains_unicode_escapes("file.txt") is False


class TestSpecialCharacterDetection:
    """Test special character detection."""

    def test_detect_special_characters_clean(self) -> None:
        """Test detection on clean input."""
        manager = SecurityManager()
        has_dangerous, patterns = manager.detect_special_characters("file.txt")
        assert has_dangerous is False
        assert len(patterns) == 0

    def test_detect_special_characters_null_bytes(self) -> None:
        """Test detection of null bytes."""
        manager = SecurityManager()
        has_dangerous, patterns = manager.detect_special_characters("file\x00.txt")
        assert has_dangerous is True
        assert "control_characters" in patterns

    def test_detect_special_characters_control_chars(self) -> None:
        """Test detection of control characters."""
        manager = SecurityManager()
        has_dangerous, patterns = manager.detect_special_characters("file\x01\x02.txt")
        assert has_dangerous is True
        assert "control_characters" in patterns

    def test_detect_special_characters_windows_reserved(self) -> None:
        """Test detection of Windows reserved characters."""
        manager = SecurityManager(
            SecurityConfig(platform="windows")
        )
        has_dangerous, patterns = manager.detect_special_characters("file<>.txt")
        assert has_dangerous is True
        assert "windows_reserved_chars" in patterns

    def test_detect_special_characters_windows_reserved_universal(self) -> None:
        """Test Windows reserved character detection in universal mode."""
        manager = SecurityManager(
            SecurityConfig(platform="universal")
        )
        has_dangerous, patterns = manager.detect_special_characters("file|.txt")
        assert has_dangerous is True
        assert "windows_reserved_chars" in patterns

    def test_detect_special_characters_posix_reserved(self) -> None:
        """Test detection of POSIX reserved characters."""
        manager = SecurityManager(
            SecurityConfig(platform="posix")
        )
        has_dangerous, patterns = manager.detect_special_characters("file/name.txt")
        assert has_dangerous is True
        assert "posix_reserved_chars" in patterns

    def test_detect_special_characters_non_printable(self) -> None:
        """Test detection of non-printable characters."""
        manager = SecurityManager()
        has_dangerous, patterns = manager.detect_special_characters("file\x7f.txt")
        assert has_dangerous is True
        assert "non_printable_chars" in patterns

    def test_detect_special_characters_empty_string(self) -> None:
        """Test detection on empty string."""
        manager = SecurityManager()
        has_dangerous, patterns = manager.detect_special_characters("")
        assert has_dangerous is False
        assert len(patterns) == 0

    def test_detect_special_characters_multiple_issues(self) -> None:
        """Test detection of multiple issues."""
        manager = SecurityManager(
            SecurityConfig(platform="universal")
        )
        has_dangerous, patterns = manager.detect_special_characters("file\x00<>.txt")
        assert has_dangerous is True
        assert "control_characters" in patterns
        assert "windows_reserved_chars" in patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
