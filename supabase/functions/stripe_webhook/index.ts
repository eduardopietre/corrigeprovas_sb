// Edge Function: stripe_webhook
// Processes Stripe webhook events for subscription management
// Requirements: 10.3, 10.4

import Stripe from "https://esm.sh/stripe@14.14.0?target=deno";
import { createServiceClient } from "../_shared/supabase.ts";
import {
  AppError,
  ErrorCode,
  createErrorResponse,
  createSuccessResponse,
} from "../_shared/errors.ts";
import { corsHeaders } from "../_shared/cors.ts";

// Initialize Stripe
const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") ?? "", {
  apiVersion: "2023-10-16",
  httpClient: Stripe.createFetchHttpClient(),
});

const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";

// Supported event types
type SupportedEventType =
  | "customer.subscription.created"
  | "customer.subscription.updated"
  | "customer.subscription.deleted"
  | "invoice.paid"
  | "invoice.payment_failed";

const SUPPORTED_EVENTS: SupportedEventType[] = [
  "customer.subscription.created",
  "customer.subscription.updated",
  "customer.subscription.deleted",
  "invoice.paid",
  "invoice.payment_failed",
];

// Processed events table for idempotency
const PROCESSED_EVENTS_TABLE = "stripe_processed_events";

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Only allow POST
    if (req.method !== "POST") {
      throw new AppError(
        ErrorCode.VALIDATION_ERROR,
        "Method not allowed. Use POST."
      );
    }

    // Get raw body for signature verification
    const body = await req.text();
    const signature = req.headers.get("stripe-signature");

    if (!signature) {
      throw new AppError(
        ErrorCode.STRIPE_SIGNATURE_ERROR,
        "Missing Stripe signature header"
      );
    }

    // Verify webhook signature
    let event: Stripe.Event;
    try {
      event = await stripe.webhooks.constructEventAsync(
        body,
        signature,
        webhookSecret
      );
    } catch (err) {
      console.error("Webhook signature verification failed:", err);
      throw new AppError(
        ErrorCode.STRIPE_SIGNATURE_ERROR,
        "Invalid Stripe signature"
      );
    }

    // Check if event type is supported
    if (!SUPPORTED_EVENTS.includes(event.type as SupportedEventType)) {
      // Acknowledge but don't process unsupported events
      return createSuccessResponse({ received: true, processed: false });
    }

    // Create service client for database operations
    const supabase = createServiceClient();

    // Check idempotency - has this event been processed?
    const alreadyProcessed = await checkEventProcessed(supabase, event.id);
    if (alreadyProcessed) {
      console.log(`Event ${event.id} already processed, skipping`);
      return createSuccessResponse({ received: true, processed: false, reason: "duplicate" });
    }

    // Process the event
    await processEvent(supabase, event);

    // Mark event as processed
    await markEventProcessed(supabase, event.id, event.type);

    return createSuccessResponse({ received: true, processed: true });

  } catch (error) {
    console.error("Webhook error:", error);
    return createErrorResponse(error);
  }
});

// Check if event has already been processed
async function checkEventProcessed(
  supabase: ReturnType<typeof createServiceClient>,
  eventId: string
): Promise<boolean> {
  const { data, error } = await supabase
    .from(PROCESSED_EVENTS_TABLE)
    .select("id")
    .eq("event_id", eventId)
    .single();

  if (error && error.code !== "PGRST116") {
    console.error("Error checking processed events:", error);
  }

  return !!data;
}

// Mark event as processed
async function markEventProcessed(
  supabase: ReturnType<typeof createServiceClient>,
  eventId: string,
  eventType: string
): Promise<void> {
  const { error } = await supabase
    .from(PROCESSED_EVENTS_TABLE)
    .insert({
      event_id: eventId,
      event_type: eventType,
      processed_at: new Date().toISOString(),
    });

  if (error) {
    console.error("Error marking event as processed:", error);
    // Don't throw - event was processed successfully
  }
}

// Process Stripe event
async function processEvent(
  supabase: ReturnType<typeof createServiceClient>,
  event: Stripe.Event
): Promise<void> {
  switch (event.type) {
    case "customer.subscription.created":
      await handleSubscriptionCreated(supabase, event.data.object as Stripe.Subscription);
      break;

    case "customer.subscription.updated":
      await handleSubscriptionUpdated(supabase, event.data.object as Stripe.Subscription);
      break;

    case "customer.subscription.deleted":
      await handleSubscriptionDeleted(supabase, event.data.object as Stripe.Subscription);
      break;

    case "invoice.paid":
      await handleInvoicePaid(supabase, event.data.object as Stripe.Invoice);
      break;

    case "invoice.payment_failed":
      await handleInvoicePaymentFailed(supabase, event.data.object as Stripe.Invoice);
      break;

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}

// Handle subscription created
async function handleSubscriptionCreated(
  supabase: ReturnType<typeof createServiceClient>,
  subscription: Stripe.Subscription
): Promise<void> {
  const userId = await getUserIdFromCustomer(supabase, subscription.customer as string);
  if (!userId) {
    console.error("User not found for customer:", subscription.customer);
    return;
  }

  const planId = getPlanIdFromSubscription(subscription);
  const status = mapStripeStatus(subscription.status);

  // Create or update subscription record
  const { error } = await supabase
    .from("subscriptions")
    .upsert({
      user_id: userId,
      plan_id: planId,
      status,
      current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
      provider: "stripe",
      provider_subscription_id: subscription.id,
    }, {
      onConflict: "provider_subscription_id",
    });

  if (error) {
    console.error("Error creating subscription:", error);
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to create subscription");
  }

  console.log(`Subscription created for user ${userId}`);
}

// Handle subscription updated
async function handleSubscriptionUpdated(
  supabase: ReturnType<typeof createServiceClient>,
  subscription: Stripe.Subscription
): Promise<void> {
  const status = mapStripeStatus(subscription.status);
  const planId = getPlanIdFromSubscription(subscription);

  const { error } = await supabase
    .from("subscriptions")
    .update({
      plan_id: planId,
      status,
      current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
    })
    .eq("provider_subscription_id", subscription.id);

  if (error) {
    console.error("Error updating subscription:", error);
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to update subscription");
  }

  console.log(`Subscription ${subscription.id} updated to status ${status}`);
}

// Handle subscription deleted
async function handleSubscriptionDeleted(
  supabase: ReturnType<typeof createServiceClient>,
  subscription: Stripe.Subscription
): Promise<void> {
  const { error } = await supabase
    .from("subscriptions")
    .update({
      status: "CANCELED",
    })
    .eq("provider_subscription_id", subscription.id);

  if (error) {
    console.error("Error canceling subscription:", error);
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to cancel subscription");
  }

  console.log(`Subscription ${subscription.id} canceled`);
}

// Handle invoice paid - credit tokens
async function handleInvoicePaid(
  supabase: ReturnType<typeof createServiceClient>,
  invoice: Stripe.Invoice
): Promise<void> {
  // Only process subscription invoices
  if (!invoice.subscription) {
    return;
  }

  const userId = await getUserIdFromCustomer(supabase, invoice.customer as string);
  if (!userId) {
    console.error("User not found for customer:", invoice.customer);
    return;
  }

  // Get the plan to determine token amount
  const { data: subscription } = await supabase
    .from("subscriptions")
    .select("plan_id")
    .eq("provider_subscription_id", invoice.subscription)
    .single();

  if (!subscription) {
    console.error("Subscription not found:", invoice.subscription);
    return;
  }

  const { data: plan } = await supabase
    .from("plans")
    .select("monthly_tokens")
    .eq("id", subscription.plan_id)
    .single();

  if (!plan) {
    console.error("Plan not found:", subscription.plan_id);
    return;
  }

  // Credit tokens using the database function
  const { error } = await supabase.rpc("credit_tokens", {
    p_user_id: userId,
    p_amount: plan.monthly_tokens,
    p_reason: "PLAN_RENEW",
  });

  if (error) {
    console.error("Error crediting tokens:", error);
    throw new AppError(ErrorCode.INTERNAL_ERROR, "Failed to credit tokens");
  }

  console.log(`Credited ${plan.monthly_tokens} tokens to user ${userId}`);
}

// Handle invoice payment failed
async function handleInvoicePaymentFailed(
  supabase: ReturnType<typeof createServiceClient>,
  invoice: Stripe.Invoice
): Promise<void> {
  if (!invoice.subscription) {
    return;
  }

  // Update subscription status to PAST_DUE
  const { error } = await supabase
    .from("subscriptions")
    .update({
      status: "PAST_DUE",
    })
    .eq("provider_subscription_id", invoice.subscription);

  if (error) {
    console.error("Error updating subscription to PAST_DUE:", error);
  }

  console.log(`Subscription ${invoice.subscription} marked as PAST_DUE`);
}

// Get user ID from Stripe customer ID
async function getUserIdFromCustomer(
  supabase: ReturnType<typeof createServiceClient>,
  customerId: string
): Promise<string | null> {
  // First, try to find by existing subscription
  const { data: subscription } = await supabase
    .from("subscriptions")
    .select("user_id")
    .eq("provider", "stripe")
    .ilike("provider_subscription_id", `%${customerId}%`)
    .single();

  if (subscription) {
    return subscription.user_id;
  }

  // Try to find by customer metadata (if stored)
  // This requires the customer to have metadata.user_id set when created
  try {
    const customer = await stripe.customers.retrieve(customerId);
    if (!customer.deleted && customer.metadata?.user_id) {
      return customer.metadata.user_id;
    }
    // Also check email match
    if (!customer.deleted && customer.email) {
      const { data: profile } = await supabase
        .from("profiles")
        .select("user_id")
        .eq("email", customer.email)
        .single();
      
      if (profile) {
        return profile.user_id;
      }
    }
  } catch (err) {
    console.error("Error retrieving Stripe customer:", err);
  }

  return null;
}

// Get plan ID from Stripe subscription
function getPlanIdFromSubscription(subscription: Stripe.Subscription): string {
  // Get the price ID from the first item
  const priceId = subscription.items.data[0]?.price?.id;
  
  // Map Stripe price ID to our plan ID
  // This mapping should be configured via environment variables or database
  const priceToPlanMap: Record<string, string> = {
    // Add your Stripe price IDs here
    // e.g., "price_xxx": "basic",
  };

  return priceToPlanMap[priceId || ""] || priceId || "default";
}

// Map Stripe subscription status to our status
function mapStripeStatus(stripeStatus: Stripe.Subscription.Status): "ACTIVE" | "PAST_DUE" | "CANCELED" {
  switch (stripeStatus) {
    case "active":
    case "trialing":
      return "ACTIVE";
    case "past_due":
    case "unpaid":
      return "PAST_DUE";
    case "canceled":
    case "incomplete":
    case "incomplete_expired":
    case "paused":
    default:
      return "CANCELED";
  }
}
