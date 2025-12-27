/**
 * ShuffleService - Deterministic randomization for exam variants
 * Requirements: 15.2, 15.3, 15.4, 15.8
 * 
 * Implements Fisher-Yates shuffle with seeded PRNG for reproducible results.
 */

/**
 * Result of shuffling an array with index mapping
 */
export interface ShuffleResult<T> {
    shuffled: T[]
    mapping: number[]  // mapping[newIndex] = originalIndex
}

/**
 * Seeded pseudo-random number generator using Mulberry32 algorithm
 * This provides deterministic random numbers given the same seed.
 */
function createSeededRandom(seed: number): () => number {
    let state = seed >>> 0  // Ensure unsigned 32-bit integer

    return function (): number {
        state = (state + 0x6D2B79F5) >>> 0
        let t = state
        t = Math.imul(t ^ (t >>> 15), t | 1)
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
}

/**
 * Fisher-Yates shuffle algorithm with seeded randomization
 * Returns both the shuffled array and the index mapping.
 * 
 * @param items - Array to shuffle
 * @param seed - Seed for deterministic randomization
 * @returns Object containing shuffled array and mapping
 */
export function shuffleWithMapping<T>(items: T[], seed: number): ShuffleResult<T> {
    if (items.length === 0) {
        return { shuffled: [], mapping: [] }
    }

    const random = createSeededRandom(seed)

    // Create array of indices
    const indices = items.map((_, i) => i)

    // Fisher-Yates shuffle on indices
    for (let i = indices.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1))
            ;[indices[i], indices[j]] = [indices[j], indices[i]]
    }

    // Build shuffled array and mapping
    const shuffled = indices.map(originalIndex => items[originalIndex])
    const mapping = indices  // mapping[newIndex] = originalIndex

    return { shuffled, mapping }
}

/**
 * Generates a unique seed for each variant based on a base seed.
 * Uses a simple but effective mixing function to ensure different variants
 * get different but reproducible seeds.
 * 
 * @param baseSeed - The base seed for the exam
 * @param variantIndex - The index of the variant (0-based)
 * @returns A unique seed for this variant
 */
export function generateVariantSeed(baseSeed: number, variantIndex: number): number {
    // Mix the base seed with the variant index using a simple hash
    // This ensures each variant gets a different but deterministic seed
    const mixed = baseSeed ^ (variantIndex * 2654435761)  // Golden ratio prime
    return mixed >>> 0  // Ensure unsigned 32-bit integer
}

/**
 * Calculates the new letter of the correct answer after shuffling alternatives.
 * 
 * @param originalCorrectIndex - The original 0-based index of the correct alternative
 * @param alternativeMapping - The mapping from new positions to original positions
 * @returns The letter (A-Z) corresponding to the new position of the correct answer
 */
export function getShuffledCorrectAnswer(
    originalCorrectIndex: number,
    alternativeMapping: number[]
): string {
    // Find the new position of the originally correct alternative
    const newPosition = alternativeMapping.findIndex(
        originalIndex => originalIndex === originalCorrectIndex
    )

    if (newPosition === -1) {
        throw new Error(`Original correct index ${originalCorrectIndex} not found in mapping`)
    }

    // Convert to letter (0 = A, 1 = B, etc.)
    return String.fromCharCode(65 + newPosition)  // 65 is ASCII for 'A'
}

/**
 * Converts a 0-based index to a letter (A-Z)
 */
export function indexToLetter(index: number): string {
    if (index < 0 || index > 25) {
        throw new Error(`Index ${index} out of range for letter conversion (0-25)`)
    }
    return String.fromCharCode(65 + index)
}

/**
 * Converts a letter (A-Z) to a 0-based index
 */
export function letterToIndex(letter: string): number {
    const upper = letter.toUpperCase()
    if (upper.length !== 1 || upper < 'A' || upper > 'Z') {
        throw new Error(`Invalid letter: ${letter}`)
    }
    return upper.charCodeAt(0) - 65
}

/**
 * ShuffleService interface for dependency injection and testing
 */
export interface ShuffleService {
    shuffleWithMapping<T>(items: T[], seed: number): ShuffleResult<T>
    generateVariantSeed(baseSeed: number, variantIndex: number): number
    getShuffledCorrectAnswer(originalCorrectIndex: number, alternativeMapping: number[]): string
}

/**
 * Default implementation of ShuffleService
 */
export const shuffleService: ShuffleService = {
    shuffleWithMapping,
    generateVariantSeed,
    getShuffledCorrectAnswer,
}

export default shuffleService
