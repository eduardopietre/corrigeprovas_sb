/**
 * DocxGenerator - Generates DOCX documents for exam variants with image support
 * Requirements: 12.1, 16.5
 */

import { supabase } from '@/lib/supabase'
import {
    AlignmentType,
    Document,
    HeadingLevel,
    ImageRun,
    Packer,
    PageBreak,
    Paragraph,
    Table,
    TableCell,
    TableRow,
    TextRun,
    WidthType
} from 'docx'
import type { ExamQuestion } from './examBuilderTypes'

export interface DocxGeneratorConfig {
    title: string
    modelIdentifier: string
    questions: ExamQuestion[]
    questionOrder: number[]
    alternativeOrders: number[][]
    includeAnswerKey: boolean
    headerText?: string
    footerText?: string
}

export interface DocxGeneratorResult {
    blob: Blob
    filename: string
}

/**
 * Fetches an image from Supabase Storage and returns it as a buffer
 */
async function fetchImageFromStorage(storagePath: string): Promise<ArrayBuffer | null> {
    try {
        const { data, error } = await supabase.storage
            .from('exam-images')
            .download(storagePath)

        if (error || !data) {
            console.error('Failed to fetch image:', error)
            return null
        }

        return await data.arrayBuffer()
    } catch (err) {
        console.error('Error fetching image:', err)
        return null
    }
}

/**
 * Converts index to letter (0 = A, 1 = B, etc.)
 */
function indexToLetter(index: number): string {
    return String.fromCharCode(65 + index)
}

/**
 * Creates an ImageRun from image data
 */
function createImageRun(
    imageData: ArrayBuffer,
    width?: number,
    height?: number
): ImageRun {
    // Default dimensions if not provided
    const maxWidth = 400
    const maxHeight = 300

    let finalWidth = width || maxWidth
    let finalHeight = height || maxHeight

    // Scale down if too large while maintaining aspect ratio
    if (finalWidth > maxWidth) {
        const scale = maxWidth / finalWidth
        finalWidth = maxWidth
        finalHeight = Math.round(finalHeight * scale)
    }
    if (finalHeight > maxHeight) {
        const scale = maxHeight / finalHeight
        finalHeight = maxHeight
        finalWidth = Math.round(finalWidth * scale)
    }

    return new ImageRun({
        data: imageData,
        transformation: {
            width: finalWidth,
            height: finalHeight,
        },
        type: 'png', // docx library handles format detection
    })
}

/**
 * Creates paragraphs for a question including images
 */
async function createQuestionParagraphs(
    question: ExamQuestion,
    questionNumber: number,
    alternativeOrder: number[]
): Promise<Paragraph[]> {
    const paragraphs: Paragraph[] = []

    // Question number and text
    paragraphs.push(
        new Paragraph({
            children: [
                new TextRun({
                    text: `${questionNumber}. `,
                    bold: true,
                }),
                new TextRun({
                    text: question.text,
                }),
            ],
            spacing: { before: 200, after: 100 },
        })
    )

    // Question images
    for (const image of question.images) {
        const imageData = await fetchImageFromStorage(image.storagePath)
        if (imageData) {
            paragraphs.push(
                new Paragraph({
                    children: [createImageRun(imageData, image.width, image.height)],
                    alignment: AlignmentType.CENTER,
                    spacing: { before: 100, after: 100 },
                })
            )
        }
    }

    // Alternatives in shuffled order
    for (let newIndex = 0; newIndex < alternativeOrder.length; newIndex++) {
        const originalIndex = alternativeOrder[newIndex]
        const alternative = question.alternatives[originalIndex]
        const letter = indexToLetter(newIndex)

        const children: (TextRun | ImageRun)[] = [
            new TextRun({
                text: `${letter}) `,
                bold: true,
            }),
            new TextRun({
                text: alternative.text,
            }),
        ]

        paragraphs.push(
            new Paragraph({
                children,
                indent: { left: 360 }, // 0.25 inch indent
                spacing: { before: 50, after: 50 },
            })
        )

        // Alternative image (if any)
        if (alternative.image) {
            const imageData = await fetchImageFromStorage(alternative.image.storagePath)
            if (imageData) {
                paragraphs.push(
                    new Paragraph({
                        children: [createImageRun(imageData, alternative.image.width, alternative.image.height)],
                        indent: { left: 720 }, // 0.5 inch indent
                        spacing: { before: 50, after: 50 },
                    })
                )
            }
        }
    }

    return paragraphs
}

/**
 * Creates the answer key table
 */
function createAnswerKeyTable(
    questions: ExamQuestion[],
    questionOrder: number[],
    alternativeOrders: number[][]
): Table {
    const rows: TableRow[] = []

    // Header row
    rows.push(
        new TableRow({
            children: [
                new TableCell({
                    children: [new Paragraph({ children: [new TextRun({ text: 'Questão', bold: true })] })],
                    width: { size: 20, type: WidthType.PERCENTAGE },
                }),
                new TableCell({
                    children: [new Paragraph({ children: [new TextRun({ text: 'Resposta', bold: true })] })],
                    width: { size: 20, type: WidthType.PERCENTAGE },
                }),
            ],
        })
    )

    // Answer rows
    for (let newQuestionIndex = 0; newQuestionIndex < questionOrder.length; newQuestionIndex++) {
        const originalQuestionIndex = questionOrder[newQuestionIndex]
        const question = questions[originalQuestionIndex]
        const alternativeOrder = alternativeOrders[newQuestionIndex]

        // Find where the correct alternative ended up
        const originalCorrectIndex = question.correctAlternativeIndex
        const newCorrectIndex = alternativeOrder.findIndex(orig => orig === originalCorrectIndex)
        const correctLetter = indexToLetter(newCorrectIndex)

        rows.push(
            new TableRow({
                children: [
                    new TableCell({
                        children: [new Paragraph({ children: [new TextRun({ text: `${newQuestionIndex + 1}` })] })],
                    }),
                    new TableCell({
                        children: [new Paragraph({ children: [new TextRun({ text: correctLetter })] })],
                    }),
                ],
            })
        )
    }

    return new Table({
        rows,
        width: { size: 40, type: WidthType.PERCENTAGE },
    })
}

/**
 * Generates a DOCX document for an exam variant
 */
export async function generateDocx(config: DocxGeneratorConfig): Promise<DocxGeneratorResult> {
    const {
        title,
        modelIdentifier,
        questions,
        questionOrder,
        alternativeOrders,
        includeAnswerKey,
        headerText,
        footerText,
    } = config

    const sections: Paragraph[] = []

    // Title
    sections.push(
        new Paragraph({
            children: [
                new TextRun({
                    text: title,
                    bold: true,
                    size: 32, // 16pt
                }),
            ],
            heading: HeadingLevel.HEADING_1,
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 },
        })
    )

    // Model identifier
    sections.push(
        new Paragraph({
            children: [
                new TextRun({
                    text: `Modelo ${modelIdentifier}`,
                    bold: true,
                    size: 24, // 12pt
                }),
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 400 },
        })
    )

    // Header text (if provided)
    if (headerText) {
        sections.push(
            new Paragraph({
                children: [new TextRun({ text: headerText })],
                spacing: { after: 200 },
            })
        )
    }

    // Questions in shuffled order
    for (let newQuestionIndex = 0; newQuestionIndex < questionOrder.length; newQuestionIndex++) {
        const originalQuestionIndex = questionOrder[newQuestionIndex]
        const question = questions[originalQuestionIndex]
        const alternativeOrder = alternativeOrders[newQuestionIndex]

        const questionParagraphs = await createQuestionParagraphs(
            question,
            newQuestionIndex + 1,
            alternativeOrder
        )
        sections.push(...questionParagraphs)
    }

    // Footer text (if provided)
    if (footerText) {
        sections.push(
            new Paragraph({
                children: [new TextRun({ text: footerText })],
                spacing: { before: 400 },
            })
        )
    }

    // Answer key (if requested)
    if (includeAnswerKey) {
        sections.push(
            new Paragraph({
                children: [new PageBreak()],
            })
        )
        sections.push(
            new Paragraph({
                children: [
                    new TextRun({
                        text: `Gabarito - Modelo ${modelIdentifier}`,
                        bold: true,
                        size: 28,
                    }),
                ],
                heading: HeadingLevel.HEADING_2,
                alignment: AlignmentType.CENTER,
                spacing: { after: 200 },
            })
        )
        sections.push(
            new Paragraph({
                children: [createAnswerKeyTable(questions, questionOrder, alternativeOrders)],
            })
        )
    }

    // Create document
    const doc = new Document({
        sections: [
            {
                children: sections,
            },
        ],
    })

    // Generate blob
    const blob = await Packer.toBlob(doc)
    const filename = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_Modelo_${modelIdentifier}.docx`

    return { blob, filename }
}

/**
 * Generates the answer key string for a variant
 */
export function generateAnswerKeyString(
    questions: ExamQuestion[],
    questionOrder: number[],
    alternativeOrders: number[][]
): string {
    let answerKey = ''

    for (let newQuestionIndex = 0; newQuestionIndex < questionOrder.length; newQuestionIndex++) {
        const originalQuestionIndex = questionOrder[newQuestionIndex]
        const question = questions[originalQuestionIndex]
        const alternativeOrder = alternativeOrders[newQuestionIndex]

        // Find where the correct alternative ended up
        const originalCorrectIndex = question.correctAlternativeIndex
        const newCorrectIndex = alternativeOrder.findIndex(orig => orig === originalCorrectIndex)
        answerKey += indexToLetter(newCorrectIndex)
    }

    return answerKey
}

export interface DocxGenerator {
    generate(config: DocxGeneratorConfig): Promise<DocxGeneratorResult>
    generateAnswerKeyString(
        questions: ExamQuestion[],
        questionOrder: number[],
        alternativeOrders: number[][]
    ): string
}

export const docxGenerator: DocxGenerator = {
    generate: generateDocx,
    generateAnswerKeyString,
}

export default docxGenerator
