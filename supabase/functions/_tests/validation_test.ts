// Tests for shared validation utilities
// Tests input validation schemas and error handling

import {
  assertEquals,
  assertExists,
  setupTestEnv,
  createMockRequest,
} from "./test_helpers.ts";
import { z } from "https://deno.land/x/zod@v3.23.8/mod.ts";
import { parseBody, ValidationError, validateAnswerString } from "../_shared/validation.ts";

// Setup environment before tests
setupTestEnv();

Deno.test("parseBody - valid JSON body", async () => {
  const schema = z.object({
    name: z.string(),
    count: z.number(),
  });

  const request = createMockRequest("POST", { name: "test", count: 5 });
  const result = await parseBody(request, schema);

  assertEquals(result.name, "test");
  assertEquals(result.count, 5);
});

Deno.test("parseBody - invalid JSON throws ValidationError", async () => {
  const schema = z.object({
    name: z.string(),
    count: z.number(),
  });

  const request = new Request("http://localhost/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "invalid json{",
  });

  try {
    await parseBody(request, schema);
    throw new Error("Should have thrown");
  } catch (error) {
    assertExists(error);
    assertEquals((error as ValidationError).code, "VALIDATION_ERROR");
  }
});

Deno.test("parseBody - missing required field throws ValidationError", async () => {
  const schema = z.object({
    name: z.string(),
    count: z.number(),
  });

  const request = createMockRequest("POST", { name: "test" }); // missing count

  try {
    await parseBody(request, schema);
    throw new Error("Should have thrown");
  } catch (error) {
    assertExists(error);
    assertEquals((error as ValidationError).code, "VALIDATION_ERROR");
    assertExists((error as ValidationError).details);
  }
});

Deno.test("parseBody - wrong content-type throws ValidationError", async () => {
  const schema = z.object({ name: z.string() });

  const request = new Request("http://localhost/test", {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: JSON.stringify({ name: "test" }),
  });

  try {
    await parseBody(request, schema);
    throw new Error("Should have thrown");
  } catch (error) {
    assertExists(error);
    assertEquals((error as ValidationError).code, "VALIDATION_ERROR");
  }
});

Deno.test("validateAnswerString - valid answers for 4 alternatives", () => {
  const result = validateAnswerString("ABCDABCD", 8, 4);
  assertEquals(result.valid, true);
  assertEquals(result.error, undefined);
});

Deno.test("validateAnswerString - valid answers for 5 alternatives", () => {
  const result = validateAnswerString("ABCDEABCDE", 10, 5);
  assertEquals(result.valid, true);
  assertEquals(result.error, undefined);
});

Deno.test("validateAnswerString - wrong length", () => {
  const result = validateAnswerString("ABCD", 10, 4);
  assertEquals(result.valid, false);
  assertExists(result.error);
});

Deno.test("validateAnswerString - invalid character for 4 alternatives", () => {
  const result = validateAnswerString("ABCDE", 5, 4); // E is invalid for 4 alternatives
  assertEquals(result.valid, false);
  assertExists(result.error);
});

Deno.test("validateAnswerString - case insensitive", () => {
  const result = validateAnswerString("abcd", 4, 4);
  assertEquals(result.valid, true);
});

Deno.test("ValidationError - has correct properties", () => {
  const error = new ValidationError("Test error", [
    { field: "name", message: "required" },
  ]);

  assertEquals(error.code, "VALIDATION_ERROR");
  assertEquals(error.statusCode, 400);
  assertEquals(error.message, "Test error");
  assertExists(error.details);
  assertEquals(error.details?.length, 1);
});
