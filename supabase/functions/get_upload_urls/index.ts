// Edge Function: get_upload_urls
// Generates signed URLs for direct upload to Storage
// Requirements: 4.1, 4.2

import { z } from "zod";
import { createUserClient, getUser } from "../_shared/supabase.ts";
import { parseBody } from "../_shared/validation.ts";
import {
  AppError,
  ErrorCode,
  createErrorResponse,
  createSuccessResponse,
} from "../_shared/errors.ts";
import { handleCors, withCors } from "../_shared/cors.ts";

// Input validation schema
const GetUploadUrlsInput = z.object({
  count: z.number().int().min(1).max(100),
  contentTypes: z.array(
    z.enum(["image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf"])
  ).min(1),
  filenameHints: z.array(z.string()).optional(),
});

// Output interface
interface UploadUrlItem {
  path: string;
  signedUrl: string;
  token: string;
  expiresAt: string;
}

interface GetUploadUrlsOutput {
  urls: UploadUrlItem[];
}

// URL expiration time in seconds (5 minutes)
const URL_EXPIRY_SECONDS = 300;

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  const corsResponse = handleCors(req);
  if (corsResponse) return corsResponse;

  try {
    // Only allow POST
    if (req.method !== "POST") {
      throw new AppError(
        ErrorCode.VALIDATION_ERROR,
        "Method not allowed. Use POST."
      );
    }

    // Get authenticated user
    const user = await getUser(req);
    if (!user) {
      throw new AppError(ErrorCode.UNAUTHORIZED, "Authentication required");
    }

    // Parse and validate input
    const input = await parseBody(req, GetUploadUrlsInput);

    // Validate contentTypes array length matches count
    if (input.contentTypes.length !== input.count) {
      throw new AppError(ErrorCode.VALIDATION_ERROR, "contentTypes array length must match count", {
        expected: input.count,
        received: input.contentTypes.length,
      });
    }

    // Create Supabase client with user context
    const supabase = createUserClient(req);

    // Generate unique paths and signed URLs
    const urls: UploadUrlItem[] = [];
    const timestamp = Date.now();
    const expiresAt = new Date(Date.now() + URL_EXPIRY_SECONDS * 1000).toISOString();

    for (let i = 0; i < input.count; i++) {
      const contentType = input.contentTypes[i];
      const extension = getExtensionFromContentType(contentType);
      const filenameHint = input.filenameHints?.[i];
      
      // Generate unique filename
      const filename = filenameHint
        ? `${sanitizeFilename(filenameHint)}_${timestamp}_${i}${extension}`
        : `upload_${timestamp}_${i}${extension}`;
      
      // Path format: uploads/{uid}/{filename}
      const path = `${user.id}/${filename}`;

      // Create signed upload URL
      const { data, error } = await supabase.storage
        .from("uploads")
        .createSignedUploadUrl(path);

      if (error) {
        console.error("Error creating signed URL:", error);
        throw new AppError(
          ErrorCode.INTERNAL_ERROR,
          "Failed to create upload URL",
          { index: i, error: error.message }
        );
      }

      urls.push({
        path: `uploads/${path}`,
        signedUrl: data.signedUrl,
        token: data.token,
        expiresAt,
      });
    }

    const response: GetUploadUrlsOutput = { urls };
    return withCors(createSuccessResponse(response));

  } catch (error) {
    return withCors(createErrorResponse(error));
  }
});

// Helper: Get file extension from content type
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

// Helper: Sanitize filename to remove special characters
function sanitizeFilename(filename: string): string {
  return filename
    .replace(/[^a-zA-Z0-9_-]/g, "_")
    .substring(0, 50);
}
