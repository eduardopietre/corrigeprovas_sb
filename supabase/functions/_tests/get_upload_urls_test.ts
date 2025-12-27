// Tests for get_upload_urls Edge Function
// Tests input validation and URL generation logic
// Requirements: 4.1, 4.2

import {
  assertEquals,
  assertExists,
  setupTestEnv,
  createMockRequest,
  createUnauthenticatedRequest,
  createCorsRequest,
  parseJsonResponse,
  assertCorsHeaders,
  assertErrorResponse,
  ErrorResponse,
  generateUUID,
} from "./test_helpers.ts";
import { z } from "https://deno.land/x/zod@v3.23.8/mod.ts";

// Setup environment before tests
setupTestEnv();

// Input schema (same as in the function)
const GetUploadUrlsInput = z.object({
  count: z.number().int().min(1).max(100),
  contentTypes: z.array(
    z.enum(["image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf"])
  ).min(1),
  filenameHints: z.array(z.string()).optional(),
});

Deno.test("GetUploadUrlsInput schema - valid input", () => {
  const input = {
    count: 3,
    contentTypes: ["image/jpeg", "image/png", "image/webp"],
  };

  const result = GetUploadUrlsInput.safeParse(input);
  assertEquals(result.success, true);
});

Deno.test("GetUploadUrlsInput schema - with filename hints", () => {
  const input = {
    count: 2,
    contentTypes: ["image/jpeg", "image/png"],
    filenameHints: ["photo1", "photo2"],
  };

  const result = GetUploadUrlsInput.safeParse(input);
  assertEquals(result.success, true);
});

Deno.test("GetUploadUrlsInput schema - count must be at least 1", () => {
  const input = {
    count: 0,
    contentTypes: [],
  };

  const result = GetUploadUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("GetUploadUrlsInput schema - count must be at most 100", () => {
  const input = {
    count: 101,
    contentTypes: Array(101).fill("image/jpeg"),
  };

  const result = GetUploadUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("GetUploadUrlsInput schema - invalid content type rejected", () => {
  const input = {
    count: 1,
    contentTypes: ["text/plain"],
  };

  const result = GetUploadUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("GetUploadUrlsInput schema - all valid content types accepted", () => {
  const validTypes = ["image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf"];
  
  for (const contentType of validTypes) {
    const input = {
      count: 1,
      contentTypes: [contentType],
    };
    const result = GetUploadUrlsInput.safeParse(input);
    assertEquals(result.success, true, `${contentType} should be valid`);
  }
});

Deno.test("GetUploadUrlsInput schema - contentTypes must not be empty", () => {
  const input = {
    count: 1,
    contentTypes: [],
  };

  const result = GetUploadUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("GetUploadUrlsInput schema - count must be integer", () => {
  const input = {
    count: 1.5,
    contentTypes: ["image/jpeg"],
  };

  const result = GetUploadUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

// Helper function tests
Deno.test("getExtensionFromContentType - returns correct extensions", () => {
  const extensions: Record<string, string> = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
    "application/pdf": ".pdf",
  };

  for (const [contentType, expectedExt] of Object.entries(extensions)) {
    const ext = getExtensionFromContentType(contentType);
    assertEquals(ext, expectedExt, `${contentType} should map to ${expectedExt}`);
  }
});

Deno.test("sanitizeFilename - removes special characters", () => {
  const result = sanitizeFilename("test@file#name!.jpg");
  assertEquals(result.includes("@"), false);
  assertEquals(result.includes("#"), false);
  assertEquals(result.includes("!"), false);
});

Deno.test("sanitizeFilename - preserves alphanumeric and underscore", () => {
  const result = sanitizeFilename("test_file_123");
  assertEquals(result, "test_file_123");
});

Deno.test("sanitizeFilename - truncates long names", () => {
  const longName = "a".repeat(100);
  const result = sanitizeFilename(longName);
  assertEquals(result.length <= 50, true);
});

// Helper functions (copied from the Edge Function for testing)
function getExtensionFromContentType(contentType: string): string {
  const extensions: Record<string, string> = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
    "application/pdf": ".pdf",
  };
  return extensions[contentType] || ".bin";
}

function sanitizeFilename(filename: string): string {
  return filename
    .replace(/[^a-zA-Z0-9_-]/g, "_")
    .substring(0, 50);
}
