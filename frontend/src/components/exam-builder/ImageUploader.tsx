/**
 * ImageUploader - Drag-and-drop image upload component for exam questions
 * Requirements: 16.1, 16.2, 16.3, 16.4
 */

import { Button } from '@/components/ui/button'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'
import { cn } from '@/lib/utils'
import { Image as ImageIcon, Loader2, Upload, X } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'

// Allowed image formats
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB

export interface UploadedImage {
    id: string
    storagePath: string
    previewUrl: string
    width?: number
    height?: number
}

export interface ImageUploaderProps {
    examId: string
    type: 'question' | 'alternative'
    onUpload: (image: UploadedImage) => void
    onError?: (error: string) => void
    className?: string
    disabled?: boolean
    children?: React.ReactNode
}

export function ImageUploader({
    examId,
    type,
    onUpload,
    onError,
    className,
    disabled = false,
    children,
}: ImageUploaderProps) {
    const { user } = useAuth()
    const [isOpen, setIsOpen] = useState(false)
    const [isDragging, setIsDragging] = useState(false)
    const [isUploading, setIsUploading] = useState(false)
    const [uploadProgress, setUploadProgress] = useState(0)
    const [previewUrl, setPreviewUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const validateFile = useCallback((file: File): string | null => {
        if (!ALLOWED_TYPES.includes(file.type)) {
            return 'Formato inválido. Use JPEG, PNG ou WebP.'
        }
        if (file.size > MAX_FILE_SIZE) {
            return 'Arquivo muito grande. Máximo 5MB.'
        }
        return null
    }, [])

    const getImageDimensions = (file: File): Promise<{ width: number; height: number }> => {
        return new Promise((resolve, reject) => {
            const img = new Image()
            img.onload = () => {
                resolve({ width: img.width, height: img.height })
                URL.revokeObjectURL(img.src)
            }
            img.onerror = () => {
                reject(new Error('Failed to load image'))
                URL.revokeObjectURL(img.src)
            }
            img.src = URL.createObjectURL(file)
        })
    }

    const uploadFile = async (file: File) => {
        if (!user) {
            setError('Você precisa estar logado para fazer upload.')
            return
        }

        const validationError = validateFile(file)
        if (validationError) {
            setError(validationError)
            onError?.(validationError)
            return
        }

        setError(null)
        setIsUploading(true)
        setUploadProgress(0)

        try {
            // Create preview
            const preview = URL.createObjectURL(file)
            setPreviewUrl(preview)

            // Get image dimensions
            const dimensions = await getImageDimensions(file)

            // Generate unique filename
            const ext = file.name.split('.').pop() || 'jpg'
            const filename = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}.${ext}`
            const folder = type === 'question' ? 'questions' : 'alternatives'
            const storagePath = `${user.id}/${examId}/${folder}/${filename}`

            // Simulate progress (Supabase doesn't provide upload progress)
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => Math.min(prev + 10, 90))
            }, 100)

            // Upload to Supabase Storage
            const { error: uploadError } = await supabase.storage
                .from('exam-images')
                .upload(storagePath, file, {
                    contentType: file.type,
                    upsert: false,
                })

            clearInterval(progressInterval)

            if (uploadError) {
                throw uploadError
            }

            setUploadProgress(100)

            // Create uploaded image object
            const uploadedImage: UploadedImage = {
                id: `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
                storagePath,
                previewUrl: preview,
                width: dimensions.width,
                height: dimensions.height,
            }

            onUpload(uploadedImage)
            setIsOpen(false)
            resetState()
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Erro ao fazer upload'
            setError(errorMessage)
            onError?.(errorMessage)
        } finally {
            setIsUploading(false)
        }
    }

    const resetState = () => {
        setPreviewUrl(null)
        setError(null)
        setUploadProgress(0)
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (!disabled && !isUploading) {
            setIsDragging(true)
        }
    }, [disabled, isUploading])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)

        if (disabled || isUploading) return

        const files = e.dataTransfer.files
        if (files.length > 0) {
            uploadFile(files[0])
        }
    }, [disabled, isUploading])

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files
        if (files && files.length > 0) {
            uploadFile(files[0])
        }
    }, [])

    const handleClick = () => {
        if (!disabled && !isUploading) {
            fileInputRef.current?.click()
        }
    }

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                {children || (
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={disabled}
                        className={className}
                    >
                        <ImageIcon className="h-4 w-4 mr-2" />
                        Adicionar Imagem
                    </Button>
                )}
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Upload de Imagem</DialogTitle>
                    <DialogDescription>
                        Arraste uma imagem ou clique para selecionar. Formatos aceitos: JPEG, PNG, WebP (máx. 5MB)
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    {/* Drop zone */}
                    <div
                        onClick={handleClick}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        className={cn(
                            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                            isDragging && 'border-primary bg-primary/5',
                            !isDragging && 'border-muted-foreground/25 hover:border-primary/50',
                            (disabled || isUploading) && 'opacity-50 cursor-not-allowed'
                        )}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept={ALLOWED_TYPES.join(',')}
                            onChange={handleFileSelect}
                            className="hidden"
                            disabled={disabled || isUploading}
                        />

                        {isUploading ? (
                            <div className="space-y-4">
                                <Loader2 className="h-10 w-10 mx-auto animate-spin text-primary" />
                                <p className="text-sm text-muted-foreground">Enviando...</p>
                                <Progress value={uploadProgress} className="w-full" />
                            </div>
                        ) : previewUrl ? (
                            <div className="space-y-4">
                                <img
                                    src={previewUrl}
                                    alt="Preview"
                                    className="max-h-48 mx-auto rounded-lg object-contain"
                                />
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        resetState()
                                    }}
                                >
                                    <X className="h-4 w-4 mr-2" />
                                    Remover
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                                <p className="text-sm text-muted-foreground">
                                    Arraste uma imagem aqui ou clique para selecionar
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-lg">
                            {error}
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}

/**
 * ImagePreview - Displays an uploaded image with remove option
 */
export interface ImagePreviewProps {
    image: UploadedImage
    onRemove?: () => void
    className?: string
    showRemove?: boolean
}

export function ImagePreview({
    image,
    onRemove,
    className,
    showRemove = true,
}: ImagePreviewProps) {
    const [imageUrl, setImageUrl] = useState<string>(image.previewUrl)
    const [isLoading, setIsLoading] = useState(false)

    // If previewUrl is not available, try to get from storage
    const loadFromStorage = async () => {
        if (!image.previewUrl && image.storagePath) {
            setIsLoading(true)
            try {
                const { data } = await supabase.storage
                    .from('exam-images')
                    .createSignedUrl(image.storagePath, 3600) // 1 hour

                if (data?.signedUrl) {
                    setImageUrl(data.signedUrl)
                }
            } catch (err) {
                console.error('Failed to load image:', err)
            } finally {
                setIsLoading(false)
            }
        }
    }

    return (
        <div className={cn('relative inline-block group', className)}>
            {isLoading ? (
                <div className="w-24 h-24 bg-muted rounded-lg flex items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
            ) : (
                <img
                    src={imageUrl}
                    alt="Imagem"
                    className="max-h-32 rounded-lg object-contain border"
                    onError={loadFromStorage}
                    style={{
                        aspectRatio: image.width && image.height
                            ? `${image.width}/${image.height}`
                            : 'auto',
                    }}
                />
            )}
            {showRemove && onRemove && (
                <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="absolute -top-2 -right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={onRemove}
                >
                    <X className="h-3 w-3" />
                </Button>
            )}
        </div>
    )
}

export default ImageUploader
