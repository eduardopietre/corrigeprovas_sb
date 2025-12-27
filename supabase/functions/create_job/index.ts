// Edge Function: create_job
// Creates a correction job, reserves tokens, and publishes to queue
// Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7

import { z } from "https://deno.land/x/zod@v3.23.8/mod.ts";
import { handleCors, withCors } from "../_shared/cors.ts";
import {
  AppError,
  ErrorCode,
  createErrorResponse,
  createSuccessResponse,
} from "../_shared/errors.ts";
import {
  createServiceClient,
  createUserClient,
  getUser,
  type AnswerKey,
  type CorrectionJob,
  type Template,
} from "../_shared/supabase.ts";
import { parseBody } from "../_shared/validation.ts";

// Input validation schema
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

type CreateJobInputType = z.infer<typeof CreateJobInput>;

// Output interface
interface CreateJobOutput {
  jobId: string;
  status: "QUEUED";
  totalItems: number;
  tokensReserved: number;
}

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
    const input = await parseBody(req, CreateJobInput);

    // Validate storage paths in items
    for (let i = 0; i < input.items.length; i++) {
      const item = input.items[i];
      try {
        validateStoragePath(item.originalStoragePath);
      } catch (error) {
        if (error instanceof SecurityError) {
          throw new AppError(
            ErrorCode.VALIDATION_ERROR,
            `Invalid storage path in item ${i}: ${error.message}`,
            { index: i, path: item.originalStoragePath }
          );
        }
        throw error;
      }
    }

    // Get idempotency key from header or body
    const idempotencyKey =
      req.headers.get("x-idempotency-key") || input.idempotencyKey;

    // Validate idempotency key format if provided
    if (idempotencyKey && !validateIdempotencyKey(idempotencyKey)) {
      throw new AppError(
        ErrorCode.VALIDATION_ERROR,
        "Invalid idempotency key format. Must be 1-255 characters, alphanumeric, hyphens, and underscores only.",
        { idempotencyKey }
      );
    }

    // Create clients
    const userClient = createUserClient(req);
    const serviceClient = createServiceClient();

    // Check for existing job with same idempotency key
    if (idempotencyKey) {
      const existingJob = await checkIdempotencyKey(
        serviceClient,
        idempotencyKey,
        user.id,
        input
      );
      if (existingJob) {
        return withCors(
          createSuccessResponse<CreateJobOutput>({
            jobId: existingJob.id,
            status: "QUEUED",
            totalItems: existingJob.total_items,
            tokensReserved: existingJob.total_items,
          })
        );
      }
    }

    // Validate answer key ownership via RLS
    const answerKey = await validateAnswerKey(
      userClient,
      input.answerKeyId,
      user.id
    );

    // Validate template exists and is active
    const template = await validateTemplate(userClient, input.templateId);

    // Validate answer key matches template
    if (answerKey.template_id !== template.id) {
      throw new AppError(
        ErrorCode.VALIDATION_ERROR,
        "Answer key template does not match specified template",
        {
          answerKeyTemplateId: answerKey.template_id,
          specifiedTemplateId: template.id,
        }
      );
    }

    // Get user's profile for institution_id
    const { data: profile } = await userClient
      .from("profiles")
      .select("institution_id")
      .eq("user_id", user.id)
      .single();

    const institutionId = profile?.institution_id || null;

    // Calculate tokens needed (1 token per item)
    const tokensNeeded = input.items.length;

    // Create job and reserve tokens in a transaction using service client
    const result = await createJobTransaction(
      serviceClient,
      user.id,
      institutionId,
      input,
      tokensNeeded,
      idempotencyKey
    );

    // Publish message to queue
    await publishToQueue(serviceClient, result.jobId);

    const response: CreateJobOutput = {
      jobId: result.jobId,
      status: "QUEUED",
      totalItems: input.items.length,
      tokensReserved: tokensNeeded,
    };

    return withCors(createSuccessResponse(response, 201));
  } catch (error) {
    return withCors(createErrorResponse(error));
  }
});

// Check if idempotency key already exists
async function checkIdempotencyKey(
  client: ReturnType<typeof createServiceClient>,
  idempotencyKey: string,
  userId: string,
  input: CreateJobInputType
): Promise<CorrectionJob | null> {
  const { data: existingJob, error } = await client
    .from("correction_jobs")
    .select("*")
    .eq("idempotency_key", idempotencyKey)
    .single();

  if (error && error.code !== "PGRST116") {
    // PGRST116 = no rows returned
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to check idempotency key");
  }

  if (existingJob) {
    // Verify the existing job matches the current request
    if (
      existingJob.owner_user_id !== userId ||
      existingJob.answer_key_id !== input.answerKeyId ||
      existingJob.template_id !== input.templateId ||
      existingJob.total_items !== input.items.length
    ) {
      throw new AppError(
        ErrorCode.IDEMPOTENCY_CONFLICT,
        "Idempotency key already used with different parameters"
      );
    }
    return existingJob as CorrectionJob;
  }

  return null;
}

// Validate answer key ownership
async function validateAnswerKey(
  client: ReturnType<typeof createUserClient>,
  answerKeyId: string,
  userId: string
): Promise<AnswerKey> {
  const { data: answerKey, error } = await client
    .from("answer_keys")
    .select("*")
    .eq("id", answerKeyId)
    .single();

  if (error || !answerKey) {
    throw new AppError(
      ErrorCode.NOT_FOUND,
      "Answer key not found or access denied",
      { answerKeyId }
    );
  }

  return answerKey as AnswerKey;
}

// Validate template exists and is active
async function validateTemplate(
  client: ReturnType<typeof createUserClient>,
  templateId: string
): Promise<Template> {
  const { data: template, error } = await client
    .from("templates")
    .select("*")
    .eq("id", templateId)
    .eq("is_active", true)
    .single();

  if (error || !template) {
    throw new AppError(ErrorCode.NOT_FOUND, "Template not found or inactive", {
      templateId,
    });
  }

  return template as Template;
}

// Create job and items in a transaction
async function createJobTransaction(
  client: ReturnType<typeof createServiceClient>,
  userId: string,
  institutionId: string | null,
  input: CreateJobInputType,
  tokensNeeded: number,
  idempotencyKey?: string
): Promise<{ jobId: string }> {
  // First, create the job to get its ID
  const { data: job, error: jobError } = await client
    .from("correction_jobs")
    .insert({
      owner_user_id: userId,
      institution_id: institutionId,
      answer_key_id: input.answerKeyId,
      template_id: input.templateId,
      status: "QUEUED",
      total_items: input.items.length,
      idempotency_key: idempotencyKey || null,
    })
    .select("id")
    .single();

  if (jobError || !job) {
    console.error("Error creating job:", jobError);
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to create correction job");
  }

  const jobId = job.id;

  // Reserve tokens using the database function
  const { data: tokenResult, error: tokenError } = await client.rpc(
    "reserve_tokens",
    {
      p_user_id: userId,
      p_amount: tokensNeeded,
      p_job_id: jobId,
    }
  );

  if (tokenError) {
    // Rollback: delete the job
    await client.from("correction_jobs").delete().eq("id", jobId);
    console.error("Error reserving tokens:", tokenError);
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to reserve tokens");
  }

  if (tokenResult === false) {
    // Insufficient balance - rollback
    await client.from("correction_jobs").delete().eq("id", jobId);
    throw new AppError(
      ErrorCode.INSUFFICIENT_TOKENS,
      "Insufficient token balance",
      { required: tokensNeeded }
    );
  }

  // Create correction items
  const items = input.items.map((item, index) => ({
    job_id: jobId,
    index,
    original_storage_path: item.originalStoragePath,
  }));

  const { error: itemsError } = await client
    .from("correction_items")
    .insert(items);

  if (itemsError) {
    // Rollback: delete job (cascade will delete items, and we need to refund tokens)
    await client.from("correction_jobs").delete().eq("id", jobId);
    // Note: tokens are already debited, but job deletion should trigger cleanup
    console.error("Error creating items:", itemsError);
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to create correction items");
  }

  return { jobId };
}

// Publish job to the corrections queue
async function publishToQueue(
  client: ReturnType<typeof createServiceClient>,
  jobId: string
): Promise<void> {
  // Use pgmq to send message to the corrections queue
  // The queue should be created via migration
  const { error } = await client.rpc("pgmq_send", {
    queue_name: "corrections",
    message: { job_id: jobId },
  });

  if (error) {
    console.error("Error publishing to queue:", error);
    // Don't fail the request - the job is created, worker can poll for QUEUED jobs
    // This is a graceful degradation
    console.warn("Queue publish failed, job will be picked up by polling");
  }
}
