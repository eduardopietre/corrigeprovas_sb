/**
 * ExamBuilderService - Orchestrates exam creation with multiple variants
 * Requirements: 15.1, 15.5, 15.6
 */

import { generateAnswerKeyString, generateDocx, type DocxGeneratorConfig } from './docxGenerator'
import type { ExamConfig, ExamQuestion, ExamVariantResult } from './examBuilderTypes'
import { generateVariantSeed, indexToLetter, shuffleWithMapping } from './shuffleService'

/**
 * Generates a single exam variant with shuffled questions and alternatives
 */
export function generateVariant(
    questions: ExamQuestion[],
    variantIndex: number,
    shuffleQuestions: boolean,
    shuffleAlternatives: boolean,
    baseSeed: number
): ExamVariantResult {
    const variantSeed = generateVariantSeed(baseSeed, variantIndex)
    const modelIdentifier = indexToLetter(variantIndex)

    // Shuffle questions if enabled
    let questionOrder: number[]
    let orderedQuestions: ExamQuestion[]

    if (shuffleQuestions && questions.length > 1) {
        const questionSeed = generateVariantSeed(variantSeed, 0)
        const result = shuffleWithMapping(questions, questionSeed)
        orderedQuestions = result.shuffled
        questionOrder = result.mapping
    } else {
        orderedQuestions = questions
        questionOrder = questions.map((_, i) => i)
    }

    // Shuffle alternatives for each question if enabled
    const alternativeOrders: number[][] = []

    for (let i = 0; i < orderedQuestions.length; i++) {
        const question = orderedQuestions[i]

        if (shuffleAlternatives && question.alternatives.length > 1) {
            const altSeed = generateVariantSeed(variantSeed, i + 1)
            const result = shuffleWithMapping(question.alternatives, altSeed)
            alternativeOrders.push(result.mapping)
        } else {
            alternativeOrders.push(question.alternatives.map((_, j) => j))
        }
    }

    // Generate answer key for this variant
    const answerKey = generateAnswerKeyString(questions, questionOrder, alternativeOrders)

    return {
        variantIndex,
        modelIdentifier,
        questionOrder,
        alternativeOrders,
        answerKey,
    }
}

/**
 * Generates all variants for an exam
 */
export function generateAllVariants(config: ExamConfig): ExamVariantResult[] {
    const {
        questions,
        shuffleQuestions,
        shuffleAlternatives,
        variantCount,
        seed = Date.now(),
    } = config

    const variants: ExamVariantResult[] = []

    for (let i = 0; i < variantCount; i++) {
        const variant = generateVariant(
            questions,
            i,
            shuffleQuestions,
            shuffleAlternatives,
            seed
        )
        variants.push(variant)
    }

    return variants
}

/**
 * Generates DOCX files for all variants
 */
export async function generateVariantDocx(
    config: ExamConfig,
    variant: ExamVariantResult,
    includeAnswerKey: boolean = false
): Promise<Blob> {
    const docxConfig: DocxGeneratorConfig = {
        title: config.name,
        modelIdentifier: variant.modelIdentifier,
        questions: config.questions,
        questionOrder: variant.questionOrder,
        alternativeOrders: variant.alternativeOrders,
        includeAnswerKey,
    }

    const result = await generateDocx(docxConfig)
    return result.blob
}

/**
 * Generates all DOCX files for all variants
 */
export async function generateAllVariantDocx(
    config: ExamConfig,
    includeAnswerKey: boolean = false,
    onProgress?: (current: number, total: number) => void
): Promise<Map<string, Blob>> {
    const variants = generateAllVariants(config)
    const docxFiles = new Map<string, Blob>()

    for (let i = 0; i < variants.length; i++) {
        const variant = variants[i]
        const blob = await generateVariantDocx(config, variant, includeAnswerKey)
        const filename = `${config.name.replace(/[^a-zA-Z0-9]/g, '_')}_Modelo_${variant.modelIdentifier}.docx`
        docxFiles.set(filename, blob)

        onProgress?.(i + 1, variants.length)
    }

    return docxFiles
}

/**
 * Generates a summary of answer keys for all variants
 */
export function generateAnswerKeySummary(
    config: ExamConfig,
    variants: ExamVariantResult[]
): string {
    let summary = `Gabaritos - ${config.name}\n`
    summary += '='.repeat(40) + '\n\n'

    for (const variant of variants) {
        summary += `Modelo ${variant.modelIdentifier}: ${variant.answerKey}\n`
    }

    summary += '\n' + '='.repeat(40) + '\n'
    summary += `Total de variantes: ${variants.length}\n`
    summary += `Total de questões: ${config.questions.length}\n`
    summary += `Embaralhar questões: ${config.shuffleQuestions ? 'Sim' : 'Não'}\n`
    summary += `Embaralhar alternativas: ${config.shuffleAlternatives ? 'Sim' : 'Não'}\n`

    return summary
}

export interface ExamBuilderService {
    generateVariant: typeof generateVariant
    generateAllVariants: typeof generateAllVariants
    generateVariantDocx: typeof generateVariantDocx
    generateAllVariantDocx: typeof generateAllVariantDocx
    generateAnswerKeySummary: typeof generateAnswerKeySummary
}

export const examBuilderService: ExamBuilderService = {
    generateVariant,
    generateAllVariants,
    generateVariantDocx,
    generateAllVariantDocx,
    generateAnswerKeySummary,
}

export default examBuilderService
