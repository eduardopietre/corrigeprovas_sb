// Test helpers for Edge Functions testing
// These utilities help create mock requests and validate responses

import { assertEquals, assertExists, assertStringIncludes } from "https://deno.land/std@0.208.0/assert/mod.ts";

export { assertEquals, assertExists, assertStringIncludes };

// Mock environment variables for testing
export function setupTestEnv() {
  Deno.env.set("SUPABASE_URL", "http://localhost:54321");
  Deno.env.set("SUPABASE_ANON_KEY", "test-anon-key");
  Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key");
  Deno.env.set("STRIPE_SECRET_KEY", "sk_test_mock");
  Deno.env.set("STRIPE_WEBHOOK_SECRET", "whsec_test_mock");
}

// Create a mock request with JSON body
export function createMockRequest(
  method: string,
  body?: unknown,
  headers?: Record<string, string>
): Request {
  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-jwt-token",
  };

  const mergedHeaders = { ...defaultHeaders, ...headers };

  return new Request("http://localhost:54321/functions/v1/test", {
    method,
    headers: mergedHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });
}

// Create a mock request without auth
export function createUnauthenticatedRequest(
  method: string,
  body?: unknown
): Request {
  return new Request("http://localhost:54321/functions/v1/test", {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

// Create a mock OPTIONS request for CORS
export function createCorsRequest(): Request {
  return new Request("http://localhost:54321/functions/v1/test", {
    method: "OPTIONS",
  });
}

// Parse JSON response
export async function parseJsonResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(`Failed to parse JSON response: ${text}`);
  }
}

// Assert response has CORS headers
export function assertCorsHeaders(response: Response) {
  assertExists(response.headers.get("Access-Control-Allow-Origin"));
  assertExists(response.headers.get("Access-Control-Allow-Headers"));
  assertExists(response.headers.get("Access-Control-Allow-Methods"));
}

// Assert error response format
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export function assertErrorResponse(
  response: ErrorResponse,
  expectedCode: string
) {
  assertExists(response.error);
  assertEquals(response.error.code, expectedCode);
  assertExists(response.error.message);
}

// Generate a valid UUID for testing
export function generateUUID(): string {
  return crypto.randomUUID();
}

// Mock Supabase client response
export interface MockSupabaseResponse<T> {
  data: T | null;
  error: { code: string; message: string } | null;
}

// Create mock Supabase client for unit testing
export function createMockSupabaseClient() {
  return {
    auth: {
      getUser: async () => ({
        data: { user: { id: generateUUID(), email: "test@example.com" } },
        error: null,
      }),
    },
    from: (table: string) => ({
      select: (columns?: string) => ({
        eq: (column: string, value: unknown) => ({
          single: async () => ({ data: null, error: null }),
          order: (col: string, opts?: { ascending: boolean }) => ({
            data: [],
            error: null,
          }),
        }),
        not: (column: string, operator: string, value: unknown) => ({
          order: (col: string, opts?: { ascending: boolean }) => ({
            data: [],
            error: null,
          }),
        }),
      }),
      insert: (data: unknown) => ({
        select: (columns?: string) => ({
          single: async () => ({ data: { id: generateUUID() }, error: null }),
        }),
      }),
      update: (data: unknown) => ({
        eq: (column: string, value: unknown) => ({
          data: null,
          error: null,
        }),
      }),
      delete: () => ({
        eq: (column: string, value: unknown) => ({
          data: null,
          error: null,
        }),
      }),
      upsert: (data: unknown, opts?: { onConflict: string }) => ({
        data: null,
        error: null,
      }),
    }),
    storage: {
      from: (bucket: string) => ({
        createSignedUploadUrl: async (path: string) => ({
          data: {
            signedUrl: `https://storage.test/${bucket}/${path}?token=test`,
            token: "test-token",
          },
          error: null,
        }),
        createSignedUrl: async (path: string, expiresIn: number) => ({
          data: {
            signedUrl: `https://storage.test/${bucket}/${path}?token=test`,
          },
          error: null,
        }),
      }),
    },
    rpc: async (fn: string, params: Record<string, unknown>) => ({
      data: true,
      error: null,
    }),
  };
}
