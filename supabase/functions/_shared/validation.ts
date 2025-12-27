// Shared validation utilities using Zod
import { z } from "https://deno.land/x/zod@v3.23.8/mod.ts";

// Re-export Zod for use in Edge Functions
export { z };

// Common validation schemas
export const uuidSchema = z.string().uuid();

export const contentTypeSchema = z.enum([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/tiff",
  "application/pdf",
]);

// Validate and parse request body with Zod schema
export async function parseBody<T extends z.ZodType>(
  req: Request,
  schema: T
): Promise<z.infer<T>> {
  const contentType = req.headers.get("content-type");
  
  if (!contentType?.includes("application/json")) {
    throw new ValidationError("Content-Type must be application/json");
  }
  
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    throw new ValidationError("Invalid JSON body");
  }
  
  const result = schema.safeParse(body);
  
  if (!result.success) {
    const errors = result.error.errors.map((e) => ({
      field: e.path.join("."),
      message: e.message,
    }));
    throw new ValidationError("Validation failed", errors);
  }
  
  return result.data;
}

// Custom validation error class
export class ValidationError extends Error {
  public readonly code = "VALIDATION_ERROR";
  public readonly statusCode = 400;
  public readonly details?: Array<{ field: string; message: string }>;
  
  constructor(
    message: string,
    details?: Array<{ field: string; message: string }>
  ) {
    super(message);
    this.name = "ValidationError";
    this.details = details;
  }
}

// Validate answer string format
export function validateAnswerString(
  answers: string,
  questionCount: number,
  alternativesCount: number
): { valid: boolean; error?: string } {
  if (answers.length !== questionCount) {
    return {
      valid: false,
      error: `Answer string length must be ${questionCount}, got ${answers.length}`,
    };
  }
  
  const validChars = "ABCDE".slice(0, alternativesCount);
  const regex = new RegExp(`^[${validChars}]+$`, "i");
  
  if (!regex.test(answers)) {
    return {
      valid: false,
      error: `Answer string must only contain characters ${validChars}`,
    };
  }
  
  return { valid: true };
}
