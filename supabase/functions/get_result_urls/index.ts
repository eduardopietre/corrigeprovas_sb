// Edge Function: get_result_urls
// Returns signed URLs for downloading correction results
// Requirements: 7.1, 7.2, 7.3, 7.4

import { z } from "https://deno.land/x/zod@v3.23.8/mod.ts";
import {
  createUserClient,
  getUser,
  type CorrectionJob,
  type CorrectionItem,
} from "../_shared/supabase.ts";
import { parseBody } from "../_shared/validation.ts";
import {
  AppError,
  ErrorCode,
  createErrorResponse,
  createSuccessResponse,
} from "../_shared/errors.ts";
import { handleCors, withCors } from "../_shared/cors.ts";

// Input validation schema
const GetResultUrlsInput = z.object({
  jobId: z.string().uuid(),
});

// Output interface
interface MarkedImageUrl {
  itemId: string;
  index: number;
  url: string;
}

interface GetResultUrlsOutput {
  xlsxUrl: string | null;
  markedImages: MarkedImageUrl[];
  expiresAt: string;
  jobStatus: string;
}

// URL expiration time in seconds (1 hour)
const URL_EXPIRY_SECONDS = 3600;

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  const corsResponse = handleCors(req);
  if (corsResponse) return corsResponse;

  try {
    // Allow GET or POST
    if (req.method !== "POST" && req.method !== "GET") {
      throw new AppError(
        ErrorCode.VALIDATION_ERROR,
        "Method not allowed. Use GET or POST."
      );
    }

    // Get authenticated user
    const user = await getUser(req);
    if (!user) {
      throw new AppError(ErrorCode.UNAUTHORIZED, "Authentication required");
    }

    // Parse input from body (POST) or query params (GET)
    let jobId: string;
    
    if (req.method === "POST") {
      const input = await parseBody(req, GetResultUrlsInput);
      jobId = input.jobId;
    } else {
      const url = new URL(req.url);
      const jobIdParam = url.searchParams.get("jobId");
      if (!jobIdParam) {
        throw new AppError(ErrorCode.VALIDATION_ERROR, "jobId query parameter is required");
      }
      const parseResult = z.string().uuid().safeParse(jobIdParam);
      if (!parseResult.success) {
        throw new AppError(ErrorCode.VALIDATION_ERROR, "Invalid jobId format");
      }
      jobId = parseResult.data;
    }

    // Create Supabase client with user context (RLS enforced)
    const supabase = createUserClient(req);

    // Get job with RLS - this validates ownership
    const { data: job, error: jobError } = await supabase
      .from("correction_jobs")
      .select("*")
      .eq("id", jobId)
      .single();

    if (jobError || !job) {
      throw new AppError(
        ErrorCode.NOT_FOUND,
        "Job not found or access denied",
        { jobId }
      );
    }

    const correctionJob = job as CorrectionJob;
    const expiresAt = new Date(Date.now() + URL_EXPIRY_SECONDS * 1000).toISOString();

    // Generate XLSX URL if job is done and has xlsx_storage_path
    let xlsxUrl: string | null = null;
    
    if (correctionJob.status === "DONE" && correctionJob.xlsx_storage_path) {
      const xlsxPath = extractStoragePath(correctionJob.xlsx_storage_path, "results");
      const { data: xlsxData, error: xlsxError } = await supabase.storage
        .from("results")
        .createSignedUrl(xlsxPath, URL_EXPIRY_SECONDS);

      if (xlsxError) {
        console.error("Error creating XLSX signed URL:", xlsxError);
      } else {
        xlsxUrl = xlsxData.signedUrl;
      }
    }

    // Get correction items with marked images
    const { data: items, error: itemsError } = await supabase
      .from("correction_items")
      .select("id, index, marked_storage_path")
      .eq("job_id", jobId)
      .not("marked_storage_path", "is", null)
      .order("index", { ascending: true });

    if (itemsError) {
      console.error("Error fetching correction items:", itemsError);
      throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to fetch correction items");
    }

    // Generate signed URLs for marked images
    const markedImages: MarkedImageUrl[] = [];
    
    for (const item of items || []) {
      if (item.marked_storage_path) {
        const imagePath = extractStoragePath(item.marked_storage_path, "results");
        const { data: imageData, error: imageError } = await supabase.storage
          .from("results")
          .createSignedUrl(imagePath, URL_EXPIRY_SECONDS);

        if (imageError) {
          console.error(`Error creating signed URL for item ${item.id}:`, imageError);
          continue;
        }

        markedImages.push({
          itemId: item.id,
          index: item.index,
          url: imageData.signedUrl,
        });
      }
    }

    const response: GetResultUrlsOutput = {
      xlsxUrl,
      markedImages,
      expiresAt,
      jobStatus: correctionJob.status,
    };

    return withCors(createSuccessResponse(response));

  } catch (error) {
    return withCors(createErrorResponse(error));
  }
});

// Helper: Extract path relative to bucket from full storage path
// e.g., "results/user-id/job-id/file.xlsx" -> "user-id/job-id/file.xlsx"
function extractStoragePath(fullPath: string, bucketName: string): string {
  const prefix = `${bucketName}/`;
  if (fullPath.startsWith(prefix)) {
    return fullPath.substring(prefix.length);
  }
  return fullPath;
}
