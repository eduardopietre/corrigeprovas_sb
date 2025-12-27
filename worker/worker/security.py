"""
Security utilities for path validation and sanitization.

This module provides functions to prevent path traversal attacks and
validate storage paths according to security best practices.
"""

import os
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


def validate_uuid(value: str) -> bool:
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
    except ValueError:
        return False


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
        
    Raises:
        SecurityError: If filename is invalid or dangerous
    """
    if not filename or not filename.strip():
        raise SecurityError("Filename cannot be empty")
    
    # URL decode first
    filename = unquote(filename)
    
    # Remove null bytes and control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # Check for path traversal sequences
    if '..' in filename or '/' in filename or '\\' in filename:
        raise SecurityError(f"Path traversal detected in filename: {filename}")
    
    # Remove dangerous characters, keep only alphanumeric, dots, hyphens, underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Ensure it doesn't start with a dot (hidden files)
    if sanitized.startswith('.'):
        sanitized = '_' + sanitized[1:]
    
    # Truncate to max length
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        max_name_length = max_length - len(ext)
        sanitized = name[:max_name_length] + ext
    
    # Ensure we still have a valid filename
    if not sanitized or sanitized in ['.', '..']:
        raise SecurityError(f"Invalid filename after sanitization: {filename}")
    
    return sanitized


def validate_storage_path(storage_path: str) -> Tuple[str, str]:
    """
    Validate and parse a storage path to prevent path traversal attacks.
    
    Args:
        storage_path: Path in format "bucket/path/to/file" or just "path/to/file"
        
    Returns:
        Tuple of (bucket, path)
        
    Raises:
        SecurityError: If path is invalid or contains traversal sequences
    """
    if not storage_path or not storage_path.strip():
        raise SecurityError("Storage path cannot be empty")
    
    # URL decode first
    storage_path = unquote(storage_path)
    
    # Remove null bytes and control characters
    storage_path = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', storage_path)
    
    # Check for path traversal sequences
    if '..' in storage_path:
        raise SecurityError(f"Path traversal detected in storage path: {storage_path}")
    
    # Split into bucket and path
    parts = storage_path.split("/", 1)
    
    if len(parts) == 1:
        # No bucket specified, assume "uploads"
        bucket = "uploads"
        path = parts[0]
    else:
        bucket = parts[0]
        path = parts[1]
    
    # Validate bucket name
    if not validate_bucket_name(bucket):
        raise SecurityError(f"Invalid bucket name: {bucket}")
    
    # Validate path components
    if not path or path.strip() == "":
        raise SecurityError("File path cannot be empty")
    
    # Check each path component
    path_parts = path.split("/")
    for part in path_parts:
        if not part or part.strip() == "":
            raise SecurityError(f"Empty path component in: {path}")
        
        if part in ['.', '..']:
            raise SecurityError(f"Invalid path component: {part}")
        
        # Check for dangerous characters in path components
        if re.search(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', part):
            raise SecurityError(f"Invalid characters in path component: {part}")
    
    return bucket, path


def validate_bucket_name(bucket: str) -> bool:
    """
    Validate a storage bucket name.
    
    Args:
        bucket: Bucket name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not bucket or not bucket.strip():
        return False
    
    # Allow only specific bucket names
    allowed_buckets = {'uploads', 'results', 'templates', 'exports'}
    
    return bucket in allowed_buckets


def validate_user_path_access(path: str, user_id: str) -> bool:
    """
    Validate that a user can access a specific path.
    
    Args:
        path: File path to validate
        user_id: User ID requesting access
        
    Returns:
        True if user can access the path, False otherwise
    """
    if not validate_uuid(user_id):
        return False
    
    # Check for path traversal sequences first
    if '..' in path:
        return False
    
    # Path should start with user ID for user-specific buckets
    path_parts = path.split("/")
    
    if len(path_parts) == 0:
        return False
    
    # First component should be the user ID for uploads and results
    first_component = path_parts[0]
    
    return first_component == user_id


def normalize_path(path: str) -> str:
    """
    Normalize a path to prevent bypasses.
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized path
    """
    # Use pathlib to normalize the path
    normalized = str(Path(path).resolve())
    
    # Ensure it doesn't escape the intended directory
    if '..' in normalized:
        raise SecurityError(f"Path traversal detected after normalization: {path}")
    
    return normalized


def validate_file_extension(filename: str, allowed_extensions: Optional[set] = None) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (with dots)
        
    Returns:
        True if extension is allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.tiff', '.pdf'}
    
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions


def create_secure_path(user_id: str, job_id: str, filename: str) -> str:
    """
    Create a secure path for file storage.
    
    Args:
        user_id: User ID
        job_id: Job ID
        filename: Original filename
        
    Returns:
        Secure path string
        
    Raises:
        SecurityError: If any parameter is invalid
    """
    if not validate_uuid(user_id):
        raise SecurityError(f"Invalid user ID: {user_id}")
    
    if not validate_uuid(job_id):
        raise SecurityError(f"Invalid job ID: {job_id}")
    
    sanitized_filename = sanitize_filename(filename)
    
    return f"{user_id}/{job_id}/{sanitized_filename}"