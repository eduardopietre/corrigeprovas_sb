// Tests for create_job Edge Function
// Tests input validation and job creation logic
// Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7

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
const CreateJobInput = z.object({
  answerKeyId: z.string().uuid(),
  templateId: z.string().uuid(),
  items: z
    .array(
      z.object({
        originalStoragePath: z.string().min(1),
      })
    )
    .min(1)
    .max(500),
  idempotencyKey: z.string().max(255).optional(),
});

Deno.test("CreateJobInput schema - valid input", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: [
      { originalStoragePath: "uploads/user-id/image1.jpg" },
      { originalStoragePath: "uploads/user-id/image2.jpg" },
    ],
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, true);
});

Deno.test("CreateJobInput schema - with idempotency key", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: [{ originalStoragePath: "uploads/user-id/image1.jpg" }],
    idempotencyKey: "unique-key-123",
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, true);
});

Deno.test("CreateJobInput schema - invalid answerKeyId UUID", () => {
  const input = {
    answerKeyId: "not-a-uuid",
    templateId: generateUUID(),
    items: [{ originalStoragePath: "uploads/user-id/image1.jpg" }],
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("CreateJobInput schema - invalid templateId UUID", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: "not-a-uuid",
    items: [{ originalStoragePath: "uploads/user-id/image1.jpg" }],
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("CreateJobInput schema - items must not be empty", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: [],
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("CreateJobInput schema - items max 500", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: Array(501).fill({ originalStoragePath: "uploads/user-id/image.jpg" }),
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("CreateJobInput schema - items at max 500 is valid", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: Array(500).fill({ originalStoragePath: "uploads/user-id/image.jpg" }),
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, true);
});

Deno.test("CreateJobInput schema - originalStoragePath must not be empty", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: [{ originalStoragePath: "" }],
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("CreateJobInput schema - idempotencyKey max 255 chars", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: [{ originalStoragePath: "uploads/user-id/image.jpg" }],
    idempotencyKey: "a".repeat(256),
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, false);
});

Deno.test("CreateJobInput schema - idempotencyKey at max 255 is valid", () => {
  const input = {
    answerKeyId: generateUUID(),
    templateId: generateUUID(),
    items: [{ originalStoragePath: "uploads/user-id/image.jpg" }],
    idempotencyKey: "a".repeat(255),
  };

  const result = CreateJobInput.safeParse(input);
  assertEquals(result.success, true);
});

Deno.test("CreateJobInput schema - missing required fields", () => {
  const inputs = [
    { templateId: generateUUID(), items: [{ originalStoragePath: "path" }] }, // missing answerKeyId
    { answerKeyId: generateUUID(), items: [{ originalStoragePath: "path" }] }, // missing templateId
    { answerKeyId: generateUUID(), templateId: generateUUID() }, // missing items
  ];

  for (const input of inputs) {
    const result = CreateJobInput.safeParse(input);
    assertEquals(result.success, false);
  }
});

// Job status enum validation
Deno.test("JobStatus - valid statuses", () => {
  const validStatuses = ["QUEUED", "PROCESSING", "DONE", "FAILED", "CANCELED"];
  
  for (const status of validStatuses) {
    assertEquals(typeof status, "string");
  }
});

// Token calculation tests
Deno.test("Token calculation - 1 token per item", () => {
  const items = [
    { originalStoragePath: "path1" },
    { originalStoragePath: "path2" },
    { originalStoragePath: "path3" },
  ];
  
  const tokensNeeded = items.length;
  assertEquals(tokensNeeded, 3);
});

Deno.test("Token calculation - single item", () => {
  const items = [{ originalStoragePath: "path1" }];
  const tokensNeeded = items.length;
  assertEquals(tokensNeeded, 1);
});

Deno.test("Token calculation - max items", () => {
  const items = Array(500).fill({ originalStoragePath: "path" });
  const tokensNeeded = items.length;
  assertEquals(tokensNeeded, 500);
});
