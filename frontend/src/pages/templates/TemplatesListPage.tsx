import { ArrowLeft, FileText, Grid } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { templateService } from '@/services'
import type { Template } from '@/services/types'

export function TemplatesListPage() {
    const [templates, setTemplates] = useState<Template[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        async function loadTemplates() {
            const { data, error } = await templateService.list()

            if (error) {
                setError(error.message)
            } else {
                setTemplates(data || [])
            }

            setIsLoading(false)
        }

        loadTemplates()
    }, [])

    const getQuestionCountColor = (count: number) => {
        if (count <= 10) return 'bg-green-100 text-green-800'
        if (count <= 20) return 'bg-blue-100 text-blue-800'
        if (count <= 50) return 'bg-yellow-100 text-yellow-800'
        return 'bg-red-100 text-red-800'
    }

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
                    <h1 className="text-xl font-bold">Templates</h1>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <div className="mb-6">
                    <h2 className="text-lg font-semibold mb-2">Modelos de Folha de Resposta</h2>
                    <p className="text-muted-foreground">
                        Visualize os templates disponíveis para correção de provas
                    </p>
                </div>

                {isLoading ? (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3, 4].map((i) => (
                            <Card key={i}>
                                <CardHeader>
                                    <Skeleton className="h-6 w-3/4" />
                                    <Skeleton className="h-4 w-1/2" />
                                </CardHeader>
                                <CardContent>
                                    <Skeleton className="h-20 w-full" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : templates.length === 0 ? (
                    <Card>
                        <CardContent className="py-8 text-center">
                            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">
                                Nenhum template disponível no momento.
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {templates.map((template) => (
                            <Card key={template.id} className="hover:shadow-md transition-shadow">
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <CardTitle className="text-lg">{template.name}</CardTitle>
                                            <CardDescription>Versão {template.version}</CardDescription>
                                        </div>
                                        <Badge variant="outline" className={getQuestionCountColor(template.question_count)}>
                                            {template.question_count}q
                                        </Badge>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        {/* Template Info */}
                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div className="flex items-center gap-2">
                                                <Grid className="h-4 w-4 text-muted-foreground" />
                                                <span>
                                                    <strong>{template.question_count}</strong> questões
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-muted-foreground">Alternativas:</span>
                                                <span className="font-medium">
                                                    {'ABCDE'.slice(0, template.alternatives_count)}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Visual representation */}
                                        <div className="p-3 bg-muted rounded-lg">
                                            <div className="flex items-center justify-center gap-1">
                                                {Array.from({ length: Math.min(template.alternatives_count, 5) }).map((_, i) => (
                                                    <div
                                                        key={i}
                                                        className="w-6 h-6 rounded-full border-2 border-muted-foreground/30 flex items-center justify-center text-xs text-muted-foreground"
                                                    >
                                                        {String.fromCharCode(65 + i)}
                                                    </div>
                                                ))}
                                            </div>
                                            <p className="text-xs text-center text-muted-foreground mt-2">
                                                Exemplo de marcação
                                            </p>
                                        </div>

                                        {/* Actions */}
                                        <div className="flex gap-2">
                                            <Button variant="outline" size="sm" className="flex-1" asChild>
                                                <Link to={`/answer-keys/new?templateId=${template.id}`}>
                                                    Criar Gabarito
                                                </Link>
                                            </Button>
                                            <Button variant="outline" size="sm" className="flex-1" asChild>
                                                <Link to={`/corrections/new?templateId=${template.id}`}>
                                                    Nova Correção
                                                </Link>
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* Info Card */}
                <Card className="mt-8">
                    <CardHeader>
                        <CardTitle className="text-base">Sobre os Templates</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground space-y-2">
                        <p>
                            Os templates definem o formato das folhas de resposta que podem ser corrigidas pelo sistema.
                        </p>
                        <p>
                            Cada template especifica o número de questões e alternativas disponíveis.
                            Ao criar um gabarito ou iniciar uma correção, você deve selecionar o template correspondente
                            à folha de resposta utilizada.
                        </p>
                        <p>
                            Templates disponíveis: 10, 20, 50 ou 100 questões, com 4 (A-D) ou 5 (A-E) alternativas.
                        </p>
                    </CardContent>
                </Card>
            </main>
        </div>
    )
}
