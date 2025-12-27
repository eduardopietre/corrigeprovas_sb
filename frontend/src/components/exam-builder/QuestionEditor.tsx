/**
 * QuestionEditor - Editor component for exam questions with image support
 * Requirements: 16.1, 16.2, 16.6
 */

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import type { AlternativeImage, ExamAlternative, ExamQuestion, QuestionImage } from '@/services/examBuilderTypes'
import { Check, GripVertical, Plus, Trash2 } from 'lucide-react'
import { useCallback } from 'react'
import { ImagePreview, ImageUploader, type UploadedImage } from './ImageUploader'

// We need to add Textarea to shadcn/ui components
// For now, let's use a simple textarea

export interface QuestionEditorProps {
    question: ExamQuestion
    examId: string
    onUpdate: (question: Partial<ExamQuestion>) => void
    onRemove: () => void
    onAddAlternative: () => void
    onUpdateAlternative: (alternativeIndex: number, alternative: Partial<ExamAlternative>) => void
    onRemoveAlternative: (alternativeIndex: number) => void
    onSetCorrectAlternative: (alternativeIndex: number) => void
    onAddImage: (image: QuestionImage) => void
    onRemoveImage: (imageId: string) => void
    onSetAlternativeImage: (alternativeIndex: number, image: AlternativeImage | null) => void
    className?: string
    isDragging?: boolean
}

export function QuestionEditor({
    question,
    examId,
    onUpdate,
    onRemove,
    onAddAlternative,
    onUpdateAlternative,
    onRemoveAlternative,
    onSetCorrectAlternative,
    onAddImage,
    onRemoveImage,
    onSetAlternativeImage,
    className,
    isDragging = false,
}: QuestionEditorProps) {
    const handleTextChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
        onUpdate({ text: e.target.value })
    }, [onUpdate])

    const handleImageUpload = useCallback((uploadedImage: UploadedImage) => {
        const questionImage: QuestionImage = {
            id: uploadedImage.id,
            storagePath: uploadedImage.storagePath,
            position: question.images.length,
            width: uploadedImage.width,
            height: uploadedImage.height,
        }
        onAddImage(questionImage)
    }, [onAddImage, question.images.length])

    const indexToLetter = (index: number): string => {
        return String.fromCharCode(65 + index) // A, B, C, D, E...
    }

    return (
        <Card className={cn(
            'transition-all',
            isDragging && 'opacity-50 scale-[0.98]',
            className
        )}>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <GripVertical className="h-5 w-5 text-muted-foreground cursor-grab" />
                        <span className="font-semibold">Questão {question.index + 1}</span>
                    </div>
                    <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={onRemove}
                        className="text-destructive hover:text-destructive"
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Question text */}
                <div className="space-y-2">
                    <Label htmlFor={`question-${question.id}-text`}>Enunciado</Label>
                    <Textarea
                        id={`question-${question.id}-text`}
                        value={question.text}
                        onChange={handleTextChange}
                        placeholder="Digite o enunciado da questão..."
                        className="min-h-[100px] resize-y"
                    />
                </div>

                {/* Question images */}
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <Label>Imagens da questão</Label>
                        <ImageUploader
                            examId={examId}
                            type="question"
                            onUpload={handleImageUpload}
                        />
                    </div>
                    {question.images.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {question.images.map((image) => (
                                <ImagePreview
                                    key={image.id}
                                    image={{
                                        id: image.id,
                                        storagePath: image.storagePath,
                                        previewUrl: '', // Will load from storage
                                        width: image.width,
                                        height: image.height,
                                    }}
                                    onRemove={() => onRemoveImage(image.id)}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Alternatives */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <Label>Alternativas</Label>
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={onAddAlternative}
                            disabled={question.alternatives.length >= 5}
                        >
                            <Plus className="h-4 w-4 mr-1" />
                            Adicionar
                        </Button>
                    </div>

                    <div className="space-y-2">
                        {question.alternatives.map((alternative, altIndex) => (
                            <AlternativeEditor
                                key={alternative.id}
                                alternative={alternative}
                                examId={examId}
                                letter={indexToLetter(altIndex)}
                                isCorrect={question.correctAlternativeIndex === altIndex}
                                onUpdate={(alt) => onUpdateAlternative(altIndex, alt)}
                                onRemove={() => onRemoveAlternative(altIndex)}
                                onSetCorrect={() => onSetCorrectAlternative(altIndex)}
                                onSetImage={(image) => onSetAlternativeImage(altIndex, image)}
                                canRemove={question.alternatives.length > 2}
                            />
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

/**
 * AlternativeEditor - Editor for a single alternative
 */
interface AlternativeEditorProps {
    alternative: ExamAlternative
    examId: string
    letter: string
    isCorrect: boolean
    onUpdate: (alternative: Partial<ExamAlternative>) => void
    onRemove: () => void
    onSetCorrect: () => void
    onSetImage: (image: AlternativeImage | null) => void
    canRemove: boolean
}

function AlternativeEditor({
    alternative,
    examId,
    letter,
    isCorrect,
    onUpdate,
    onRemove,
    onSetCorrect,
    onSetImage,
    canRemove,
}: AlternativeEditorProps) {
    const handleTextChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        onUpdate({ text: e.target.value })
    }, [onUpdate])

    const handleImageUpload = useCallback((uploadedImage: UploadedImage) => {
        const alternativeImage: AlternativeImage = {
            id: uploadedImage.id,
            storagePath: uploadedImage.storagePath,
            width: uploadedImage.width,
            height: uploadedImage.height,
        }
        onSetImage(alternativeImage)
    }, [onSetImage])

    return (
        <div className={cn(
            'flex items-start gap-2 p-3 rounded-lg border transition-colors',
            isCorrect && 'border-green-500 bg-green-50 dark:bg-green-950/20'
        )}>
            {/* Correct indicator button */}
            <Button
                type="button"
                variant={isCorrect ? 'default' : 'outline'}
                size="sm"
                className={cn(
                    'h-8 w-8 p-0 shrink-0',
                    isCorrect && 'bg-green-600 hover:bg-green-700'
                )}
                onClick={onSetCorrect}
                title={isCorrect ? 'Alternativa correta' : 'Marcar como correta'}
            >
                {isCorrect ? (
                    <Check className="h-4 w-4" />
                ) : (
                    <span className="text-sm font-medium">{letter}</span>
                )}
            </Button>

            {/* Alternative content */}
            <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                    <span className="font-medium text-sm w-6">{letter})</span>
                    <input
                        type="text"
                        value={alternative.text}
                        onChange={handleTextChange}
                        placeholder={`Alternativa ${letter}...`}
                        className="flex-1 px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                </div>

                {/* Alternative image */}
                <div className="flex items-center gap-2 ml-8">
                    {alternative.image ? (
                        <ImagePreview
                            image={{
                                id: alternative.image.id,
                                storagePath: alternative.image.storagePath,
                                previewUrl: '',
                                width: alternative.image.width,
                                height: alternative.image.height,
                            }}
                            onRemove={() => onSetImage(null)}
                            className="max-h-20"
                        />
                    ) : (
                        <ImageUploader
                            examId={examId}
                            type="alternative"
                            onUpload={handleImageUpload}
                        >
                            <Button type="button" variant="ghost" size="sm" className="text-xs">
                                + Imagem
                            </Button>
                        </ImageUploader>
                    )}
                </div>
            </div>

            {/* Remove button */}
            {canRemove && (
                <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={onRemove}
                    className="text-muted-foreground hover:text-destructive shrink-0"
                >
                    <Trash2 className="h-4 w-4" />
                </Button>
            )}
        </div>
    )
}

export default QuestionEditor
