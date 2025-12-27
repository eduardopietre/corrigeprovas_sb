import { ArrowLeft, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table'
import { supabase } from '@/lib/supabase'
import { answerKeyService } from '@/services'
import type { AnswerKey, Template } from '@/services/types'

interface AnswerKeyWithTemplate extends AnswerKey {
    template?: Template
}

export function AnswerKeysListPage() {
    const [answerKeys, setAnswerKeys] = useState<AnswerKeyWithTemplate[]>([])
    const [templates, setTemplates] = useState<Record<string, Template>>({})
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [deleteId, setDeleteId] = useState<string | null>(null)
    const [isDeleting, setIsDeleting] = useState(false)

    useEffect(() => {
        async function loadData() {
            try {
                // Load templates first
                const { data: templatesData } = await supabase
                    .from('templates')
                    .select('*')

                const templatesMap: Record<string, Template> = {}
                templatesData?.forEach((t) => {
                    templatesMap[t.id] = t as Template
                })
                setTemplates(templatesMap)

                // Load answer keys
                const { data, error } = await answerKeyService.list()

                if (error) {
                    setError(error.message)
                } else {
                    setAnswerKeys(data || [])
                }
            } catch (err) {
                setError('Erro ao carregar dados.')
            } finally {
                setIsLoading(false)
            }
        }

        loadData()
    }, [])

    const handleDelete = async () => {
        if (!deleteId) return

        setIsDeleting(true)
        const { error } = await answerKeyService.delete(deleteId)

        if (error) {
            setError(error.message)
        } else {
            setAnswerKeys((prev) => prev.filter((ak) => ak.id !== deleteId))
        }

        setIsDeleting(false)
        setDeleteId(null)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
        })
    }

    const truncateAnswers = (answers: string, maxLength = 20) => {
        if (answers.length <= maxLength) return answers
        return answers.slice(0, maxLength) + '...'
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" asChild>
                            <Link to="/dashboard">
                                <ArrowLeft className="h-5 w-5" />
                            </Link>
                        </Button>
                        <h1 className="text-xl font-bold">Gabaritos</h1>
                    </div>
                    <Button asChild>
                        <Link to="/answer-keys/new">
                            <Plus className="mr-2 h-4 w-4" />
                            Novo Gabarito
                        </Link>
                    </Button>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <Card>
                    <CardHeader>
                        <CardTitle>Seus Gabaritos</CardTitle>
                        <CardDescription>
                            Gerencie os gabaritos das suas provas
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <div className="space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="flex items-center gap-4">
                                        <Skeleton className="h-10 w-10 rounded-full" />
                                        <div className="space-y-2 flex-1">
                                            <Skeleton className="h-4 w-1/4" />
                                            <Skeleton className="h-3 w-1/2" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : answerKeys.length === 0 ? (
                            <div className="text-center py-8">
                                <p className="text-muted-foreground mb-4">
                                    Você ainda não tem nenhum gabarito.
                                </p>
                                <Button asChild>
                                    <Link to="/answer-keys/new">
                                        <Plus className="mr-2 h-4 w-4" />
                                        Criar Primeiro Gabarito
                                    </Link>
                                </Button>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Nome</TableHead>
                                        <TableHead>Template</TableHead>
                                        <TableHead>Respostas</TableHead>
                                        <TableHead>Data</TableHead>
                                        <TableHead></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {answerKeys.map((answerKey) => {
                                        const template = templates[answerKey.template_id]
                                        return (
                                            <TableRow key={answerKey.id}>
                                                <TableCell className="font-medium">
                                                    {answerKey.name || `Gabarito ${answerKey.id.slice(0, 8)}`}
                                                </TableCell>
                                                <TableCell>
                                                    {template ? (
                                                        <span className="text-sm">
                                                            {template.name} ({template.question_count}q)
                                                        </span>
                                                    ) : (
                                                        <span className="text-sm text-muted-foreground">-</span>
                                                    )}
                                                </TableCell>
                                                <TableCell>
                                                    <code className="text-xs bg-muted px-2 py-1 rounded">
                                                        {truncateAnswers(answerKey.answers_string)}
                                                    </code>
                                                </TableCell>
                                                <TableCell>{formatDate(answerKey.created_at)}</TableCell>
                                                <TableCell className="text-right">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => setDeleteId(answerKey.id)}
                                                    >
                                                        <Trash2 className="h-4 w-4 text-destructive" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        )
                                    })}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </main>

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Excluir Gabarito</DialogTitle>
                        <DialogDescription>
                            Tem certeza que deseja excluir este gabarito? Esta ação não pode ser desfeita.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteId(null)}>
                            Cancelar
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDelete}
                            disabled={isDeleting}
                        >
                            {isDeleting ? 'Excluindo...' : 'Excluir'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
