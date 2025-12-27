// Tests for CORS handling utilities
// Tests CORS preflight and header management

import {
  assertEquals,
  assertExists,
  setupTestEnv,
} from "./test_helpers.ts";
import { corsHeaders, handleCors, withCors } from "../_shared/cors.ts";

// Setup environment before tests
setupTestEnv();

Deno.test("corsHeaders - contains required headers", () => {
  assertExists(corsHeaders["Access-Control-Allow-Origin"]);
  assertExists(corsHeaders["Access-Control-Allow-Headers"]);
  assertExists(corsHeaders["Access-Control-Allow-Methods"]);
});

Deno.test("corsHeaders - allows all origins", () => {
  assertEquals(corsHeaders["Access-Control-Allow-Origin"], "*");
});

Deno.test("corsHeaders - allows required headers", () => {
  const allowedHeaders = corsHeaders["Access-Control-Allow-Headers"];
  assertEquals(allowedHeaders.includes("authorization"), true);
  assertEquals(allowedHeaders.includes("content-type"), true);
  assertEquals(allowedHeaders.includes("apikey"), true);
});

Deno.test("corsHeaders - allows required methods", () => {
  const allowedMethods = corsHeaders["Access-Control-Allow-Methods"];
  assertEquals(allowedMethods.includes("POST"), true);
  assertEquals(allowedMethods.includes("GET"), true);
  assertEquals(allowedMethods.includes("OPTIONS"), true);
});

Deno.test("handleCors - returns response for OPTIONS", () => {
  const request = new Request("http://localhost/test", { method: "OPTIONS" });
  const response = handleCors(request);

  assertExists(response);
  assertEquals(response?.status, 200);
});

Deno.test("handleCors - OPTIONS response has CORS headers", () => {
  const request = new Request("http://localhost/test", { method: "OPTIONS" });
  const response = handleCors(request);

  assertExists(response);
  assertExists(response?.headers.get("Access-Control-Allow-Origin"));
  assertExists(response?.headers.get("Access-Control-Allow-Headers"));
  assertExists(response?.headers.get("Access-Control-Allow-Methods"));
});

Deno.test("handleCors - returns null for GET", () => {
  const request = new Request("http://localhost/test", { method: "GET" });
  const response = handleCors(request);

  assertEquals(response, null);
});

Deno.test("handleCors - returns null for POST", () => {
  const request = new Request("http://localhost/test", { method: "POST" });
  const response = handleCors(request);

  assertEquals(response, null);
});

Deno.test("withCors - adds headers to response", () => {
  const original = new Response("test body", {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

  const corsResponse = withCors(original);

  assertEquals(corsResponse.status, 200);
  assertExists(corsResponse.headers.get("Access-Control-Allow-Origin"));
  assertExists(corsResponse.headers.get("Access-Control-Allow-Headers"));
  assertExists(corsResponse.headers.get("Access-Control-Allow-Methods"));
  assertEquals(corsResponse.headers.get("Content-Type"), "application/json");
});

Deno.test("withCors - preserves original status", () => {
  const original = new Response("created", { status: 201 });
  const corsResponse = withCors(original);

  assertEquals(corsResponse.status, 201);
});

Deno.test("withCors - preserves original body", async () => {
  const original = new Response("test body", { status: 200 });
  const corsResponse = withCors(original);

  const body = await corsResponse.text();
  assertEquals(body, "test body");
});

Deno.test("withCors - preserves error status", () => {
  const original = new Response("error", { status: 400 });
  const corsResponse = withCors(original);

  assertEquals(corsResponse.status, 400);
});
