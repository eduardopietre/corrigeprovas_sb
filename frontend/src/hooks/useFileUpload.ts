import { correctionService } from '@/services'
import type { UploadUrlItem } from '@/services/types'
import { useCallback, useState } from 'react'

export interface UploadedFile {
    file: File
    path: string
    status: 'pending' | 'uploading' | 'success' | 'error'
    progress: number
    error?: string
}

export function useFileUpload() {
    const [files, setFiles] = useState<UploadedFile[]>([])
    const [isUploading, setIsUploading] = useState(false)

    const addFiles = useCallback((newFiles: File[]) => {
        const uploadedFiles: UploadedFile[] = newFiles.map((file) => ({
            file,
            path: '',
            status: 'pending',
            progress: 0,
        }))
        setFiles((prev) => [...prev, ...uploadedFiles])
    }, [])

    const removeFile = useCallback((index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index))
    }, [])

    const clearFiles = useCallback(() => {
        setFiles([])
    }, [])

    const uploadFiles = useCallback(async (): Promise<string[]> => {
        if (files.length === 0) return []

        setIsUploading(true)
        const uploadedPaths: string[] = []

        try {
            // Get content types for all files
            const contentTypes = files.map((f) => {
                const type = f.file.type
                if (['image/jpeg', 'image/png', 'image/webp', 'image/tiff', 'application/pdf'].includes(type)) {
                    return type
                }
                return 'image/jpeg' // Default fallback
            })

            // Get signed URLs
            const { data: urlsResponse, error: urlsError } = await correctionService.getUploadUrls(
                files.length,
                contentTypes
            )

            if (urlsError || !urlsResponse) {
                throw new Error(urlsError?.message || 'Failed to get upload URLs')
            }

            // Upload each file
            for (let i = 0; i < files.length; i++) {
                const file = files[i]
                const urlItem: UploadUrlItem = urlsResponse.urls[i]

                setFiles((prev) =>
                    prev.map((f, idx) =>
                        idx === i ? { ...f, status: 'uploading', progress: 0 } : f
                    )
                )

                try {
                    // Upload using the signed URL
                    const response = await fetch(urlItem.signedUrl, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': file.file.type,
                        },
                        body: file.file,
                    })

                    if (!response.ok) {
                        throw new Error(`Upload failed: ${response.statusText}`)
                    }

                    uploadedPaths.push(urlItem.path)

                    setFiles((prev) =>
                        prev.map((f, idx) =>
                            idx === i
                                ? { ...f, status: 'success', progress: 100, path: urlItem.path }
                                : f
                        )
                    )
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : 'Upload failed'
                    setFiles((prev) =>
                        prev.map((f, idx) =>
                            idx === i
                                ? { ...f, status: 'error', error: errorMessage }
                                : f
                        )
                    )
                }
            }

            return uploadedPaths
        } finally {
            setIsUploading(false)
        }
    }, [files])

    return {
        files,
        isUploading,
        addFiles,
        removeFile,
        clearFiles,
        uploadFiles,
    }
}
