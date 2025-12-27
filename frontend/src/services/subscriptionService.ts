/**
 * SubscriptionService - Manages plans and subscriptions
 * Requirements: 10.1, 10.2, 10.5
 */

import { supabase } from '@/lib/supabase'

export interface Plan {
    id: string
    name: string
    description: string
    monthlyPriceCents: number
    monthlyTokens: number
    isActive: boolean
    features: string[]
}

export interface Subscription {
    id: string
    userId: string
    planId: string
    status: 'ACTIVE' | 'PAST_DUE' | 'CANCELED'
    currentPeriodEnd: string
    provider: string
    providerSubscriptionId: string
}

export interface SubscriptionWithPlan extends Subscription {
    plan: Plan
}

/**
 * Fetches all active plans
 */
export async function getPlans(): Promise<Plan[]> {
    const { data, error } = await supabase
        .from('plans')
        .select('*')
        .eq('is_active', true)
        .order('monthly_price_cents')

    if (error) {
        console.error('Failed to fetch plans:', error)
        return []
    }

    return data.map(p => ({
        id: p.id,
        name: p.name || p.id,
        description: p.description || '',
        monthlyPriceCents: p.monthly_price_cents,
        monthlyTokens: p.monthly_tokens,
        isActive: p.is_active,
        features: p.features || [],
    }))
}

/**
 * Fetches the current user's subscription
 */
export async function getCurrentSubscription(userId: string): Promise<SubscriptionWithPlan | null> {
    const { data, error } = await supabase
        .from('subscriptions')
        .select(`
            *,
            plans (*)
        `)
        .eq('user_id', userId)
        .in('status', ['ACTIVE', 'PAST_DUE'])
        .single()

    if (error || !data) {
        return null
    }

    const plan = data.plans as any

    return {
        id: data.id,
        userId: data.user_id,
        planId: data.plan_id,
        status: data.status,
        currentPeriodEnd: data.current_period_end,
        provider: data.provider,
        providerSubscriptionId: data.provider_subscription_id,
        plan: {
            id: plan.id,
            name: plan.name || plan.id,
            description: plan.description || '',
            monthlyPriceCents: plan.monthly_price_cents,
            monthlyTokens: plan.monthly_tokens,
            isActive: plan.is_active,
            features: plan.features || [],
        },
    }
}

/**
 * Creates a Stripe Checkout session for a plan
 */
export async function createCheckoutSession(planId: string): Promise<string | null> {
    const { data, error } = await supabase.functions.invoke('create-checkout-session', {
        body: { planId },
    })

    if (error || !data?.url) {
        console.error('Failed to create checkout session:', error)
        return null
    }

    return data.url
}

/**
 * Creates a Stripe Customer Portal session
 */
export async function createPortalSession(): Promise<string | null> {
    const { data, error } = await supabase.functions.invoke('create-portal-session', {
        body: {},
    })

    if (error || !data?.url) {
        console.error('Failed to create portal session:', error)
        return null
    }

    return data.url
}

/**
 * Formats price in cents to display string
 */
export function formatPrice(cents: number): string {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    }).format(cents / 100)
}

export interface SubscriptionService {
    getPlans: typeof getPlans
    getCurrentSubscription: typeof getCurrentSubscription
    createCheckoutSession: typeof createCheckoutSession
    createPortalSession: typeof createPortalSession
    formatPrice: typeof formatPrice
}

export const subscriptionService: SubscriptionService = {
    getPlans,
    getCurrentSubscription,
    createCheckoutSession,
    createPortalSession,
    formatPrice,
}

export default subscriptionService
