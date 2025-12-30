import { ArrowLeft, CheckCircle, Download, Loader2, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { correctionService } from '@/services'
import type { CorrectionJob, GetResultUrlsResponse } from '@/services/types'

export function CorrectionProgressPage() {
    const { jobId } = useParams<{ jobId: string }>()
    const [job, setJob] = useState<CorrectionJob | null>(null)
    const [results, setResults] = useState<GetResultUrlsResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Load job and subscribe to updates
    useEffect(() => {
        if (!jobId) return

        let isMounted = true
        const currentJobId = jobId

        async function loadJob() {
            const { data, error } = await correctionService.getJob(currentJobId)
            if (!isMounted) return

            if (error) {
                setError(error.message)
                setIsLoading(false)
                return
            }

            setJob(data || null)
            setIsLoading(false)

            // Load results if job is done
            if (data?.status === 'DONE') {
                loadResults()
            }
        }

        async function loadResults() {
            const { data, error } = await correctionService.getResultUrls(currentJobId)
            if (!isMounted) return

            if (!error && data) {
                setResults(data)
            }
        }

        loadJob()

        // Subscribe to real-time updates
        const channel = correctionService.subscribeToJob(currentJobId, (updatedJob) => {
            if (!isMounted) return
            setJob(updatedJob)

            // Load results when job completes
            if (updatedJob.status === 'DONE') {
                loadResults()
            }
        })

        return () => {
            isMounted = false
            correctionService.unsubscribeFromJob(channel)
        }
    }, [jobId])

    const getStatusInfo = (status: string) => {
        switch (status) {
            case 'QUEUED':
                return {
                    label: 'Na fila',
                    description: 'Aguardando processamento...',
                    color: 'text-yellow-600',
                    icon: <Loader2 className="h-6 w-6 animate-spin text-yellow-600" />,
                }
            case 'PROCESSING':
                return {
                    label: 'Processando',
                    description: 'Corrigindo folhas de resposta...',
                    color: 'text-blue-600',
                    icon: <Loader2 className="h-6 w-6 animate-spin text-blue-600" />,
                }
            case 'DONE':
                return {
                    label: 'Concluído',
                    description: 'Correção finalizada com sucesso!',
                    color: 'text-green-600',
                    icon: <CheckCircle className="h-6 w-6 text-green-600" />,
                }
            case 'FAILED':
                return {
                    label: 'Falhou',
                    description: 'Ocorreu um erro durante o processamento.',
                    color: 'text-red-600',
                    icon: <XCircle className="h-6 w-6 text-red-600" />,
                }
            case 'CANCELED':
                return {
                    label: 'Cancelado',
                    description: 'A correção foi cancelada.',
                    color: 'text-gray-600',
                    icon: <XCircle className="h-6 w-6 text-gray-600" />,
                }
            default:
                return {
                    label: status,
                    description: '',
                    color: 'text-gray-600',
                    icon: null,
                }
        }
    }

    const progress = job
        ? Math.round(((job.success_items + job.error_items) / job.total_items) * 100)
        : 0

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <header className="border-b">
                    <div className="container mx-auto px-4 py-4 flex items-center gap-4">
                        <Button variant="ghost" size="icon" asChild>
                            <Link to="/dashboard">
                                <ArrowLeft className="h-5 w-5" />
                            </Link>
                        </Button>
                        <Skeleton className="h-6 w-48" />
                    </div>
                </header>
                <main className="container mx-auto px-4 py-8 max-w-3xl">
                    <Card>
                        <CardHeader>
                            <Skeleton className="h-6 w-32" />
                            <Skeleton className="h-4 w-64" />
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-8 w-full" />
                        </CardContent>
                    </Card>
                </main>
            </div>
        )
    }

    if (error || !job) {
        return (
            <div className="min-h-screen bg-background">
                <header className="border-b">
                    <div className="container mx-auto px-4 py-4 flex items-center gap-4">
                        <Button variant="ghost" size="icon" asChild>
                            <Link to="/dashboard">
                                <ArrowLeft className="h-5 w-5" />
                            </Link>
                        </Button>
                        <h1 className="text-xl font-bold">Correção</h1>
                    </div>
                </header>
                <main className="container mx-auto px-4 py-8 max-w-3xl">
                    <Alert variant="destructive">
                        <AlertDescription>
                            {error || 'Correção não encontrada.'}
                        </AlertDescription>
                    </Alert>
                    <Button asChild className="mt-4">
                        <Link to="/dashboard">Voltar ao Dashboard</Link>
                    </Button>
                </main>
            </div>
        )
    }

    const statusInfo = getStatusInfo(job.status)

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="sticky top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
                <div className="container mx-auto px-4 py-4 flex items-center gap-4">
                    <Button variant="ghost" size="icon" asChild>
                        <Link to="/dashboard">
                            <ArrowLeft className="h-5 w-5" />
                        </Link>
                    </Button>
                    <h1 className="text-xl font-bold tracking-tight">Correção</h1>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8 max-w-3xl space-y-6 animate-fade-in-up">
                {/* Status Card */}
                <Card className="glass">
                    <CardHeader>
                        <div className="flex items-center gap-3">
                            {statusInfo.icon}
                            <div>
                                <CardTitle className={statusInfo.color}>{statusInfo.label}</CardTitle>
                                <CardDescription>{statusInfo.description}</CardDescription>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Progress */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <span>Progresso</span>
                                <span>
                                    {job.success_items + job.error_items} / {job.total_items}
                                </span>
                            </div>
                            <Progress value={progress} />
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-3 gap-4 pt-4">
                            <div className="text-center">
                                <p className="text-2xl font-bold">{job.total_items}</p>
                                <p className="text-sm text-muted-foreground">Total</p>
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-bold text-green-600">{job.success_items}</p>
                                <p className="text-sm text-muted-foreground">Sucesso</p>
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-bold text-red-600">{job.error_items}</p>
                                <p className="text-sm text-muted-foreground">Erros</p>
                            </div>
                        </div>

                        {/* Elapsed time */}
                        {job.elapsed_ms && (
                            <p className="text-sm text-muted-foreground text-center pt-2">
                                Tempo de processamento: {(job.elapsed_ms / 1000).toFixed(1)}s
                            </p>
                        )}
                    </CardContent>
                </Card>

                {/* Results Card */}
                {job.status === 'DONE' && results && (
                    <Card className="glass">
                        <CardHeader>
                            <CardTitle>Resultados</CardTitle>
                            <CardDescription>
                                Baixe os resultados da correção
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* XLSX Download */}
                            {results.xlsxUrl && (
                                <Button asChild className="w-full">
                                    <a href={results.xlsxUrl} download>
                                        <Download className="mr-2 h-4 w-4" />
                                        Baixar Planilha (XLSX)
                                    </a>
                                </Button>
                            )}

                            {/* Marked Images */}
                            {results.markedImages.length > 0 && (
                                <div className="space-y-2">
                                    <p className="text-sm font-medium">Imagens Corrigidas</p>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                        {results.markedImages.slice(0, 6).map((image) => (
                                            <a
                                                key={image.itemId}
                                                href={image.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="block aspect-[3/4] rounded-lg overflow-hidden border hover:border-primary transition-colors"
                                            >
                                                <img
                                                    src={image.url}
                                                    alt={`Folha ${image.index + 1}`}
                                                    className="w-full h-full object-cover"
                                                />
                                            </a>
                                        ))}
                                    </div>
                                    {results.markedImages.length > 6 && (
                                        <p className="text-sm text-muted-foreground text-center">
                                            +{results.markedImages.length - 6} imagens
                                        </p>
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Actions */}
                <div className="flex gap-4">
                    <Button variant="outline" asChild className="flex-1">
                        <Link to="/dashboard">Voltar ao Dashboard</Link>
                    </Button>
                    <Button asChild className="flex-1">
                        <Link to="/corrections/new">Nova Correção</Link>
                    </Button>
                </div>
            </main>
        </div>
    )
}
