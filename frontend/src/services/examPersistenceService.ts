/**
 * ExamPersistenceService - Persists exam data to Supabase database
 * Requirements: 12.2, 12.3
 */

import { supabase } from '@/lib/supabase'
import type {
    Exam,
    ExamConfig,
    ExamQuestion,
    ExamVariantResult
} from './examBuilderTypes'

export interface SaveExamResult {
    examId: string
    questionIds: string[]
    variantIds: string[]
}

/**
 * Saves an exam configuration to the database
 */
export async function saveExam(
    config: ExamConfig,
    userId: string,
    institutionId?: string | null
): Promise<SaveExamResult> {
    // Start a transaction by using multiple operations
    // Note: Supabase doesn't support true transactions in the client,
    // so we'll do our best with sequential operations

    // 1. Create the exam record
    const { data: examData, error: examError } = await supabase
        .from('exams')
        .insert({
            owner_user_id: userId,
            institution_id: institutionId || null,
            name: config.name,
            shuffle_questions: config.shuffleQuestions,
            shuffle_alternatives: config.shuffleAlternatives,
            variant_count: config.variantCount,
            seed: config.seed || null,
        })
        .select('id')
        .single()

    if (examError || !examData) {
        throw new Error(`Failed to create exam: ${examError?.message}`)
    }

    const examId = examData.id
    const questionIds: string[] = []

    // 2. Create questions and their images/alternatives
    for (const question of config.questions) {
        // Create question
        const { data: questionData, error: questionError } = await supabase
            .from('exam_questions')
            .insert({
                exam_id: examId,
                index: question.index,
                text: question.text,
                correct_alternative_index: question.correctAlternativeIndex,
            })
            .select('id')
            .single()

        if (questionError || !questionData) {
            throw new Error(`Failed to create question: ${questionError?.message}`)
        }

        const questionId = questionData.id
        questionIds.push(questionId)

        // Create question images
        if (question.images.length > 0) {
            const questionImages = question.images.map(img => ({
                question_id: questionId,
                storage_path: img.storagePath,
                position: img.position,
                width: img.width || null,
                height: img.height || null,
            }))

            const { error: imagesError } = await supabase
                .from('question_images')
                .insert(questionImages)

            if (imagesError) {
                console.error('Failed to create question images:', imagesError)
            }
        }

        // Create alternatives
        for (const alternative of question.alternatives) {
            const { data: altData, error: altError } = await supabase
                .from('exam_alternatives')
                .insert({
                    question_id: questionId,
                    index: alternative.index,
                    text: alternative.text,
                })
                .select('id')
                .single()

            if (altError || !altData) {
                console.error('Failed to create alternative:', altError)
                continue
            }

            // Create alternative image if exists
            if (alternative.image) {
                const { error: altImgError } = await supabase
                    .from('alternative_images')
                    .insert({
                        alternative_id: altData.id,
                        storage_path: alternative.image.storagePath,
                        width: alternative.image.width || null,
                        height: alternative.image.height || null,
                    })

                if (altImgError) {
                    console.error('Failed to create alternative image:', altImgError)
                }
            }
        }
    }

    return {
        examId,
        questionIds,
        variantIds: [],
    }
}

/**
 * Saves exam variants to the database
 */
export async function saveVariants(
    examId: string,
    variants: ExamVariantResult[],
    docxStoragePaths?: Map<string, string>
): Promise<string[]> {
    const variantIds: string[] = []

    for (const variant of variants) {
        const qrcodePayload = JSON.stringify({
            examId,
            model: variant.modelIdentifier,
            variantIndex: variant.variantIndex,
        })

        const docxPath = docxStoragePaths?.get(variant.modelIdentifier) || null

        // Create variant
        const { data: variantData, error: variantError } = await supabase
            .from('exam_variants')
            .insert({
                exam_id: examId,
                variant_index: variant.variantIndex,
                model_identifier: variant.modelIdentifier,
                question_order: variant.questionOrder,
                alternative_orders: variant.alternativeOrders,
                qrcode_payload: qrcodePayload,
                docx_storage_path: docxPath,
            })
            .select('id')
            .single()

        if (variantError || !variantData) {
            throw new Error(`Failed to create variant: ${variantError?.message}`)
        }

        const variantId = variantData.id
        variantIds.push(variantId)

        // Create variant answer key
        const { error: answerKeyError } = await supabase
            .from('variant_answer_keys')
            .insert({
                variant_id: variantId,
                answers_string: variant.answerKey,
            })

        if (answerKeyError) {
            console.error('Failed to create variant answer key:', answerKeyError)
        }
    }

    return variantIds
}

/**
 * Loads an exam from the database
 */
export async function loadExam(examId: string): Promise<ExamConfig | null> {
    // Load exam
    const { data: examData, error: examError } = await supabase
        .from('exams')
        .select('*')
        .eq('id', examId)
        .single()

    if (examError || !examData) {
        console.error('Failed to load exam:', examError)
        return null
    }

    // Load questions
    const { data: questionsData, error: questionsError } = await supabase
        .from('exam_questions')
        .select('*')
        .eq('exam_id', examId)
        .order('index')

    if (questionsError || !questionsData) {
        console.error('Failed to load questions:', questionsError)
        return null
    }

    const questions: ExamQuestion[] = []

    for (const q of questionsData) {
        // Load question images
        const { data: imagesData } = await supabase
            .from('question_images')
            .select('*')
            .eq('question_id', q.id)
            .order('position')

        // Load alternatives
        const { data: alternativesData } = await supabase
            .from('exam_alternatives')
            .select('*')
            .eq('question_id', q.id)
            .order('index')

        const alternatives = []
        for (const alt of alternativesData || []) {
            // Load alternative image
            const { data: altImageData } = await supabase
                .from('alternative_images')
                .select('*')
                .eq('alternative_id', alt.id)
                .single()

            alternatives.push({
                id: alt.id,
                index: alt.index,
                text: alt.text,
                image: altImageData ? {
                    id: altImageData.id,
                    storagePath: altImageData.storage_path,
                    width: altImageData.width,
                    height: altImageData.height,
                } : null,
            })
        }

        questions.push({
            id: q.id,
            index: q.index,
            text: q.text,
            images: (imagesData || []).map(img => ({
                id: img.id,
                storagePath: img.storage_path,
                position: img.position,
                width: img.width,
                height: img.height,
            })),
            alternatives,
            correctAlternativeIndex: q.correct_alternative_index,
        })
    }

    return {
        name: examData.name,
        templateId: '', // Not stored in exam table
        questions,
        shuffleQuestions: examData.shuffle_questions,
        shuffleAlternatives: examData.shuffle_alternatives,
        variantCount: examData.variant_count,
        seed: examData.seed,
    }
}

/**
 * Loads exam variants from the database
 */
export async function loadVariants(examId: string): Promise<ExamVariantResult[]> {
    const { data: variantsData, error: variantsError } = await supabase
        .from('exam_variants')
        .select(`
            *,
            variant_answer_keys (answers_string)
        `)
        .eq('exam_id', examId)
        .order('variant_index')

    if (variantsError || !variantsData) {
        console.error('Failed to load variants:', variantsError)
        return []
    }

    return variantsData.map(v => ({
        variantIndex: v.variant_index,
        modelIdentifier: v.model_identifier,
        questionOrder: v.question_order,
        alternativeOrders: v.alternative_orders,
        answerKey: v.variant_answer_keys?.[0]?.answers_string || '',
    }))
}

/**
 * Deletes an exam and all related data
 */
export async function deleteExam(examId: string): Promise<boolean> {
    // Due to cascading deletes in the database, we only need to delete the exam
    const { error } = await supabase
        .from('exams')
        .delete()
        .eq('id', examId)

    if (error) {
        console.error('Failed to delete exam:', error)
        return false
    }

    return true
}

/**
 * Lists exams for a user
 */
export async function listExams(userId: string): Promise<Exam[]> {
    const { data, error } = await supabase
        .from('exams')
        .select('*')
        .eq('owner_user_id', userId)
        .order('created_at', { ascending: false })

    if (error) {
        console.error('Failed to list exams:', error)
        return []
    }

    return data.map(e => ({
        id: e.id,
        ownerUserId: e.owner_user_id,
        institutionId: e.institution_id,
        name: e.name,
        shuffleQuestions: e.shuffle_questions,
        shuffleAlternatives: e.shuffle_alternatives,
        variantCount: e.variant_count,
        seed: e.seed,
        createdAt: e.created_at,
    }))
}

export interface ExamPersistenceService {
    saveExam: typeof saveExam
    saveVariants: typeof saveVariants
    loadExam: typeof loadExam
    loadVariants: typeof loadVariants
    deleteExam: typeof deleteExam
    listExams: typeof listExams
}

export const examPersistenceService: ExamPersistenceService = {
    saveExam,
    saveVariants,
    loadExam,
    loadVariants,
    deleteExam,
    listExams,
}

export default examPersistenceService
