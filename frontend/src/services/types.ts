// Types for the correction service

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'DONE' | 'FAILED' | 'CANCELED'

export interface UploadUrlItem {
    path: string
    signedUrl: string
    token: string
    expiresAt: string
}

export interface GetUploadUrlsResponse {
    urls: UploadUrlItem[]
}

export interface CreateJobParams {
    answerKeyId: string
    templateId: string
    items: { originalStoragePath: string }[]
    idempotencyKey?: string
}

export interface CreateJobResponse {
    jobId: string
    status: 'QUEUED'
    totalItems: number
    tokensReserved: number
}

export interface MarkedImageUrl {
    itemId: string
    index: number
    url: string
}

export interface GetResultUrlsResponse {
    xlsxUrl: string | null
    markedImages: MarkedImageUrl[]
    expiresAt: string
    jobStatus: JobStatus
}

export interface CorrectionJob {
    id: string
    owner_user_id: string
    institution_id: string | null
    answer_key_id: string
    template_id: string
    status: JobStatus
    total_items: number
    success_items: number
    error_items: number
    elapsed_ms: number | null
    xlsx_storage_path: string | null
    created_at: string
    started_at: string | null
    finished_at: string | null
}

export interface CorrectionItem {
    id: string
    job_id: string
    index: number
    original_storage_path: string
    marked_storage_path: string | null
    identifier: string | null
    detected_answers: string | null
    correct_count: number | null
    error_code: string | null
    error_message: string | null
    created_at: string
}

export interface Template {
    id: string
    name: string
    question_count: number
    alternatives_count: number
    version: number
    template_storage_path: string
    is_active: boolean
    created_at: string
}

export interface AnswerKey {
    id: string
    owner_user_id: string
    institution_id: string | null
    exam_id: string | null
    template_id: string
    answers_string: string
    name: string | null
    created_at: string
}

export interface ApiError {
    code: string
    message: string
    details?: Record<string, unknown>
}

export interface ApiResponse<T> {
    data?: T
    error?: ApiError
}
