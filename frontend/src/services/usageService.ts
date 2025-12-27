/**
 * UsageService - Manages token usage and balance
 * Requirements: 9.4
 */

import { supabase } from '@/lib/supabase'

export type UsageReason = 'CORRECTION_JOB' | 'PLAN_RENEW' | 'JOB_FAILED_REFUND' | 'ADMIN_ADJUSTMENT'

export interface UsageLedgerEntry {
    id: string
    userId: string
    deltaTokens: number
    reason: UsageReason
    jobId: string | null
    createdAt: string
}

export interface UsageStats {
    balance: number
    totalUsed: number
    totalCredits: number
    entriesThisMonth: number
}

/**
 * Gets the current token balance for a user
 */
export async function getBalance(userId: string): Promise<number> {
    const { data, error } = await supabase
        .rpc('get_balance', { p_user_id: userId })

    if (error) {
        console.error('Failed to get balance:', error)
        // Fallback: calculate from ledger
        return calculateBalanceFromLedger(userId)
    }

    return data || 0
}

/**
 * Calculates balance from ledger entries (fallback)
 */
async function calculateBalanceFromLedger(userId: string): Promise<number> {
    const { data, error } = await supabase
        .from('usage_ledger')
        .select('delta_tokens')
        .eq('user_id', userId)

    if (error || !data) {
        return 0
    }

    return data.reduce((sum, entry) => sum + entry.delta_tokens, 0)
}

/**
 * Gets usage statistics for a user
 */
export async function getUsageStats(userId: string): Promise<UsageStats> {
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1).toISOString()

    const { data, error } = await supabase
        .from('usage_ledger')
        .select('delta_tokens, created_at')
        .eq('user_id', userId)

    if (error || !data) {
        return {
            balance: 0,
            totalUsed: 0,
            totalCredits: 0,
            entriesThisMonth: 0,
        }
    }

    let balance = 0
    let totalUsed = 0
    let totalCredits = 0
    let entriesThisMonth = 0

    for (const entry of data) {
        balance += entry.delta_tokens

        if (entry.delta_tokens < 0) {
            totalUsed += Math.abs(entry.delta_tokens)
        } else {
            totalCredits += entry.delta_tokens
        }

        if (entry.created_at >= startOfMonth) {
            entriesThisMonth++
        }
    }

    return {
        balance,
        totalUsed,
        totalCredits,
        entriesThisMonth,
    }
}

/**
 * Gets usage history for a user with pagination
 */
export async function getUsageHistory(
    userId: string,
    page: number = 1,
    pageSize: number = 20
): Promise<{ entries: UsageLedgerEntry[]; total: number }> {
    const from = (page - 1) * pageSize
    const to = from + pageSize - 1

    // Get total count
    const { count } = await supabase
        .from('usage_ledger')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', userId)

    // Get paginated entries
    const { data, error } = await supabase
        .from('usage_ledger')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .range(from, to)

    if (error || !data) {
        return { entries: [], total: 0 }
    }

    const entries: UsageLedgerEntry[] = data.map(e => ({
        id: e.id,
        userId: e.user_id,
        deltaTokens: e.delta_tokens,
        reason: e.reason as UsageReason,
        jobId: e.job_id,
        createdAt: e.created_at,
    }))

    return { entries, total: count || 0 }
}

/**
 * Gets a human-readable label for a usage reason
 */
export function getReasonLabel(reason: UsageReason): string {
    switch (reason) {
        case 'CORRECTION_JOB':
            return 'Correção de Provas'
        case 'PLAN_RENEW':
            return 'Renovação de Plano'
        case 'JOB_FAILED_REFUND':
            return 'Reembolso (Falha)'
        case 'ADMIN_ADJUSTMENT':
            return 'Ajuste Administrativo'
        default:
            return reason
    }
}

export interface UsageService {
    getBalance: typeof getBalance
    getUsageStats: typeof getUsageStats
    getUsageHistory: typeof getUsageHistory
    getReasonLabel: typeof getReasonLabel
}

export const usageService: UsageService = {
    getBalance,
    getUsageStats,
    getUsageHistory,
    getReasonLabel,
}

export default usageService
