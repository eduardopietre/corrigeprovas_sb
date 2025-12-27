/**
 * Types for the Exam Builder feature
 * Requirements: 12.1, 16.1, 16.2
 */

// Image types for questions and alternatives

/**
 * Represents an image embedded in a question text
 * A question can have multiple images at different positions
 */
export interface QuestionImage {
    id: string
    storagePath: string
    position: number  // Position in the text where the image appears
    width?: number
    height?: number
}

/**
 * Represents an image for an alternative
 * Each alternative can have at most one image
 */
export interface AlternativeImage {
    id: string
    storagePath: string
    width?: number
    height?: number
}

/**
 * Represents an alternative (option) for a question
 */
export interface ExamAlternative {
    id: string
    index: number  // 0-based index (0=A, 1=B, 2=C, etc.)
    text: string
    image: AlternativeImage | null  // At most one image per alternative
}

/**
 * Represents a question in an exam
 */
export interface ExamQuestion {
    id: string
    index: number  // 0-based index of the question
    text: string
    images: QuestionImage[]  // Zero or more images in the question text
    alternatives: ExamAlternative[]
    correctAlternativeIndex: number  // 0-based index of the correct alternative
}

/**
 * Configuration for creating an exam with variants
 */
export interface ExamConfig {
    name: string
    templateId: string
    questions: ExamQuestion[]
    shuffleQuestions: boolean
    shuffleAlternatives: boolean
    variantCount: number  // 1-26 variants
    seed?: number  // Seed for deterministic randomization
}

/**
 * Result of generating a single exam variant
 */
export interface ExamVariantResult {
    variantIndex: number
    modelIdentifier: string  // "A", "B", "C", etc.
    questionOrder: number[]  // Mapping: new position -> original question index
    alternativeOrders: number[][]  // For each question: new position -> original alternative index
    answerKey: string  // Answer key adjusted for this variant (e.g., "ABCDE...")
    docxBlob?: Blob  // Generated DOCX file
}

/**
 * Persisted exam entity (matches database schema)
 */
export interface Exam {
    id: string
    ownerUserId: string
    institutionId: string | null
    name: string
    shuffleQuestions: boolean
    shuffleAlternatives: boolean
    variantCount: number
    seed: number | null
    createdAt: string
}

/**
 * Persisted exam question entity (matches database schema)
 */
export interface PersistedExamQuestion {
    id: string
    examId: string
    index: number
    text: string
    correctAlternativeIndex: number
    createdAt: string
}

/**
 * Persisted question image entity (matches database schema)
 */
export interface PersistedQuestionImage {
    id: string
    questionId: string
    storagePath: string
    position: number
    width: number | null
    height: number | null
    createdAt: string
}

/**
 * Persisted exam alternative entity (matches database schema)
 */
export interface PersistedExamAlternative {
    id: string
    questionId: string
    index: number
    text: string
    createdAt: string
}

/**
 * Persisted alternative image entity (matches database schema)
 */
export interface PersistedAlternativeImage {
    id: string
    alternativeId: string
    storagePath: string
    width: number | null
    height: number | null
    createdAt: string
}

/**
 * Persisted exam variant entity (matches database schema)
 */
export interface ExamVariant {
    id: string
    examId: string
    variantIndex: number
    modelIdentifier: string
    questionOrder: number[]
    alternativeOrders: number[][]
    qrcodePayload: string | null
    docxStoragePath: string | null
    createdAt: string
}

/**
 * Persisted variant answer key entity (matches database schema)
 */
export interface VariantAnswerKey {
    id: string
    variantId: string
    answersString: string
    createdAt: string
}

// Helper types for the exam builder UI

/**
 * State of an image upload operation
 */
export type ImageUploadStatus = 'idle' | 'uploading' | 'success' | 'error'

/**
 * Represents an image being uploaded or already uploaded
 */
export interface ImageUploadState {
    id: string
    file?: File
    previewUrl?: string
    storagePath?: string
    status: ImageUploadStatus
    error?: string
    progress?: number
}

/**
 * Actions available in the exam builder
 */
export type ExamBuilderAction =
    | { type: 'SET_NAME'; payload: string }
    | { type: 'SET_TEMPLATE_ID'; payload: string }
    | { type: 'SET_SHUFFLE_QUESTIONS'; payload: boolean }
    | { type: 'SET_SHUFFLE_ALTERNATIVES'; payload: boolean }
    | { type: 'SET_VARIANT_COUNT'; payload: number }
    | { type: 'SET_SEED'; payload: number | undefined }
    | { type: 'ADD_QUESTION'; payload?: Partial<ExamQuestion> }
    | { type: 'UPDATE_QUESTION'; payload: { index: number; question: Partial<ExamQuestion> } }
    | { type: 'REMOVE_QUESTION'; payload: number }
    | { type: 'REORDER_QUESTIONS'; payload: number[] }
    | { type: 'ADD_ALTERNATIVE'; payload: { questionIndex: number; alternative?: Partial<ExamAlternative> } }
    | { type: 'UPDATE_ALTERNATIVE'; payload: { questionIndex: number; alternativeIndex: number; alternative: Partial<ExamAlternative> } }
    | { type: 'REMOVE_ALTERNATIVE'; payload: { questionIndex: number; alternativeIndex: number } }
    | { type: 'SET_CORRECT_ALTERNATIVE'; payload: { questionIndex: number; alternativeIndex: number } }
    | { type: 'ADD_QUESTION_IMAGE'; payload: { questionIndex: number; image: QuestionImage } }
    | { type: 'REMOVE_QUESTION_IMAGE'; payload: { questionIndex: number; imageId: string } }
    | { type: 'SET_ALTERNATIVE_IMAGE'; payload: { questionIndex: number; alternativeIndex: number; image: AlternativeImage | null } }
    | { type: 'RESET' }
    | { type: 'LOAD_EXAM'; payload: ExamConfig }

/**
 * State of the exam builder
 */
export interface ExamBuilderState {
    name: string
    templateId: string
    questions: ExamQuestion[]
    shuffleQuestions: boolean
    shuffleAlternatives: boolean
    variantCount: number
    seed?: number
    isDirty: boolean
    isValid: boolean
    validationErrors: string[]
}

/**
 * Context value for the exam builder
 */
export interface ExamBuilderContextValue {
    state: ExamBuilderState
    dispatch: React.Dispatch<ExamBuilderAction>
    // Convenience methods
    addQuestion: (question?: Partial<ExamQuestion>) => void
    updateQuestion: (index: number, question: Partial<ExamQuestion>) => void
    removeQuestion: (index: number) => void
    addAlternative: (questionIndex: number, alternative?: Partial<ExamAlternative>) => void
    updateAlternative: (questionIndex: number, alternativeIndex: number, alternative: Partial<ExamAlternative>) => void
    removeAlternative: (questionIndex: number, alternativeIndex: number) => void
    setCorrectAlternative: (questionIndex: number, alternativeIndex: number) => void
    addQuestionImage: (questionIndex: number, image: QuestionImage) => void
    removeQuestionImage: (questionIndex: number, imageId: string) => void
    setAlternativeImage: (questionIndex: number, alternativeIndex: number, image: AlternativeImage | null) => void
    reset: () => void
    loadExam: (config: ExamConfig) => void
    getConfig: () => ExamConfig
    validate: () => boolean
}
