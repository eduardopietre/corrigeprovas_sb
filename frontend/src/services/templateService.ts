import { supabase } from '@/lib/supabase'
import type { ApiResponse, Template } from './types'

export interface TemplateService {
    list(): Promise<ApiResponse<Template[]>>
    getById(id: string): Promise<ApiResponse<Template>>
}

export const templateService: TemplateService = {
    /**
     * List all active templates
     */
    async list(): Promise<ApiResponse<Template[]>> {
        const { data, error } = await supabase
            .from('templates')
            .select('*')
            .eq('is_active', true)
            .order('question_count', { ascending: true })

        if (error) {
            return {
                error: {
                    code: error.code,
                    message: error.message,
                },
            }
        }

        return { data: data as Template[] }
    },

    /**
     * Get a template by ID
     */
    async getById(id: string): Promise<ApiResponse<Template>> {
        const { data, error } = await supabase
            .from('templates')
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

        return { data: data as Template }
    },
}
