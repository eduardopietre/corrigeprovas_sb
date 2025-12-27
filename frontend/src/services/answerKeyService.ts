import { supabase } from '@/lib/supabase'
import type { AnswerKey, ApiResponse, Template } from './types'

export interface CreateAnswerKeyParams {
    templateId: string
    answersString: string
    name?: string
    examId?: string
}

export interface AnswerKeyService {
    create(params: CreateAnswerKeyParams): Promise<ApiResponse<AnswerKey>>
    getById(id: string): Promise<ApiResponse<AnswerKey>>
    list(): Promise<ApiResponse<AnswerKey[]>>
    delete(id: string): Promise<ApiResponse<void>>
    validateAnswersString(answersString: string, template: Template): { valid: boolean; error?: string }
}

export const answerKeyService: AnswerKeyService = {
    /**
     * Create a new answer key
     */
    async create(params: CreateAnswerKeyParams): Promise<ApiResponse<AnswerKey>> {
        const { data: { user } } = await supabase.auth.getUser()

        if (!user) {
            return {
                error: {
                    code: 'UNAUTHORIZED',
                    message: 'Authentication required',
                },
            }
        }

        // Get user's profile for institution_id
        const { data: profile } = await supabase
            .from('profiles')
            .select('institution_id')
            .eq('user_id', user.id)
            .single()

        const { data, error } = await supabase
            .from('answer_keys')
            .insert({
                owner_user_id: user.id,
                institution_id: profile?.institution_id || null,
                template_id: params.templateId,
                answers_string: params.answersString.toUpperCase(),
                name: params.name || null,
                exam_id: params.examId || null,
            })
            .select()
            .single()

        if (error) {
            return {
                error: {
                    code: error.code,
                    message: error.message,
                },
            }
        }

        return { data: data as AnswerKey }
    },

    /**
     * Get an answer key by ID
     */
    async getById(id: string): Promise<ApiResponse<AnswerKey>> {
        const { data, error } = await supabase
            .from('answer_keys')
            .select('*')
            .eq('id', id)
            .single()

        if (error) {
            return {
                error: {
                    code: error.code,
                    message: error.message,
                },
            }
        }

        return { data: data as AnswerKey }
    },

    /**
     * List all answer keys for the current user
     */
    async list(): Promise<ApiResponse<AnswerKey[]>> {
        const { data, error } = await supabase
            .from('answer_keys')
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

        return { data: data as AnswerKey[] }
    },

    /**
     * Delete an answer key
     */
    async delete(id: string): Promise<ApiResponse<void>> {
        const { error } = await supabase
            .from('answer_keys')
            .delete()
            .eq('id', id)

        if (error) {
            return {
                error: {
                    code: error.code,
                    message: error.message,
                },
            }
        }

        return { data: undefined }
    },

    /**
     * Validate answers string against template constraints
     */
    validateAnswersString(answersString: string, template: Template): { valid: boolean; error?: string } {
        const normalized = answersString.toUpperCase().trim()

        // Check length
        if (normalized.length !== template.question_count) {
            return {
                valid: false,
                error: `O gabarito deve ter exatamente ${template.question_count} respostas. Você digitou ${normalized.length}.`,
            }
        }

        // Check valid characters based on alternatives count
        const validChars = 'ABCDE'.slice(0, template.alternatives_count)
        const invalidChars: string[] = []

        for (let i = 0; i < normalized.length; i++) {
            const char = normalized[i]
            if (!validChars.includes(char)) {
                invalidChars.push(`Questão ${i + 1}: "${char}"`)
            }
        }

        if (invalidChars.length > 0) {
            return {
                valid: false,
                error: `Caracteres inválidos encontrados. Use apenas ${validChars.split('').join(', ')}. Erros: ${invalidChars.slice(0, 5).join('; ')}${invalidChars.length > 5 ? '...' : ''}`,
            }
        }

        return { valid: true }
    },
}
