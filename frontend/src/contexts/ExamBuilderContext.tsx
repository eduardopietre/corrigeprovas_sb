/**
 * ExamBuilderContext - Manages state for the exam builder editor
 * Requirements: 12.1, 16.1, 16.2
 */

import type {
    AlternativeImage,
    ExamAlternative,
    ExamBuilderAction,
    ExamBuilderContextValue,
    ExamBuilderState,
    ExamConfig,
    ExamQuestion,
    QuestionImage,
} from '@/services/examBuilderTypes'
import { createContext, useCallback, useContext, useReducer, type ReactNode } from 'react'

// Generate a unique ID for new items
const generateId = (): string => {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

// Create a default alternative
const createDefaultAlternative = (index: number): ExamAlternative => ({
    id: generateId(),
    index,
    text: '',
    image: null,
})

// Create a default question with 4 alternatives
const createDefaultQuestion = (index: number): ExamQuestion => ({
    id: generateId(),
    index,
    text: '',
    images: [],
    alternatives: [
        createDefaultAlternative(0),
        createDefaultAlternative(1),
        createDefaultAlternative(2),
        createDefaultAlternative(3),
    ],
    correctAlternativeIndex: 0,
})

// Initial state for the exam builder
const initialState: ExamBuilderState = {
    name: '',
    templateId: '',
    questions: [],
    shuffleQuestions: false,
    shuffleAlternatives: false,
    variantCount: 1,
    seed: undefined,
    isDirty: false,
    isValid: false,
    validationErrors: [],
}

// Validate the exam builder state
function validateState(state: ExamBuilderState): { isValid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!state.name.trim()) {
        errors.push('O nome da prova é obrigatório')
    }

    if (!state.templateId) {
        errors.push('Selecione um template')
    }

    if (state.questions.length === 0) {
        errors.push('Adicione pelo menos uma questão')
    }

    for (let i = 0; i < state.questions.length; i++) {
        const question = state.questions[i]

        if (!question.text.trim()) {
            errors.push(`Questão ${i + 1}: O texto da questão é obrigatório`)
        }

        if (question.alternatives.length < 2) {
            errors.push(`Questão ${i + 1}: Adicione pelo menos 2 alternativas`)
        }

        const hasEmptyAlternative = question.alternatives.some(alt => !alt.text.trim() && !alt.image)
        if (hasEmptyAlternative) {
            errors.push(`Questão ${i + 1}: Todas as alternativas devem ter texto ou imagem`)
        }

        if (question.correctAlternativeIndex < 0 || question.correctAlternativeIndex >= question.alternatives.length) {
            errors.push(`Questão ${i + 1}: Selecione a alternativa correta`)
        }
    }

    if (state.variantCount < 1 || state.variantCount > 26) {
        errors.push('O número de variantes deve ser entre 1 e 26')
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

// Reducer for exam builder state
function examBuilderReducer(state: ExamBuilderState, action: ExamBuilderAction): ExamBuilderState {
    let newState: ExamBuilderState

    switch (action.type) {
        case 'SET_NAME':
            newState = { ...state, name: action.payload, isDirty: true }
            break

        case 'SET_TEMPLATE_ID':
            newState = { ...state, templateId: action.payload, isDirty: true }
            break

        case 'SET_SHUFFLE_QUESTIONS':
            newState = { ...state, shuffleQuestions: action.payload, isDirty: true }
            break

        case 'SET_SHUFFLE_ALTERNATIVES':
            newState = { ...state, shuffleAlternatives: action.payload, isDirty: true }
            break

        case 'SET_VARIANT_COUNT':
            newState = { ...state, variantCount: action.payload, isDirty: true }
            break

        case 'SET_SEED':
            newState = { ...state, seed: action.payload, isDirty: true }
            break

        case 'ADD_QUESTION': {
            const newQuestion = action.payload
                ? { ...createDefaultQuestion(state.questions.length), ...action.payload, id: generateId() }
                : createDefaultQuestion(state.questions.length)
            newState = {
                ...state,
                questions: [...state.questions, newQuestion],
                isDirty: true,
            }
            break
        }

        case 'UPDATE_QUESTION': {
            const { index, question } = action.payload
            const updatedQuestions = [...state.questions]
            if (index >= 0 && index < updatedQuestions.length) {
                updatedQuestions[index] = { ...updatedQuestions[index], ...question }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'REMOVE_QUESTION': {
            const updatedQuestions = state.questions
                .filter((_, i) => i !== action.payload)
                .map((q, i) => ({ ...q, index: i }))
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'REORDER_QUESTIONS': {
            const newOrder = action.payload
            const reorderedQuestions = newOrder
                .map((oldIndex, newIndex) => ({
                    ...state.questions[oldIndex],
                    index: newIndex,
                }))
            newState = { ...state, questions: reorderedQuestions, isDirty: true }
            break
        }

        case 'ADD_ALTERNATIVE': {
            const { questionIndex, alternative } = action.payload
            const updatedQuestions = [...state.questions]
            if (questionIndex >= 0 && questionIndex < updatedQuestions.length) {
                const question = updatedQuestions[questionIndex]
                const newAlternative = alternative
                    ? { ...createDefaultAlternative(question.alternatives.length), ...alternative, id: generateId() }
                    : createDefaultAlternative(question.alternatives.length)
                updatedQuestions[questionIndex] = {
                    ...question,
                    alternatives: [...question.alternatives, newAlternative],
                }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'UPDATE_ALTERNATIVE': {
            const { questionIndex, alternativeIndex, alternative } = action.payload
            const updatedQuestions = [...state.questions]
            if (questionIndex >= 0 && questionIndex < updatedQuestions.length) {
                const question = updatedQuestions[questionIndex]
                if (alternativeIndex >= 0 && alternativeIndex < question.alternatives.length) {
                    const updatedAlternatives = [...question.alternatives]
                    updatedAlternatives[alternativeIndex] = {
                        ...updatedAlternatives[alternativeIndex],
                        ...alternative,
                    }
                    updatedQuestions[questionIndex] = {
                        ...question,
                        alternatives: updatedAlternatives,
                    }
                }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'REMOVE_ALTERNATIVE': {
            const { questionIndex, alternativeIndex } = action.payload
            const updatedQuestions = [...state.questions]
            if (questionIndex >= 0 && questionIndex < updatedQuestions.length) {
                const question = updatedQuestions[questionIndex]
                const updatedAlternatives = question.alternatives
                    .filter((_, i) => i !== alternativeIndex)
                    .map((alt, i) => ({ ...alt, index: i }))

                // Adjust correctAlternativeIndex if needed
                let newCorrectIndex = question.correctAlternativeIndex
                if (alternativeIndex < question.correctAlternativeIndex) {
                    newCorrectIndex = question.correctAlternativeIndex - 1
                } else if (alternativeIndex === question.correctAlternativeIndex) {
                    newCorrectIndex = 0
                }

                updatedQuestions[questionIndex] = {
                    ...question,
                    alternatives: updatedAlternatives,
                    correctAlternativeIndex: Math.min(newCorrectIndex, updatedAlternatives.length - 1),
                }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'SET_CORRECT_ALTERNATIVE': {
            const { questionIndex, alternativeIndex } = action.payload
            const updatedQuestions = [...state.questions]
            if (questionIndex >= 0 && questionIndex < updatedQuestions.length) {
                updatedQuestions[questionIndex] = {
                    ...updatedQuestions[questionIndex],
                    correctAlternativeIndex: alternativeIndex,
                }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'ADD_QUESTION_IMAGE': {
            const { questionIndex, image } = action.payload
            const updatedQuestions = [...state.questions]
            if (questionIndex >= 0 && questionIndex < updatedQuestions.length) {
                const question = updatedQuestions[questionIndex]
                updatedQuestions[questionIndex] = {
                    ...question,
                    images: [...question.images, image],
                }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'REMOVE_QUESTION_IMAGE': {
            const { questionIndex, imageId } = action.payload
            const updatedQuestions = [...state.questions]
            if (questionIndex >= 0 && questionIndex < updatedQuestions.length) {
                const question = updatedQuestions[questionIndex]
                updatedQuestions[questionIndex] = {
                    ...question,
                    images: question.images.filter(img => img.id !== imageId),
                }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'SET_ALTERNATIVE_IMAGE': {
            const { questionIndex, alternativeIndex, image } = action.payload
            const updatedQuestions = [...state.questions]
            if (questionIndex >= 0 && questionIndex < updatedQuestions.length) {
                const question = updatedQuestions[questionIndex]
                if (alternativeIndex >= 0 && alternativeIndex < question.alternatives.length) {
                    const updatedAlternatives = [...question.alternatives]
                    updatedAlternatives[alternativeIndex] = {
                        ...updatedAlternatives[alternativeIndex],
                        image,
                    }
                    updatedQuestions[questionIndex] = {
                        ...question,
                        alternatives: updatedAlternatives,
                    }
                }
            }
            newState = { ...state, questions: updatedQuestions, isDirty: true }
            break
        }

        case 'RESET':
            newState = { ...initialState }
            break

        case 'LOAD_EXAM': {
            const config = action.payload
            newState = {
                name: config.name,
                templateId: config.templateId,
                questions: config.questions,
                shuffleQuestions: config.shuffleQuestions,
                shuffleAlternatives: config.shuffleAlternatives,
                variantCount: config.variantCount,
                seed: config.seed,
                isDirty: false,
                isValid: false,
                validationErrors: [],
            }
            break
        }

        default:
            return state
    }

    // Validate after each state change
    const validation = validateState(newState)
    return {
        ...newState,
        isValid: validation.isValid,
        validationErrors: validation.errors,
    }
}

// Create the context
const ExamBuilderContext = createContext<ExamBuilderContextValue | undefined>(undefined)

// Provider component
export function ExamBuilderProvider({ children }: { children: ReactNode }) {
    const [state, dispatch] = useReducer(examBuilderReducer, initialState)

    const addQuestion = useCallback((question?: Partial<ExamQuestion>) => {
        dispatch({ type: 'ADD_QUESTION', payload: question })
    }, [])

    const updateQuestion = useCallback((index: number, question: Partial<ExamQuestion>) => {
        dispatch({ type: 'UPDATE_QUESTION', payload: { index, question } })
    }, [])

    const removeQuestion = useCallback((index: number) => {
        dispatch({ type: 'REMOVE_QUESTION', payload: index })
    }, [])

    const addAlternative = useCallback((questionIndex: number, alternative?: Partial<ExamAlternative>) => {
        dispatch({ type: 'ADD_ALTERNATIVE', payload: { questionIndex, alternative } })
    }, [])

    const updateAlternative = useCallback(
        (questionIndex: number, alternativeIndex: number, alternative: Partial<ExamAlternative>) => {
            dispatch({ type: 'UPDATE_ALTERNATIVE', payload: { questionIndex, alternativeIndex, alternative } })
        },
        []
    )

    const removeAlternative = useCallback((questionIndex: number, alternativeIndex: number) => {
        dispatch({ type: 'REMOVE_ALTERNATIVE', payload: { questionIndex, alternativeIndex } })
    }, [])

    const setCorrectAlternative = useCallback((questionIndex: number, alternativeIndex: number) => {
        dispatch({ type: 'SET_CORRECT_ALTERNATIVE', payload: { questionIndex, alternativeIndex } })
    }, [])

    const addQuestionImage = useCallback((questionIndex: number, image: QuestionImage) => {
        dispatch({ type: 'ADD_QUESTION_IMAGE', payload: { questionIndex, image } })
    }, [])

    const removeQuestionImage = useCallback((questionIndex: number, imageId: string) => {
        dispatch({ type: 'REMOVE_QUESTION_IMAGE', payload: { questionIndex, imageId } })
    }, [])

    const setAlternativeImage = useCallback(
        (questionIndex: number, alternativeIndex: number, image: AlternativeImage | null) => {
            dispatch({ type: 'SET_ALTERNATIVE_IMAGE', payload: { questionIndex, alternativeIndex, image } })
        },
        []
    )

    const reset = useCallback(() => {
        dispatch({ type: 'RESET' })
    }, [])

    const loadExam = useCallback((config: ExamConfig) => {
        dispatch({ type: 'LOAD_EXAM', payload: config })
    }, [])

    const getConfig = useCallback((): ExamConfig => {
        return {
            name: state.name,
            templateId: state.templateId,
            questions: state.questions,
            shuffleQuestions: state.shuffleQuestions,
            shuffleAlternatives: state.shuffleAlternatives,
            variantCount: state.variantCount,
            seed: state.seed,
        }
    }, [state])

    const validate = useCallback((): boolean => {
        const validation = validateState(state)
        return validation.isValid
    }, [state])

    const value: ExamBuilderContextValue = {
        state,
        dispatch,
        addQuestion,
        updateQuestion,
        removeQuestion,
        addAlternative,
        updateAlternative,
        removeAlternative,
        setCorrectAlternative,
        addQuestionImage,
        removeQuestionImage,
        setAlternativeImage,
        reset,
        loadExam,
        getConfig,
        validate,
    }

    return <ExamBuilderContext.Provider value={value}>{children}</ExamBuilderContext.Provider>
}

// Hook to use the exam builder context
export function useExamBuilder(): ExamBuilderContextValue {
    const context = useContext(ExamBuilderContext)
    if (context === undefined) {
        throw new Error('useExamBuilder must be used within an ExamBuilderProvider')
    }
    return context
}
