/**
 * Security utilities for Edge Functions
 * 
 * This module provides functions to prevent path traversal attacks and
 * validate inputs according to security best practices.
 */

export class SecurityError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'SecurityError';
    }
}

/**
 * Validate if a string is a valid UUID
 */
export function isValidUUID(value: string): boolean {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(value);
}

/**
 * Sanitize a filename to prevent path traversal and other attacks
 */
export function sanitizeFilename(filename: string, maxLength: number = 255): string {
    if (!filename || !filename.trim()) {
        throw new SecurityError("Filename cannot be empty");
    }

    // URL decode first
    let sanitized = decodeURIComponent(filename);

    // Remove null bytes and control characters
    sanitized = sanitized.replace(/[\x00-\x1f\x7f-\x9f]/g, '');

    // Check for path traversal sequences
    if (sanitized.includes('..') || sanitized.includes('/') || sanitized.includes('\\')) {
        throw new SecurityError(`Path traversal detected in filename: ${filename}`);
    }

    // Remove dangerous characters, keep only alphanumeric, dots, hyphens, underscores
    sanitized = sanitized.replace(/[^a-zA-Z0-9._-]/g, '_');

    // Ensure it doesn't start with a dot (hidden files)
    if (sanitized.startsWith('.')) {
        sanitized = '_' + sanitized.substring(1);
    }

    // Truncate to max length
    if (sanitized.length > maxLength) {
        const lastDotIndex = sanitized.lastIndexOf('.');
        if (lastDotIndex > 0) {
            const extension = sanitized.substring(lastDotIndex);
            const maxNameLength = maxLength - extension.length;
            sanitized = sanitized.substring(0, maxNameLength) + extension;
        } else {
            sanitized = sanitized.substring(0, maxLength);
        }
    }

    // Ensure we still have a valid filename
    if (!sanitized || sanitized === '.' || sanitized === '..') {
        throw new SecurityError(`Invalid filename after sanitization: ${filename}`);
    }

    return sanitized;
}

/**
 * Validate and parse a storage path to prevent path traversal attacks
 */
export function validateStoragePath(storagePath: string): { bucket: string; path: string } {
    if (!storagePath || !storagePath.trim()) {
        throw new SecurityError("Storage path cannot be empty");
    }

    // URL decode first
    let decoded = decodeURIComponent(storagePath);

    // Remove null bytes and control characters
    decoded = decoded.replace(/[\x00-\x1f\x7f-\x9f]/g, '');

    // Check for path traversal sequences
    if (decoded.includes('..')) {
        throw new SecurityError(`Path traversal detected in storage path: ${storagePath}`);
    }

    // Split into bucket and path
    const parts = decoded.split('/', 2);

    let bucket: string;
    let path: string;

    if (parts.length === 1) {
        // No bucket specified, assume "uploads"
        bucket = "uploads";
        path = parts[0];
    } else {
        bucket = parts[0];
        path = parts[1];
    }

    // Validate bucket name
    if (!isValidBucketName(bucket)) {
        throw new SecurityError(`Invalid bucket name: ${bucket}`);
    }

    // Validate path components
    if (!path || path.trim() === "") {
        throw new SecurityError("File path cannot be empty");
    }

    // Check each path component
    const pathParts = path.split("/");
    for (const part of pathParts) {
        if (!part || part.trim() === "") {
            throw new SecurityError(`Empty path component in: ${path}`);
        }

        if (part === '.' || part === '..') {
            throw new SecurityError(`Invalid path component: ${part}`);
        }

        // Check for dangerous characters in path components
        if (/[<>:"|?*\x00-\x1f\x7f-\x9f]/.test(part)) {
            throw new SecurityError(`Invalid characters in path component: ${part}`);
        }
    }

    return { bucket, path };
}

/**
 * Validate a storage bucket name
 */
export function isValidBucketName(bucket: string): boolean {
    if (!bucket || !bucket.trim()) {
        return false;
    }

    // Allow only specific bucket names
    const allowedBuckets = new Set(['uploads', 'results', 'templates', 'exports']);

    return allowedBuckets.has(bucket);
}

/**
 * Validate that a user can access a specific path
 */
export function validateUserPathAccess(path: string, userId: string): boolean {
    if (!isValidUUID(userId)) {
        return false;
    }

    // Path should start with user ID for user-specific buckets
    const pathParts = path.split("/");

    if (pathParts.length === 0) {
        return false;
    }

    // First component should be the user ID for uploads and results
    const firstComponent = pathParts[0];

    return firstComponent === userId;
}

/**
 * Create a secure path for file storage
 */
export function createSecurePath(userId: string, jobId: string, filename: string): string {
    if (!isValidUUID(userId)) {
        throw new SecurityError(`Invalid user ID: ${userId}`);
    }

    if (!isValidUUID(jobId)) {
        throw new SecurityError(`Invalid job ID: ${jobId}`);
    }

    const sanitizedFilename = sanitizeFilename(filename);

    return `${userId}/${jobId}/${sanitizedFilename}`;
}

/**
 * Validate file extension against allowed list
 */
export function isValidFileExtension(filename: string, allowedExtensions?: Set<string>): boolean {
    const defaultAllowed = new Set(['.jpg', '.jpeg', '.png', '.webp', '.tiff', '.pdf']);
    const allowed = allowedExtensions || defaultAllowed;

    const lastDotIndex = filename.lastIndexOf('.');
    if (lastDotIndex === -1) {
        return false;
    }

    const extension = filename.substring(lastDotIndex).toLowerCase();
    return allowed.has(extension);
}

/**
 * Validate content type against allowed list
 */
export function isValidContentType(contentType: string): boolean {
    const allowedTypes = new Set([
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/tiff',
        'application/pdf'
    ]);

    return allowedTypes.has(contentType);
}

/**
 * Rate limiting key generator
 */
export function createRateLimitKey(userId: string, action: string): string {
    return `rate_limit:${action}:${userId}`;
}

/**
 * Validate idempotency key format
 */
export function validateIdempotencyKey(key: string): boolean {
    if (!key || key.length < 1 || key.length > 255) {
        return false;
    }

    // Allow alphanumeric, hyphens, underscores
    return /^[a-zA-Z0-9_-]+$/.test(key);
}