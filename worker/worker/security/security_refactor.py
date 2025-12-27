"""
Refactored security module with pluggable validation providers.

This module provides a flexible architecture for path validation and
filename sanitization using multiple backend providers.
"""

import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import unquote

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"
    NORMAL = "normal"
    PERMISSIVE = "permissive"


class SecurityViolationType(Enum):
    """Types of security violations."""
    PATH_TRAVERSAL = "path_traversal"
    INVALID_FILENAME = "invalid_filename"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    INVALID_CHARACTERS = "invalid_characters"
    ENCODING_ATTACK = "encoding_attack"


@dataclass
class SecurityViolation:
    """Represents a security violation detected."""

    violation_type: SecurityViolationType
    original_value: str
    detected_patterns: List[str] = field(default_factory=list)
    severity: str = "medium"  # low, medium, high, critical
    timestamp: datetime = field(default_factory=datetime.now)
    provider_used: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"SecurityViolation({self.violation_type.value}, "
            f"severity={self.severity}, patterns={self.detected_patterns})"
        )


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    sanitized_value: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    provider_used: Optional[str] = None
    violation: Optional[SecurityViolation] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for security operations."""

    operation: str
    provider: str
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        status = "success" if self.success else "failed"
        return (
            f"Metrics({self.operation}, {self.provider}, "
            f"{self.duration_ms:.2f}ms, {status})"
        )


@dataclass
class SecurityConfig:
    """Centralized security configuration."""

    # Provider selection
    preferred_provider: str = "pathvalidate"  # pathvalidate, werkzeug, custom
    validation_level: ValidationLevel = ValidationLevel.STRICT
    platform: str = "universal"  # universal, windows, posix

    # Filename validation
    max_filename_length: int = 255
    replacement_char: str = "_"

    # Path validation
    allowed_buckets: Set[str] = field(
        default_factory=lambda: {"uploads", "results", "templates", "exports"}
    )

    # Fallback behavior
    enable_fallback: bool = True
    log_provider_usage: bool = True
    enable_metrics: bool = True
    enable_audit_log: bool = True

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Create configuration from environment variables."""
        return cls(
            preferred_provider=os.getenv(
                "SECURITY_PROVIDER", "pathvalidate"
            ),
            validation_level=ValidationLevel(
                os.getenv("SECURITY_LEVEL", "strict")
            ),
            platform=os.getenv("SECURITY_PLATFORM", "universal"),
            max_filename_length=int(
                os.getenv("SECURITY_MAX_FILENAME_LENGTH", "255")
            ),
            enable_fallback=os.getenv("SECURITY_ENABLE_FALLBACK", "true")
            .lower()
            == "true",
            log_provider_usage=os.getenv(
                "SECURITY_LOG_PROVIDER_USAGE", "true"
            ).lower()
            == "true",
            enable_metrics=os.getenv("SECURITY_ENABLE_METRICS", "true")
            .lower()
            == "true",
            enable_audit_log=os.getenv("SECURITY_ENABLE_AUDIT_LOG", "true")
            .lower()
            == "true",
        )


class ValidationProvider(ABC):
    """Abstract base class for validation providers."""

    @abstractmethod
    def sanitize_filename(
        self, filename: str, **kwargs: object
    ) -> str:
        """
        Sanitize a filename.

        Args:
            filename: Original filename
            **kwargs: Additional provider-specific options

        Returns:
            Sanitized filename

        Raises:
            ValueError: If filename is invalid
        """
        pass

    @abstractmethod
    def validate_filename(
        self, filename: str, **kwargs: object
    ) -> ValidationResult:
        """
        Validate a filename.

        Args:
            filename: Filename to validate
            **kwargs: Additional provider-specific options

        Returns:
            ValidationResult with validation details
        """
        pass

    @abstractmethod
    def is_valid_filename(
        self, filename: str, **kwargs: object
    ) -> bool:
        """
        Check if filename is valid.

        Args:
            filename: Filename to check
            **kwargs: Additional provider-specific options

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available."""
        pass


class CustomProvider(ValidationProvider):
    """
    Custom provider using the current implementation.

    This serves as a fallback when other libraries are not available.
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()

    def sanitize_filename(
        self, filename: str, **kwargs: object
    ) -> str:
        """Sanitize filename using custom implementation."""
        import re
        from urllib.parse import unquote

        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")

        # URL decode first
        filename = unquote(filename)

        # Remove null bytes and control characters
        filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

        # Check for path traversal sequences
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError(
                f"Path traversal detected in filename: {filename}"
            )

        # Remove dangerous characters
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

        # Ensure it doesn't start with a dot
        if sanitized.startswith("."):
            sanitized = "_" + sanitized[1:]

        # Truncate to max length
        max_length = kwargs.get("max_length", self.config.max_filename_length)
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            max_name_length = max_length - len(ext)
            sanitized = name[:max_name_length] + ext

        # Ensure we still have a valid filename
        if not sanitized or sanitized in [".", ".."]:
            raise ValueError(
                f"Invalid filename after sanitization: {filename}"
            )

        return sanitized

    def validate_filename(
        self, filename: str, **kwargs: object
    ) -> ValidationResult:
        """Validate filename using custom implementation."""
        try:
            sanitized = self.sanitize_filename(filename, **kwargs)
            return ValidationResult(
                is_valid=True,
                sanitized_value=sanitized,
                provider_used=self.get_provider_name(),
            )
        except ValueError as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(e)],
                provider_used=self.get_provider_name(),
            )

    def is_valid_filename(
        self, filename: str, **kwargs: object
    ) -> bool:
        """Check if filename is valid."""
        result = self.validate_filename(filename, **kwargs)
        return result.is_valid

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "custom"

    def is_available(self) -> bool:
        """Custom provider is always available."""
        return True


class PathValidateProvider(ValidationProvider):
    """Provider using the pathvalidate library."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.pathvalidate = None
        self._available = False

        try:
            import pathvalidate

            self.pathvalidate = pathvalidate
            self._available = True
            logger.debug("PathValidate provider initialized successfully")
        except ImportError:
            logger.debug("PathValidate library not available")

    def sanitize_filename(
        self, filename: str, **kwargs: object
    ) -> str:
        """Sanitize filename using pathvalidate."""
        if not self._available:
            raise ImportError("pathvalidate library not available")

        max_length = kwargs.get("max_length", self.config.max_filename_length)
        replacement = kwargs.get("replacement", self.config.replacement_char)

        return self.pathvalidate.sanitize_filename(
            filename,
            platform=self.config.platform,
            max_len=max_length,
            replacement_text=replacement,
        )

    def validate_filename(
        self, filename: str, **kwargs: object
    ) -> ValidationResult:
        """Validate filename using pathvalidate."""
        if not self._available:
            return ValidationResult(
                is_valid=False,
                errors=["pathvalidate library not available"],
                provider_used=self.get_provider_name(),
            )

        try:
            is_valid = self.pathvalidate.is_valid_filename(
                filename, platform=self.config.platform
            )
            if is_valid:
                sanitized = self.sanitize_filename(filename, **kwargs)
                return ValidationResult(
                    is_valid=True,
                    sanitized_value=sanitized,
                    provider_used=self.get_provider_name(),
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    errors=["Invalid filename according to pathvalidate"],
                    provider_used=self.get_provider_name(),
                )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(e)],
                provider_used=self.get_provider_name(),
            )

    def is_valid_filename(
        self, filename: str, **kwargs: object
    ) -> bool:
        """Check if filename is valid."""
        if not self._available:
            return False

        try:
            return self.pathvalidate.is_valid_filename(
                filename, platform=self.config.platform
            )
        except Exception:
            return False

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "pathvalidate"

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._available


class WerkzeugProvider(ValidationProvider):
    """Provider using werkzeug.utils.secure_filename."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.secure_filename_func = None
        self._available = False

        try:
            from werkzeug.utils import secure_filename

            self.secure_filename_func = secure_filename
            self._available = True
            logger.debug("Werkzeug provider initialized successfully")
        except ImportError:
            logger.debug("Werkzeug library not available")

    def sanitize_filename(
        self, filename: str, **kwargs: object
    ) -> str:
        """Sanitize filename using werkzeug."""
        if not self._available:
            raise ImportError("werkzeug library not available")

        sanitized = self.secure_filename_func(filename)

        # Apply max_length if specified
        max_length = kwargs.get("max_length", self.config.max_filename_length)
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            max_name_length = max_length - len(ext)
            sanitized = name[:max_name_length] + ext

        return sanitized

    def validate_filename(
        self, filename: str, **kwargs: object
    ) -> ValidationResult:
        """Validate filename using werkzeug."""
        if not self._available:
            return ValidationResult(
                is_valid=False,
                errors=["werkzeug library not available"],
                provider_used=self.get_provider_name(),
            )

        try:
            sanitized = self.sanitize_filename(filename, **kwargs)
            # Werkzeug returns empty string for invalid filenames
            if not sanitized:
                return ValidationResult(
                    is_valid=False,
                    errors=["Filename sanitized to empty string"],
                    provider_used=self.get_provider_name(),
                )
            return ValidationResult(
                is_valid=True,
                sanitized_value=sanitized,
                provider_used=self.get_provider_name(),
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(e)],
                provider_used=self.get_provider_name(),
            )

    def is_valid_filename(
        self, filename: str, **kwargs: object
    ) -> bool:
        """Check if filename is valid."""
        if not self._available:
            return False

        try:
            sanitized = self.sanitize_filename(filename, **kwargs)
            return bool(sanitized)
        except Exception:
            return False

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "werkzeug"

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._available


class SecurityManager:
    """
    Main security manager coordinating validation providers.

    Maintains backward compatibility with the existing security API
    while providing a flexible provider-based architecture.
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.providers: dict[str, ValidationProvider] = {}
        self._current_provider: Optional[ValidationProvider] = None

        # Initialize all providers
        self._init_providers()

        # Select the best available provider
        self._select_provider()

    def _init_providers(self) -> None:
        """Initialize all available providers."""
        self.providers["pathvalidate"] = PathValidateProvider(self.config)
        self.providers["werkzeug"] = WerkzeugProvider(self.config)
        self.providers["custom"] = CustomProvider(self.config)

    def _select_provider(self) -> None:
        """Select the best available provider based on configuration."""
        # Try preferred provider first
        if self.config.preferred_provider in self.providers:
            provider = self.providers[self.config.preferred_provider]
            if provider.is_available():
                self._current_provider = provider
                if self.config.log_provider_usage:
                    logger.info(
                        f"Using {provider.get_provider_name()} "
                        "as security provider"
                    )
                return

        # Fallback to available providers in order
        if self.config.enable_fallback:
            for name in ["pathvalidate", "werkzeug", "custom"]:
                if name != self.config.preferred_provider:
                    provider = self.providers[name]
                    if provider.is_available():
                        self._current_provider = provider
                        if self.config.log_provider_usage:
                            logger.warning(
                                f"Preferred provider "
                                f"{self.config.preferred_provider} "
                                f"not available, using {name}"
                            )
                        return

        # This should never happen as custom provider is always available
        raise RuntimeError("No security provider available")

    def sanitize_filename(
        self, filename: str, max_length: Optional[int] = None
    ) -> str:
        """
        Sanitize a filename (backward compatible API).

        Args:
            filename: Original filename
            max_length: Maximum allowed length

        Returns:
            Sanitized filename

        Raises:
            SecurityError: If filename is invalid
        """
        if self._current_provider is None:
            raise SecurityError("No security provider available")

        kwargs = {}
        if max_length is not None:
            kwargs["max_length"] = max_length

        try:
            return self._current_provider.sanitize_filename(filename, **kwargs)
        except ValueError as e:
            raise SecurityError(str(e)) from e

    def validate_filename(
        self, filename: str, max_length: Optional[int] = None
    ) -> ValidationResult:
        """
        Validate a filename.

        Args:
            filename: Filename to validate
            max_length: Maximum allowed length

        Returns:
            ValidationResult with details
        """
        if self._current_provider is None:
            raise RuntimeError("No security provider available")

        kwargs = {}
        if max_length is not None:
            kwargs["max_length"] = max_length

        return self._current_provider.validate_filename(filename, **kwargs)

    def is_valid_filename(self, filename: str) -> bool:
        """
        Check if filename is valid.

        Args:
            filename: Filename to check

        Returns:
            True if valid, False otherwise
        """
        if self._current_provider is None:
            return False

        return self._current_provider.is_valid_filename(filename)

    def get_current_provider_name(self) -> str:
        """Get the name of the currently active provider."""
        if self._current_provider is None:
            return "none"
        return self._current_provider.get_provider_name()

    # Backward-compatible API methods

    def validate_storage_path(
        self, storage_path: str
    ) -> tuple[str, str]:
        """
        Validate and parse a storage path (backward compatible).

        Args:
            storage_path: Path in format "bucket/path/to/file"

        Returns:
            Tuple of (bucket, path)

        Raises:
            SecurityError: If path is invalid or contains traversal
        """
        if not storage_path or not storage_path.strip():
            raise SecurityError("Storage path cannot be empty")

        # URL decode first
        storage_path = unquote(storage_path)

        # Remove null bytes and control characters
        import re
        storage_path = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", storage_path)

        # Check for path traversal sequences
        if ".." in storage_path:
            raise SecurityError(
                f"Path traversal detected in storage path: {storage_path}"
            )

        # Split into bucket and path
        parts = storage_path.split("/", 1)

        if len(parts) == 1:
            bucket = "uploads"
            path = parts[0]
        else:
            bucket = parts[0]
            path = parts[1]

        # Validate bucket name
        if not self.validate_bucket_name(bucket):
            raise SecurityError(f"Invalid bucket name: {bucket}")

        # Validate path components
        if not path or path.strip() == "":
            raise SecurityError("File path cannot be empty")

        # Check each path component
        path_parts = path.split("/")
        for part in path_parts:
            if not part or part.strip() == "":
                raise SecurityError(f"Empty path component in: {path}")

            if part in [".", ".."]:
                raise SecurityError(f"Invalid path component: {part}")

            # Check for dangerous characters
            if re.search(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', part):
                raise SecurityError(
                    f"Invalid characters in path component: {part}"
                )

        return bucket, path

    def validate_bucket_name(self, bucket: str) -> bool:
        """
        Validate a storage bucket name (backward compatible).

        Args:
            bucket: Bucket name to validate

        Returns:
            True if valid, False otherwise
        """
        if not bucket or not bucket.strip():
            return False

        return bucket in self.config.allowed_buckets

    def validate_user_path_access(
        self, path: str, user_id: str
    ) -> bool:
        """
        Validate that a user can access a specific path.

        Args:
            path: File path to validate
            user_id: User ID requesting access

        Returns:
            True if user can access the path, False otherwise
        """
        if not self._is_valid_uuid(user_id):
            return False

        # Check for path traversal sequences
        if ".." in path:
            return False

        # Path should start with user ID
        path_parts = path.split("/")

        if len(path_parts) == 0:
            return False

        first_component = path_parts[0]

        return first_component == user_id

    def create_secure_path(
        self, user_id: str, job_id: str, filename: str
    ) -> str:
        """
        Create a secure path for file storage (backward compatible).

        Args:
            user_id: User ID
            job_id: Job ID
            filename: Original filename

        Returns:
            Secure path string

        Raises:
            SecurityError: If any parameter is invalid
        """
        if not self._is_valid_uuid(user_id):
            raise SecurityError(f"Invalid user ID: {user_id}")

        if not self._is_valid_uuid(job_id):
            raise SecurityError(f"Invalid job ID: {job_id}")

        sanitized_filename = self.sanitize_filename(filename)

        return f"{user_id}/{job_id}/{sanitized_filename}"

    def is_safe_path(self, basedir: str, path: str) -> bool:
        """
        Check if a path is safe and doesn't escape basedir.

        Implements robust path traversal detection using:
        - os.path.normpath() and pathlib.Path.resolve()
        - Detection of encoded traversal sequences
        - Validation of sandbox boundaries

        Args:
            basedir: Base directory path
            path: Path to check

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # First, detect encoded traversal attempts
            if self._contains_encoded_traversal(path):
                return False

            # Normalize and resolve paths
            base_path = Path(basedir).resolve()
            full_path = (base_path / path).resolve()

            # Check if resolved path is within basedir
            return str(full_path).startswith(str(base_path))
        except Exception:
            return False

    def _contains_encoded_traversal(self, path: str) -> bool:
        """
        Detect path traversal attempts using various encodings.

        Detects:
        - Standard traversal: .., ../, ..\
        - URL encoded: %2e%2e, %2f, %5c
        - Unicode encoded: \u002e\u002e, etc.
        - Double encoded: %252e%252e
        - Null bytes: \x00, %00
        - Mixed encodings

        Args:
            path: Path to check

        Returns:
            True if encoded traversal detected, False otherwise
        """
        import re
        from urllib.parse import unquote

        if not path:
            return False

        # Check for null bytes (direct and encoded)
        if "\x00" in path or "%00" in path or "\\x00" in path:
            return True

        # Progressively decode to catch multiple encoding layers
        decoded_path = path
        previous_decoded = None
        max_iterations = 5  # Prevent infinite loops

        for _ in range(max_iterations):
            if decoded_path == previous_decoded:
                break

            previous_decoded = decoded_path

            # URL decode
            try:
                decoded_path = unquote(decoded_path)
            except Exception:
                break

            # Check for traversal patterns after each decode
            if self._has_traversal_pattern(decoded_path):
                return True

        # Also check for Unicode escape sequences
        if self._contains_unicode_escapes(path):
            return True

        return False

    def _has_traversal_pattern(self, path: str) -> bool:
        """
        Check if path contains traversal patterns.

        Detects:
        - .. sequences
        - ./ or .\ sequences
        - Backslashes (Windows path separators in Unix context)

        Args:
            path: Path to check

        Returns:
            True if traversal pattern found, False otherwise
        """
        import re

        if not path:
            return False

        # Normalize path separators for checking
        normalized = path.replace("\\", "/")

        # Check for .. patterns
        if ".." in normalized:
            return True

        # Check for ./ at start or after /
        if re.search(r"(^|/)\./", normalized):
            return True

        # Check for backslashes in path (potential Windows escape)
        if "\\" in path:
            return True

        return False

    def _contains_unicode_escapes(self, path: str) -> bool:
        """
        Detect Unicode escape sequences that could represent traversal.

        Detects:
        - \\uXXXX sequences
        - \\UXXXXXXXX sequences
        - \\xXX sequences

        Args:
            path: Path to check

        Returns:
            True if Unicode escapes found, False otherwise
        """
        import re

        if not path:
            return False

        # Check for Unicode escape patterns
        unicode_patterns = [
            r"\\u[0-9a-fA-F]{4}",  # \uXXXX
            r"\\U[0-9a-fA-F]{8}",  # \UXXXXXXXX
            r"\\x[0-9a-fA-F]{2}",  # \xXX
        ]

        for pattern in unicode_patterns:
            if re.search(pattern, path):
                return True

        return False

    def detect_special_characters(self, value: str) -> tuple[bool, List[str]]:
        """
        Detect special characters that could be dangerous.

        Detects:
        - Null bytes and control characters
        - Platform-specific dangerous characters
        - Invalid UTF-8 sequences

        Args:
            value: String to check

        Returns:
            Tuple of (has_dangerous_chars, list_of_detected_patterns)
        """
        import re

        if not value:
            return False, []

        detected_patterns = []

        # Check for null bytes and control characters
        if re.search(r"[\x00-\x1f\x7f-\x9f]", value):
            detected_patterns.append("control_characters")

        # Check for Windows reserved characters
        if self.config.platform in ["universal", "windows"]:
            if re.search(r'[<>:"|?*]', value):
                detected_patterns.append("windows_reserved_chars")

        # Check for POSIX reserved characters (less restrictive)
        if self.config.platform in ["universal", "posix"]:
            if re.search(r"[\x00/]", value):
                detected_patterns.append("posix_reserved_chars")

        # Check for invalid UTF-8 sequences
        try:
            value.encode("utf-8").decode("utf-8")
        except UnicodeDecodeError:
            detected_patterns.append("invalid_utf8")

        # Check for non-printable characters
        if any(ord(c) < 32 or (127 <= ord(c) < 160) for c in value):
            detected_patterns.append("non_printable_chars")

        return len(detected_patterns) > 0, detected_patterns

    # Monitoring and metrics methods

    def record_metric(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """
        Record a performance metric.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
        """
        if not self.config.enable_metrics:
            return

        metric = PerformanceMetrics(
            operation=operation,
            provider=self.get_current_provider_name(),
            duration_ms=duration_ms,
            success=success,
        )

        logger.debug(f"Performance metric: {metric}")

    def audit_violation(
        self,
        violation_type: SecurityViolationType,
        original_value: str,
        detected_patterns: Optional[List[str]] = None,
        severity: str = "medium",
    ) -> None:
        """
        Record a security violation for audit purposes.

        Args:
            violation_type: Type of violation
            original_value: Original value that triggered violation
            detected_patterns: Patterns that were detected
            severity: Severity level
        """
        if not self.config.enable_audit_log:
            return

        violation = SecurityViolation(
            violation_type=violation_type,
            original_value=original_value,
            detected_patterns=detected_patterns or [],
            severity=severity,
            provider_used=self.get_current_provider_name(),
        )

        logger.warning(f"Security violation detected: {violation}")

    def get_metrics_summary(self) -> Dict[str, object]:
        """
        Get a summary of security metrics.

        Returns:
            Dictionary with metrics summary
        """
        return {
            "current_provider": self.get_current_provider_name(),
            "validation_level": self.config.validation_level.value,
            "metrics_enabled": self.config.enable_metrics,
            "audit_log_enabled": self.config.enable_audit_log,
            "fallback_enabled": self.config.enable_fallback,
        }

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        """
        Validate if a string is a valid UUID.

        Args:
            value: String to validate

        Returns:
            True if valid UUID, False otherwise
        """
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False
