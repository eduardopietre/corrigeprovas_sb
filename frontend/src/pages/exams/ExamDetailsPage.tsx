import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table'
import { supabase } from '@/lib/supabase'
import { examPersistenceService } from '@/services/examPersistenceService'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Calendar, Copy, Download, FileText, Trash2 } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

export function ExamDetailsPage() {
    const { examId } = useParams()
    const navigate = useNavigate()

    const { data: exam, isLoading: isLoadingExam } = useQuery({
        queryKey: ['exam', examId],
        queryFn: async () => {
            if (!examId) return null
            return await examPersistenceService.loadExam(examId)
        },
        enabled: !!examId
    })

    const { data: variants, isLoading: isLoadingVariants } = useQuery({
        queryKey: ['exam-variants', examId],
        queryFn: async () => {
            if (!examId) return []
            const data = await examPersistenceService.loadVariants(examId)
            // Fetch signed URLs for DOCX files
            const variantsWithUrls = await Promise.all(data.map(async (v: any) => {
                if (v.docx_storage_path) {
                    const { data: signedData } = await supabase.storage
                        .from('exam-documents')
                        .createSignedUrl(v.docx_storage_path, 3600) // 1 hour link
                    return { ...v, downloadUrl: signedData?.signedUrl }
                }
                return v
            }))
            return variantsWithUrls
        },
        enabled: !!examId
    })

    const handleCopyAnswerKey = (key: string) => {
        navigator.clipboard.writeText(key)
        toast.success('Gabarito copiado!')
    }

    const handleDelete = async () => {
        if (!examId || !confirm('Tem certeza que deseja excluir esta prova?')) return
        try {
            await examPersistenceService.deleteExam(examId)
            toast.success('Prova excluída')
            navigate('/exams')
        } catch (error) {
            console.error(error)
            toast.error('Erro ao excluir')
        }
    }

    if (isLoadingExam || isLoadingVariants) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
        )
    }

    if (!exam) {
        return (
            <div className="container mx-auto px-4 py-8">
                <p>Prova não encontrada.</p>
                <Button onClick={() => navigate('/exams')}>Voltar</Button>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background pb-20">
            <header className="sticky top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" onClick={() => navigate('/exams')}>
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div>
                            <h1 className="text-xl font-bold tracking-tight">{exam.name}</h1>
                            <p className="text-xs text-muted-foreground flex items-center gap-2">
                                <Calendar className="h-3 w-3" />
                                {new Date().toLocaleDateString()} {/* Placeholder, exam object doesn't have createdAt in ExamConfig but list has it */}
                            </p>
                        </div>
                    </div>
                    <Button variant="destructive" size="sm" onClick={handleDelete}>
                        <Trash2 className="h-4 w-4 mr-2" />
                        Excluir
                    </Button>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8 max-w-5xl animate-fade-in-up space-y-8">
                {/* Variants Section */}
                <div className="space-y-4">
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        <FileText className="h-6 w-6 text-primary" />
                        Cadernos de Prova
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {variants?.map((variant: any) => (
                            <Card key={variant.variantIndex} className="glass glass-hover">
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-lg">Modelo {variant.modelIdentifier}</CardTitle>
                                    <CardDescription>Variante {variant.variantIndex + 1}</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <Button
                                        className="w-full"
                                        disabled={!variant.downloadUrl}
                                        asChild={!!variant.downloadUrl}
                                    >
                                        {variant.downloadUrl ? (
                                            <a href={variant.downloadUrl} download>
                                                <Download className="mr-2 h-4 w-4" />
                                                Baixar Prova (DOCX)
                                            </a>
                                        ) : (
                                            <span>
                                                <Download className="mr-2 h-4 w-4" />
                                                Gerando...
                                            </span>
                                        )}
                                    </Button>

                                    <div className="bg-muted p-3 rounded-md text-sm font-mono break-all relative group">
                                        <p className="text-xs text-muted-foreground mb-1">Gabarito:</p>
                                        {variant.answerKey || variant.variant_answer_keys?.[0]?.answers_string}
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                            onClick={() => handleCopyAnswerKey(variant.answerKey || variant.variant_answer_keys?.[0]?.answers_string)}
                                        >
                                            <Copy className="h-3 w-3" />
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>

                {/* Summary Table */}
                <Card className="glass mt-8">
                    <CardHeader>
                        <CardTitle>Resumo dos Gabaritos</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[100px]">Questão</TableHead>
                                    {variants?.map((v: any) => (
                                        <TableHead key={v.modelIdentifier} className="text-center">
                                            Modelo {v.modelIdentifier}
                                        </TableHead>
                                    ))}
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {exam.questions.map((q, qIdx) => (
                                    <TableRow key={q.id}>
                                        <TableCell className="font-medium">{qIdx + 1}</TableCell>
                                        {variants?.map((v: any) => {
                                            // We need to find the answer for this question in this variant
                                            // Since we don't have the full variant structure here easily (it parses orders),
                                            // we can rely on the answer string if it maps 1:1 to questions
                                            // Answer string is like "ADC..." where char 0 is Q1, char 1 is Q2
                                            const answerKey = v.answerKey || v.variant_answer_keys?.[0]?.answers_string
                                            const answer = answerKey ? answerKey[qIdx] : '-'
                                            return (
                                                <TableCell key={v.modelIdentifier} className="text-center">
                                                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-xs">
                                                        {answer}
                                                    </span>
                                                </TableCell>
                                            )
                                        })}
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </main>
        </div>
    )
}
