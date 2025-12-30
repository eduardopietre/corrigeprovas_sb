import { useQuery } from '@tanstack/react-query'
import { FileText, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/contexts/AuthContext'
import { examPersistenceService } from '@/services/examPersistenceService'

export function ExamsListPage() {
    const { user } = useAuth()
    const [searchTerm, setSearchTerm] = useState('')

    const { data: exams, isLoading } = useQuery({
        queryKey: ['exams', user?.id],
        queryFn: () => {
            if (!user?.id) return []
            return examPersistenceService.listExams(user.id)
        },
        enabled: !!user?.id,
    })

    const filteredExams = exams?.filter((exam) =>
        exam.name.toLowerCase().includes(searchTerm.toLowerCase())
    )

    return (
        <div className="min-h-screen bg-background">
            <header className="sticky top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <Link to="/dashboard" className="text-xl font-bold tracking-tight">
                        Corrige<span className="text-primary">Provas</span>
                    </Link>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8 animate-fade-in-up">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Minhas Provas</h1>
                        <p className="text-muted-foreground">
                            Gerencie suas provas e variantes
                        </p>
                    </div>
                    <Button asChild size="lg" className="shadow-lg shadow-primary/25">
                        <Link to="/exams/new">
                            <Plus className="mr-2 h-5 w-5" />
                            Nova Prova
                        </Link>
                    </Button>
                </div>

                {/* Search Bar */}
                <div className="relative mb-8 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Buscar provas..."
                        className="pl-10 bg-card/50 backdrop-blur-sm border-white/10"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                {isLoading ? (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3].map((i) => (
                            <Card key={i} className="glass h-[200px] animate-pulse">
                                <CardHeader>
                                    <div className="h-6 w-2/3 bg-muted rounded" />
                                    <div className="h-4 w-1/2 bg-muted rounded mt-2" />
                                </CardHeader>
                            </Card>
                        ))}
                    </div>
                ) : filteredExams?.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
                            <FileText className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="text-xl font-semibold mb-2">Nenhuma prova encontrada</h3>
                        <p className="text-muted-foreground mb-6">
                            Você ainda não criou nenhuma prova. Comece agora!
                        </p>
                        <Button asChild>
                            <Link to="/exams/new">Criar Prova</Link>
                        </Button>
                    </div>
                ) : (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {filteredExams?.map((exam) => (
                            <Card key={exam.id} className="glass glass-hover group border-0 relative overflow-hidden transition-all duration-300 hover:-translate-y-1">
                                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <CardHeader className="relative z-10">
                                    <div className="flex justify-between items-start">
                                        <CardTitle className="text-xl truncate" title={exam.name}>
                                            {exam.name}
                                        </CardTitle>
                                    </div>
                                    <CardDescription>
                                        Criada em {new Date(exam.createdAt).toLocaleDateString()}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="relative z-10 space-y-4">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">Variantes</span>
                                        <span className="font-medium">{exam.variantCount}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">Randomização</span>
                                        <span className="font-medium">
                                            {exam.shuffleQuestions ? 'Sim' : 'Não'}
                                        </span>
                                    </div>

                                    <Button asChild variant="secondary" className="w-full mt-4 bg-white/5 hover:bg-white/10">
                                        <Link to={`/exams/${exam.id}`}>Detalhes</Link>
                                    </Button>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </main>
        </div>
    )
}
