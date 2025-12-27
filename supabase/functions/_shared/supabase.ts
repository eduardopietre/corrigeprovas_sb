// Shared Supabase client configuration for Edge Functions
import { createClient, SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.47.10";

// Types for database entities
export type JobStatus = "QUEUED" | "PROCESSING" | "DONE" | "FAILED" | "CANCELED";
export type UserRole = "USER" | "ADMIN" | "INSTITUTION_ADMIN";
export type SubscriptionStatus = "ACTIVE" | "PAST_DUE" | "CANCELED";
export type UsageReason = "CORRECTION_JOB" | "PLAN_RENEW" | "JOB_FAILED_REFUND" | "ADMIN_ADJUSTMENT";

export interface Profile {
  user_id: string;
  email: string;
  display_name: string | null;
  institution_id: string | null;
  created_at: string;
}

export interface Template {
  id: string;
  name: string;
  question_count: number;
  alternatives_count: number;
  version: number;
  template_storage_path: string;
  is_active: boolean;
  created_at: string;
}

export interface AnswerKey {
  id: string;
  owner_user_id: string;
  institution_id: string | null;
  exam_id: string | null;
  template_id: string;
  answers_string: string;
  name: string | null;
  created_at: string;
}

export interface CorrectionJob {
  id: string;
  owner_user_id: string;
  institution_id: string | null;
  answer_key_id: string;
  template_id: string;
  status: JobStatus;
  total_items: number;
  success_items: number;
  error_items: number;
  elapsed_ms: number | null;
  xlsx_storage_path: string | null;
  idempotency_key: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface CorrectionItem {
  id: string;
  job_id: string;
  index: number;
  original_storage_path: string;
  marked_storage_path: string | null;
  identifier: string | null;
  detected_answers: string | null;
  correct_count: number | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan_id: string;
  status: SubscriptionStatus;
  current_period_end: string;
  provider: string;
  provider_subscription_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Plan {
  id: string;
  monthly_price_cents: number;
  monthly_tokens: number;
  is_active: boolean;
  created_at: string;
}

// Create Supabase client with user's JWT (for RLS)
export function createUserClient(req: Request): SupabaseClient {
  const authHeader = req.headers.get("Authorization");
  
  return createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_ANON_KEY") ?? "",
    {
      global: {
        headers: authHeader ? { Authorization: authHeader } : {},
      },
    }
  );
}

// Create Supabase client with service role (bypasses RLS)
export function createServiceClient(): SupabaseClient {
  return createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
    {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    }
  );
}

// Get authenticated user from request
export async function getUser(req: Request) {
  const client = createUserClient(req);
  const { data: { user }, error } = await client.auth.getUser();
  
  if (error || !user) {
    return null;
  }
  
  return user;
}
