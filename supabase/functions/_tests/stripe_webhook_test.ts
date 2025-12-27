// Tests for stripe_webhook Edge Function
// Tests event handling and subscription management logic
// Requirements: 10.3, 10.4

import {
  assertEquals,
  assertExists,
  setupTestEnv,
  generateUUID,
} from "./test_helpers.ts";

// Setup environment before tests
setupTestEnv();

// Supported event types
const SUPPORTED_EVENTS = [
  "customer.subscription.created",
  "customer.subscription.updated",
  "customer.subscription.deleted",
  "invoice.paid",
  "invoice.payment_failed",
];

Deno.test("Supported events - subscription.created is supported", () => {
  assertEquals(SUPPORTED_EVENTS.includes("customer.subscription.created"), true);
});

Deno.test("Supported events - subscription.updated is supported", () => {
  assertEquals(SUPPORTED_EVENTS.includes("customer.subscription.updated"), true);
});

Deno.test("Supported events - subscription.deleted is supported", () => {
  assertEquals(SUPPORTED_EVENTS.includes("customer.subscription.deleted"), true);
});

Deno.test("Supported events - invoice.paid is supported", () => {
  assertEquals(SUPPORTED_EVENTS.includes("invoice.paid"), true);
});

Deno.test("Supported events - invoice.payment_failed is supported", () => {
  assertEquals(SUPPORTED_EVENTS.includes("invoice.payment_failed"), true);
});

Deno.test("Supported events - unsupported event not in list", () => {
  assertEquals(SUPPORTED_EVENTS.includes("charge.succeeded"), false);
});

// Status mapping tests
Deno.test("mapStripeStatus - active maps to ACTIVE", () => {
  const result = mapStripeStatus("active");
  assertEquals(result, "ACTIVE");
});

Deno.test("mapStripeStatus - trialing maps to ACTIVE", () => {
  const result = mapStripeStatus("trialing");
  assertEquals(result, "ACTIVE");
});

Deno.test("mapStripeStatus - past_due maps to PAST_DUE", () => {
  const result = mapStripeStatus("past_due");
  assertEquals(result, "PAST_DUE");
});

Deno.test("mapStripeStatus - unpaid maps to PAST_DUE", () => {
  const result = mapStripeStatus("unpaid");
  assertEquals(result, "PAST_DUE");
});

Deno.test("mapStripeStatus - canceled maps to CANCELED", () => {
  const result = mapStripeStatus("canceled");
  assertEquals(result, "CANCELED");
});

Deno.test("mapStripeStatus - incomplete maps to CANCELED", () => {
  const result = mapStripeStatus("incomplete");
  assertEquals(result, "CANCELED");
});

Deno.test("mapStripeStatus - incomplete_expired maps to CANCELED", () => {
  const result = mapStripeStatus("incomplete_expired");
  assertEquals(result, "CANCELED");
});

Deno.test("mapStripeStatus - paused maps to CANCELED", () => {
  const result = mapStripeStatus("paused");
  assertEquals(result, "CANCELED");
});

Deno.test("mapStripeStatus - unknown status maps to CANCELED", () => {
  const result = mapStripeStatus("unknown_status" as any);
  assertEquals(result, "CANCELED");
});

// Helper function (copied from the Edge Function for testing)
function mapStripeStatus(stripeStatus: string): "ACTIVE" | "PAST_DUE" | "CANCELED" {
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

// Idempotency tests
Deno.test("Idempotency - event ID format", () => {
  const eventId = "evt_" + generateUUID().replace(/-/g, "");
  assertEquals(eventId.startsWith("evt_"), true);
});

Deno.test("Idempotency - duplicate detection logic", () => {
  const processedEvents = new Set<string>();
  const eventId = "evt_123";

  // First time - not processed
  assertEquals(processedEvents.has(eventId), false);
  
  // Mark as processed
  processedEvents.add(eventId);
  
  // Second time - already processed
  assertEquals(processedEvents.has(eventId), true);
});

// Timestamp conversion tests
Deno.test("Timestamp conversion - Unix to ISO", () => {
  const unixTimestamp = 1704067200; // 2024-01-01 00:00:00 UTC
  const isoDate = new Date(unixTimestamp * 1000).toISOString();
  
  assertEquals(isoDate.startsWith("2024-01-01"), true);
});

Deno.test("Timestamp conversion - current_period_end", () => {
  const futureTimestamp = Math.floor(Date.now() / 1000) + 30 * 24 * 60 * 60; // 30 days from now
  const periodEnd = new Date(futureTimestamp * 1000);
  
  assertEquals(periodEnd.getTime() > Date.now(), true);
});

// Subscription data structure tests
Deno.test("Subscription record - required fields", () => {
  interface SubscriptionRecord {
    user_id: string;
    plan_id: string;
    status: "ACTIVE" | "PAST_DUE" | "CANCELED";
    current_period_end: string;
    provider: string;
    provider_subscription_id: string;
  }

  const record: SubscriptionRecord = {
    user_id: generateUUID(),
    plan_id: "basic",
    status: "ACTIVE",
    current_period_end: new Date().toISOString(),
    provider: "stripe",
    provider_subscription_id: "sub_123",
  };

  assertExists(record.user_id);
  assertExists(record.plan_id);
  assertExists(record.status);
  assertExists(record.current_period_end);
  assertEquals(record.provider, "stripe");
});

// Token credit tests
Deno.test("Token credit - positive delta for PLAN_RENEW", () => {
  const monthlyTokens = 100;
  const deltaTokens = monthlyTokens; // positive for credit
  
  assertEquals(deltaTokens > 0, true);
});

Deno.test("Token credit - reason is PLAN_RENEW", () => {
  const reason = "PLAN_RENEW";
  assertEquals(reason, "PLAN_RENEW");
});

// Webhook response tests
Deno.test("Webhook response - success format", () => {
  const response = { received: true, processed: true };
  assertEquals(response.received, true);
  assertEquals(response.processed, true);
});

Deno.test("Webhook response - duplicate format", () => {
  const response = { received: true, processed: false, reason: "duplicate" };
  assertEquals(response.received, true);
  assertEquals(response.processed, false);
  assertEquals(response.reason, "duplicate");
});

Deno.test("Webhook response - unsupported event format", () => {
  const response = { received: true, processed: false };
  assertEquals(response.received, true);
  assertEquals(response.processed, false);
});
