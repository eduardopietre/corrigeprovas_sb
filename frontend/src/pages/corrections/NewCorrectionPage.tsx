import { ArrowLeft, FileImage, Loader2, Trash2, Upload, X } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { useFileUpload } from '@/hooks'
import { supabase } from '@/lib/supabase'
import { correctionService } from '@/services'
import type { AnswerKey, Template } from '@/services/types'

export function NewCorrectionPage() {
    const navigate = useNavigate()
    const { files, isUploading, addFiles, removeFile, clearFiles, uploadFiles } = useFileUpload()

    const [templates, setTemplates] = useState<Template[]>([])
    const [answerKeys, setAnswerKeys] = useState<AnswerKey[]>([])
    const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
    const [selectedAnswerKeyId, setSelectedAnswerKeyId] = useState<string>('')
    const [isLoading, setIsLoading] = useState(true)
    const [isCreatingJob, setIsCreatingJob] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isDragging, setIsDragging] = useState(false)

    // Load templates and answer keys
    useEffect(() => {
        async function loadData() {
            setIsLoading(true)
            try {
                // Load templates
                const { data: templatesData, error: templatesError } = await supabase
                    .from('templates')
                    .select('*')
                    .eq('is_active', true)
                    .order('name')

                if (templatesError) throw templatesError
                setTemplates(templatesData as Template[])

                // Load answer keys
                const { data: answerKeysData, error: answerKeysError } = await supabase
                    .from('answer_keys')
                    .select('*')
                    .order('created_at', { ascending: false })

                if (answerKeysError) throw answerKeysError
                setAnswerKeys(answerKeysData as AnswerKey[])
            } catch (err) {
                console.error('Error loading data:', err)
                setError('Erro ao carregar dados. Tente novamente.')
            } finally {
                setIsLoading(false)
            }
        }

        loadData()
    }, [])

    // Filter answer keys by selected template
    const filteredAnswerKeys = selectedTemplateId
        ? answerKeys.filter((ak) => ak.template_id === selectedTemplateId)
        : answerKeys

    // Handle file drop
    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault()
            setIsDragging(false)

            const droppedFiles = Array.from(e.dataTransfer.files).filter((file) =>
                file.type.startsWith('image/') || file.type === 'application/pdf'
            )

            if (droppedFiles.length > 0) {
                addFiles(droppedFiles)
            }
        },
        [addFiles]
    )

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }, [])

    // Handle file input change
    const handleFileInputChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const selectedFiles = Array.from(e.target.files || [])
            if (selectedFiles.length > 0) {
                addFiles(selectedFiles)
            }
            // Reset input
            e.target.value = ''
        },
        [addFiles]
    )

    // Handle job creation
    const handleCreateJob = async () => {
        if (!selectedAnswerKeyId || !selectedTemplateId || files.length === 0) {
            setError('Selecione um template, gabarito e adicione pelo menos uma imagem.')
            return
        }

        setError(null)
        setIsCreatingJob(true)

        try {
            // Upload files first
            const uploadedPaths = await uploadFiles()

            if (uploadedPaths.length === 0) {
                throw new Error('Nenhum arquivo foi enviado com sucesso.')
            }

            // Create correction job
            const { data: jobData, error: jobError } = await correctionService.createJob({
                answerKeyId: selectedAnswerKeyId,
                templateId: selectedTemplateId,
                items: uploadedPaths.map((path) => ({ originalStoragePath: path })),
                idempotencyKey: `job-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            })

            if (jobError) {
                throw new Error(jobError.message)
            }

            // Navigate to job progress page
            navigate(`/corrections/${jobData?.jobId}`)
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Erro ao criar correção.'
            setError(errorMessage)
        } finally {
            setIsCreatingJob(false)
        }
    }

    const uploadProgress = files.length > 0
        ? Math.round(
            (files.filter((f) => f.status === 'success').length / files.length) * 100
        )
        : 0

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b">
                <div className="container mx-auto px-4 py-4 flex items-center gap-4">
                    <Button variant="ghost" size="icon" asChild>
                        <Link to="/dashboard">
                            <ArrowLeft className="h-5 w-5" />
                        </Link>
                    </Button>
                    <h1 className="text-xl font-bold">Nova Correção</h1>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8 max-w-3xl">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <div className="space-y-6">
                    {/* Template and Answer Key Selection */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Configuração</CardTitle>
                            <CardDescription>
                                Selecione o template e gabarito para a correção
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Template</label>
                                <Select
                                    value={selectedTemplateId}
                                    onValueChange={(value) => {
                                        setSelectedTemplateId(value)
                                        setSelectedAnswerKeyId('') // Reset answer key when template changes
                                    }}
                                    disabled={isLoading}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Selecione um template" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {templates.map((template) => (
                                            <SelectItem key={template.id} value={template.id}>
                                                {template.name} ({template.question_count} questões, {template.alternatives_count} alternativas)
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Gabarito</label>
                                <Select
                                    value={selectedAnswerKeyId}
                                    onValueChange={setSelectedAnswerKeyId}
                                    disabled={isLoading || !selectedTemplateId}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder={selectedTemplateId ? "Selecione um gabarito" : "Selecione um template primeiro"} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {filteredAnswerKeys.map((answerKey) => (
                                            <SelectItem key={answerKey.id} value={answerKey.id}>
                                                {answerKey.name || `Gabarito ${answerKey.id.slice(0, 8)}`}
                                            </SelectItem>
                                        ))}
                                        {filteredAnswerKeys.length === 0 && selectedTemplateId && (
                                            <div className="px-2 py-4 text-sm text-muted-foreground text-center">
                                                Nenhum gabarito encontrado para este template.
                                                <Link to="/answer-keys/new" className="block mt-2 text-primary hover:underline">
                                                    Criar novo gabarito
                                                </Link>
                                            </div>
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>
                        </CardContent>
                    </Card>

                    {/* File Upload */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Imagens</CardTitle>
                            <CardDescription>
                                Arraste e solte as imagens das folhas de resposta ou clique para selecionar
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {/* Drop Zone */}
                            <div
                                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragging
                                        ? 'border-primary bg-primary/5'
                                        : 'border-muted-foreground/25 hover:border-primary/50'
                                    }`}
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                            >
                                <input
                                    type="file"
                                    id="file-input"
                                    className="hidden"
                                    multiple
                                    accept="image/*,application/pdf"
                                    onChange={handleFileInputChange}
                                />
                                <label
                                    htmlFor="file-input"
                                    className="cursor-pointer flex flex-col items-center gap-2"
                                >
                                    <Upload className="h-10 w-10 text-muted-foreground" />
                                    <span className="text-sm text-muted-foreground">
                                        Arraste imagens aqui ou clique para selecionar
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                        Formatos aceitos: JPEG, PNG, WebP, TIFF, PDF
                                    </span>
                                </label>
                            </div>

                            {/* File List */}
                            {files.length > 0 && (
                                <div className="mt-4 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium">
                                            {files.length} arquivo(s) selecionado(s)
                                        </span>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={clearFiles}
                                            disabled={isUploading || isCreatingJob}
                                        >
                                            <Trash2 className="h-4 w-4 mr-1" />
                                            Limpar
                                        </Button>
                                    </div>

                                    <div className="max-h-60 overflow-y-auto space-y-2">
                                        {files.map((file, index) => (
                                            <div
                                                key={index}
                                                className="flex items-center gap-3 p-2 rounded-lg bg-muted/50"
                                            >
                                                <FileImage className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm truncate">{file.file.name}</p>
                                                    {file.status === 'uploading' && (
                                                        <Progress value={file.progress} className="h-1 mt-1" />
                                                    )}
                                                    {file.status === 'error' && (
                                                        <p className="text-xs text-destructive">{file.error}</p>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {file.status === 'success' && (
                                                        <span className="text-xs text-green-600">✓</span>
                                                    )}
                                                    {file.status === 'uploading' && (
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                    )}
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-6 w-6"
                                                        onClick={() => removeFile(index)}
                                                        disabled={isUploading || isCreatingJob}
                                                    >
                                                        <X className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Upload Progress */}
                    {isUploading && (
                        <Card>
                            <CardContent className="pt-6">
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span>Enviando arquivos...</span>
                                        <span>{uploadProgress}%</span>
                                    </div>
                                    <Progress value={uploadProgress} />
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Submit Button */}
                    <Button
                        className="w-full"
                        size="lg"
                        onClick={handleCreateJob}
                        disabled={
                            isLoading ||
                            isUploading ||
                            isCreatingJob ||
                            !selectedTemplateId ||
                            !selectedAnswerKeyId ||
                            files.length === 0
                        }
                    >
                        {isCreatingJob ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Criando correção...
                            </>
                        ) : (
                            'Iniciar Correção'
                        )}
                    </Button>
                </div>
            </main>
        </div>
    )
}
