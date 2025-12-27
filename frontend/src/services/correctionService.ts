import { supabase } from '@/lib/supabase'
import type { RealtimeChannel } from '@supabase/supabase-js'
import type {
    ApiResponse,
    CorrectionJob,
    CreateJobParams,
    CreateJobResponse,
    GetResultUrlsResponse,
    GetUploadUrlsResponse,
} from './types'

const FUNCTIONS_URL = import.meta.env.VITE_SUPABASE_URL + '/functions/v1'

async function callEdgeFunction<T>(
    functionName: string,
    body: Record<string, unknown>,
    options?: { idempotencyKey?: string }
): Promise<ApiResponse<T>> {
    const { data: { session } } = await supabase.auth.getSession()

    if (!session) {
        return {
            error: {
                code: 'UNAUTHORIZED',
                message: 'Authentication required',
            },
        }
    }

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
    }

    if (options?.idempotencyKey) {
        headers['x-idempotency-key'] = options.idempotencyKey
    }

    try {
        const response = await fetch(`${FUNCTIONS_URL}/${functionName}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
        })

        const result = await response.json()

        if (!response.ok) {
            return {
                error: result.error || {
                    code: 'UNKNOWN_ERROR',
                    message: 'An unknown error occurred',
                },
            }
        }

        return { data: result.data || result }
    } catch (error) {
        console.error(`Error calling ${functionName}:`, error)
        return {
            error: {
                code: 'NETWORK_ERROR',
                message: 'Failed to connect to server',
            },
        }
    }
}

export interface CorrectionService {
    getUploadUrls(count: number, contentTypes: string[]): Promise<ApiResponse<GetUploadUrlsResponse>>
    createJob(params: CreateJobParams): Promise<ApiResponse<CreateJobResponse>>
    getResultUrls(jobId: string): Promise<ApiResponse<GetResultUrlsResponse>>
    subscribeToJob(jobId: string, callback: (job: CorrectionJob) => void): RealtimeChannel
    unsubscribeFromJob(channel: RealtimeChannel): void
    getJob(jobId: string): Promise<ApiResponse<CorrectionJob>>
    listJobs(): Promise<ApiResponse<CorrectionJob[]>>
}

export const correctionService: CorrectionService = {
    /**
     * Get signed URLs for uploading images
     */
    async getUploadUrls(
        count: number,
        contentTypes: string[]
    ): Promise<ApiResponse<GetUploadUrlsResponse>> {
        return callEdgeFunction<GetUploadUrlsResponse>('get_upload_urls', {
            count,
            contentTypes,
        })
    },

    /**
     * Create a new correction job
     */
    async createJob(params: CreateJobParams): Promise<ApiResponse<CreateJobResponse>> {
        return callEdgeFunction<CreateJobResponse>(
            'create_job',
            {
                answerKeyId: params.answerKeyId,
                templateId: params.templateId,
                items: params.items,
            },
            { idempotencyKey: params.idempotencyKey }
        )
    },

    /**
     * Get signed URLs for downloading results
     */
    async getResultUrls(jobId: string): Promise<ApiResponse<GetResultUrlsResponse>> {
        return callEdgeFunction<GetResultUrlsResponse>('get_result_urls', {
            jobId,
        })
    },

    /**
     * Subscribe to real-time updates for a job
     */
    subscribeToJob(jobId: string, callback: (job: CorrectionJob) => void): RealtimeChannel {
        const channel = supabase
            .channel(`job:${jobId}`)
            .on(
                'postgres_changes',
                {
                    event: 'UPDATE',
                    schema: 'public',
                    table: 'correction_jobs',
                    filter: `id=eq.${jobId}`,
                },
                (payload) => {
                    callback(payload.new as CorrectionJob)
                }
            )
            .subscribe()

        return channel
    },

    /**
     * Unsubscribe from job updates
     */
    unsubscribeFromJob(channel: RealtimeChannel): void {
        supabase.removeChannel(channel)
    },

    /**
     * Get a single job by ID
     */
    async getJob(jobId: string): Promise<ApiResponse<CorrectionJob>> {
        const { data, error } = await supabase
            .from('correction_jobs')
            .select('*')
            .eq('id', jobId)
            .single()

        if (error) {
            return {
                error: {
                    code: error.code,
                    message: error.message,
                },
            }
        }

        return { data: data as CorrectionJob }
    },

    /**
     * List all jobs for the current user
     */
    async listJobs(): Promise<ApiResponse<CorrectionJob[]>> {
        const { data, error } = await supabase
            .from('correction_jobs')
            .select('*')
            .order('created_at', { ascending: false })

        if (error) {
            return {
                error: {
                    code: error.code,
                    message: error.message,
                },
            }
        }

        return { data: data as CorrectionJob[] }
    },
}
