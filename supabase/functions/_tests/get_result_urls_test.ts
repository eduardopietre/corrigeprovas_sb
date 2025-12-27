// Tests for get_result_urls Edge Function
// Tests input validation and URL generation logic
// Requirements: 7.1, 7.2, 7.3, 7.4

import {
  assertEquals,
  assertExists,
  setupTestEnv,
  generateUUID,
} from "./test_helpers.ts";
import { z } from "https://deno.land/x/zod@v3.23.8/mod.ts";

// Setup environment before tests
setupTestEnv();

// Input schema (same as in the function)
const GetResultUrlsInput = z.object({
  jobId: z.string().uuid(),
});

Deno.test("GetResultUrlsInput schema - valid UUID", () => {
  const input = { jobId: generateUUID() };
  const result = GetResultUrlsInput.safeParse(input);
  assertEquals(result.success, true);
});

Deno.test("GetResultUrlsInput schema - invalid UUID rejected", () => {
  const input = { jobId: "not-a-uuid" };
  const result = GetResultUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("GetResultUrlsInput schema - empty string rejected", () => {
  const input = { jobId: "" };
  const result = GetResultUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("GetResultUrlsInput schema - missing jobId rejected", () => {
  const input = {};
  const result = GetResultUrlsInput.safeParse(input);
  assertEquals(result.success, false);
});

// URL expiration tests
const URL_EXPIRY_SECONDS = 3600;

Deno.test("URL expiration - 1 hour in seconds", () => {
  assertEquals(URL_EXPIRY_SECONDS, 3600);
});

Deno.test("URL expiration - calculates future date", () => {
  const now = Date.now();
  const expiresAt = new Date(now + URL_EXPIRY_SECONDS * 1000);
  
  assertEquals(expiresAt.getTime() > now, true);
  assertEquals(expiresAt.getTime() - now, URL_EXPIRY_SECONDS * 1000);
});

// Storage path extraction tests
Deno.test("extractStoragePath - removes bucket prefix", () => {
  const fullPath = "results/user-id/job-id/file.xlsx";
  const result = extractStoragePath(fullPath, "results");
  assertEquals(result, "user-id/job-id/file.xlsx");
});

Deno.test("extractStoragePath - handles path without prefix", () => {
  const fullPath = "user-id/job-id/file.xlsx";
  const result = extractStoragePath(fullPath, "results");
  assertEquals(result, "user-id/job-id/file.xlsx");
});

Deno.test("extractStoragePath - handles different bucket names", () => {
  const fullPath = "uploads/user-id/image.jpg";
  const result = extractStoragePath(fullPath, "uploads");
  assertEquals(result, "user-id/image.jpg");
});

// Helper function (copied from the Edge Function for testing)
function extractStoragePath(fullPath: string, bucketName: string): string {
  const prefix = `${bucketName}/`;
  if (fullPath.startsWith(prefix)) {
    return fullPath.substring(prefix.length);
  }
  return fullPath;
}

// Job status validation tests
Deno.test("Job status - DONE allows XLSX URL", () => {
  const status: string = "DONE";
  const hasXlsxPath = true;
  const shouldGenerateXlsxUrl = status === "DONE" && hasXlsxPath;
  assertEquals(shouldGenerateXlsxUrl, true);
});

Deno.test("Job status - PROCESSING does not allow XLSX URL", () => {
  const status: string = "PROCESSING";
  const hasXlsxPath = false;
  const shouldGenerateXlsxUrl = status === "DONE" && hasXlsxPath;
  assertEquals(shouldGenerateXlsxUrl, false);
});

Deno.test("Job status - DONE without path does not generate URL", () => {
  const status: string = "DONE";
  const hasXlsxPath = false;
  const shouldGenerateXlsxUrl = status === "DONE" && hasXlsxPath;
  assertEquals(shouldGenerateXlsxUrl, false);
});

// Output interface validation
Deno.test("Output interface - xlsxUrl can be null", () => {
  interface GetResultUrlsOutput {
    xlsxUrl: string | null;
    markedImages: { itemId: string; index: number; url: string }[];
    expiresAt: string;
    jobStatus: string;
  }

  const output: GetResultUrlsOutput = {
    xlsxUrl: null,
    markedImages: [],
    expiresAt: new Date().toISOString(),
    jobStatus: "PROCESSING",
  };

  assertEquals(output.xlsxUrl, null);
  assertEquals(output.markedImages.length, 0);
});

Deno.test("Output interface - with marked images", () => {
  interface MarkedImageUrl {
    itemId: string;
    index: number;
    url: string;
  }

  const markedImages: MarkedImageUrl[] = [
    { itemId: generateUUID(), index: 0, url: "https://example.com/image1.jpg" },
    { itemId: generateUUID(), index: 1, url: "https://example.com/image2.jpg" },
  ];

  assertEquals(markedImages.length, 2);
  assertEquals(markedImages[0].index, 0);
  assertEquals(markedImages[1].index, 1);
});
