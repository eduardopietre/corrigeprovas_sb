// Tests for shared error handling utilities
// Tests error response creation and formatting

import {
  assertEquals,
  assertExists,
  setupTestEnv,
  parseJsonResponse,
  ErrorResponse,
} from "./test_helpers.ts";
import {
  AppError,
  ErrorCode,
  createErrorResponse,
  createSuccessResponse,
  handleCors,
  withCors,
} from "../_shared/errors.ts";

// Setup environment before tests
setupTestEnv();

Deno.test("AppError - creates error with correct properties", () => {
  const error = new AppError(
    ErrorCode.VALIDATION_ERROR,
    "Test validation error",
    { field: "name" }
  );

  assertEquals(error.code, ErrorCode.VALIDATION_ERROR);
  assertEquals(error.statusCode, 400);
  assertEquals(error.message, "Test validation error");
  assertExists(error.details);
  assertEquals(error.details?.field, "name");
});

Deno.test("AppError - UNAUTHORIZED has status 401", () => {
  const error = new AppError(ErrorCode.UNAUTHORIZED, "Not authenticated");
  assertEquals(error.statusCode, 401);
});

Deno.test("AppError - FORBIDDEN has status 403", () => {
  const error = new AppError(ErrorCode.FORBIDDEN, "Access denied");
  assertEquals(error.statusCode, 403);
});

Deno.test("AppError - NOT_FOUND has status 404", () => {
  const error = new AppError(ErrorCode.NOT_FOUND, "Resource not found");
  assertEquals(error.statusCode, 404);
});

Deno.test("AppError - INSUFFICIENT_TOKENS has status 402", () => {
  const error = new AppError(ErrorCode.INSUFFICIENT_TOKENS, "Not enough tokens");
  assertEquals(error.statusCode, 402);
});

Deno.test("AppError - INTERNAL_ERROR has status 500", () => {
  const error = new AppError(ErrorCode.INTERNAL_ERROR, "Server error");
  assertEquals(error.statusCode, 500);
});

Deno.test("createErrorResponse - formats AppError correctly", async () => {
  const error = new AppError(
    ErrorCode.VALIDATION_ERROR,
    "Invalid input",
    { field: "email" }
  );

  const response = createErrorResponse(error);
  assertEquals(response.status, 400);

  const body = await parseJsonResponse<ErrorResponse>(response);
  assertEquals(body.error.code, "VALIDATION_ERROR");
  assertEquals(body.error.message, "Invalid input");
  assertExists(body.error.details);
});

Deno.test("createErrorResponse - handles generic Error", async () => {
  const error = new Error("Something went wrong");

  const response = createErrorResponse(error);
  assertEquals(response.status, 500);

  const body = await parseJsonResponse<ErrorResponse>(response);
  assertEquals(body.error.code, "INTERNAL_ERROR");
});

Deno.test("createSuccessResponse - creates JSON response", async () => {
  const data = { id: "123", name: "test" };

  const response = createSuccessResponse(data);
  assertEquals(response.status, 200);
  assertEquals(response.headers.get("Content-Type"), "application/json");

  const body = await parseJsonResponse<typeof data>(response);
  assertEquals(body.id, "123");
  assertEquals(body.name, "test");
});

Deno.test("createSuccessResponse - custom status code", async () => {
  const data = { created: true };

  const response = createSuccessResponse(data, 201);
  assertEquals(response.status, 201);
});

Deno.test("handleCors - returns response for OPTIONS request", () => {
  const request = new Request("http://localhost/test", { method: "OPTIONS" });
  const response = handleCors(request);

  assertExists(response);
  assertEquals(response?.status, 200);
});

Deno.test("handleCors - returns null for non-OPTIONS request", () => {
  const request = new Request("http://localhost/test", { method: "POST" });
  const response = handleCors(request);

  assertEquals(response, null);
});

Deno.test("withCors - adds CORS headers to response", () => {
  const originalResponse = new Response("test", { status: 200 });
  const corsResponse = withCors(originalResponse);

  assertExists(corsResponse.headers.get("Access-Control-Allow-Origin"));
  assertExists(corsResponse.headers.get("Access-Control-Allow-Headers"));
  assertExists(corsResponse.headers.get("Access-Control-Allow-Methods"));
});
