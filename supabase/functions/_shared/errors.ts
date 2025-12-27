// Shared error handling utilities for Edge Functions

// Error codes enum
export enum ErrorCode {
  VALIDATION_ERROR = "VALIDATION_ERROR",
  UNAUTHORIZED = "UNAUTHORIZED",
  FORBIDDEN = "FORBIDDEN",
  NOT_FOUND = "NOT_FOUND",
  INSUFFICIENT_TOKENS = "INSUFFICIENT_TOKENS",
  IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT",
  INTERNAL_ERROR = "INTERNAL_ERROR",
  STRIPE_SIGNATURE_ERROR = "STRIPE_SIGNATURE_ERROR",
}

// HTTP status codes for each error
const errorStatusCodes: Record<ErrorCode, number> = {
  [ErrorCode.VALIDATION_ERROR]: 400,
  [ErrorCode.UNAUTHORIZED]: 401,
  [ErrorCode.FORBIDDEN]: 403,
  [ErrorCode.NOT_FOUND]: 404,
  [ErrorCode.INSUFFICIENT_TOKENS]: 402,
  [ErrorCode.IDEMPOTENCY_CONFLICT]: 409,
  [ErrorCode.INTERNAL_ERROR]: 500,
  [ErrorCode.STRIPE_SIGNATURE_ERROR]: 400,
};

// Application error class
export class AppError extends Error {
  public readonly code: ErrorCode;
  public readonly statusCode: number;
  public readonly details?: Record<string, unknown>;

  constructor(
    code: ErrorCode,
    message: string,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "AppError";
    this.code = code;
    this.statusCode = errorStatusCodes[code];
    this.details = details;
  }
}

// Error response interface
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

// Create error response
export function createErrorResponse(error: unknown): Response {
  if (error instanceof AppError) {
    const body: ErrorResponse = {
      error: {
        code: error.code,
        message: error.message,
        details: error.details,
      },
    };
    return new Response(JSON.stringify(body), {
      status: error.statusCode,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Handle validation errors from validation.ts
  if (
    error instanceof Error &&
    "code" in error &&
    (error as { code: string }).code === "VALIDATION_ERROR"
  ) {
    const validationError = error as Error & {
      code: string;
      statusCode: number;
      details?: Array<{ field: string; message: string }>;
    };
    const body: ErrorResponse = {
      error: {
        code: validationError.code,
        message: validationError.message,
        details: validationError.details
          ? { fields: validationError.details }
          : undefined,
      },
    };
    return new Response(JSON.stringify(body), {
      status: validationError.statusCode,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Generic error
  console.error("Unhandled error:", error);
  const body: ErrorResponse = {
    error: {
      code: ErrorCode.INTERNAL_ERROR,
      message: "An unexpected error occurred",
    },
  };
  return new Response(JSON.stringify(body), {
    status: 500,
    headers: { "Content-Type": "application/json" },
  });
}

// Create success response
export function createSuccessResponse<T>(data: T, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// CORS headers for Edge Functions
export const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-idempotency-key",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
};

// Handle CORS preflight
export function handleCors(req: Request): Response | null {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  return null;
}

// Wrap response with CORS headers
export function withCors(response: Response): Response {
  const newHeaders = new Headers(response.headers);
  Object.entries(corsHeaders).forEach(([key, value]) => {
    newHeaders.set(key, value);
  });
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}
