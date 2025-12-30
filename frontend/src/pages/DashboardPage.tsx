import { FileText, Key, LayoutTemplate, LogOut, Plus, User } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/contexts/AuthContext'

export function DashboardPage() {
    const { user, signOut } = useAuth()

    const handleSignOut = async () => {
        await signOut()
    }

    const greeting = () => {
        const hour = new Date().getHours()
        if (hour < 12) return 'Bom dia'
        if (hour < 18) return 'Boa tarde'
        return 'Boa noite'
    }

    return (
        <div className="min-h-screen">
            {/* Header */}
            <header className="sticky top-0 z-50 border-b border-white/10 bg-background/80 backdrop-blur-md">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <Link to="/" className="text-xl font-bold tracking-tight">
                        Corrige<span className="text-primary">Provas</span>
                    </Link>

                    <div className="flex items-center gap-4">
                        <span className="text-sm text-muted-foreground hidden md:inline-block">
                            {user?.email}
                        </span>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="rounded-full ring-offset-background transition-colors hover:bg-secondary">
                                    <User className="h-5 w-5" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="glass">
                                <DropdownMenuLabel>Minha Conta</DropdownMenuLabel>
                                <DropdownMenuSeparator className="bg-white/10" />
                                <DropdownMenuItem onClick={handleSignOut} className="text-destructive focus:text-destructive">
                                    <LogOut className="mr-2 h-4 w-4" />
                                    Sair
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8 animate-fade-in-up">
                <div className="mb-8 space-y-2">
                    <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
                        {greeting()}, <span className="text-gradient">{user?.email?.split('@')[0]}</span>
                    </h1>
                    <p className="text-muted-foreground text-lg">
                        Gerencie suas provas e correções com agilidade.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 auto-rows-[180px]">
                    {/* New Correction - Featured Card */}
                    <Card className="glass glass-hover md:col-span-2 lg:col-span-1 row-span-2 relative overflow-hidden group border-0">
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                        <CardHeader className="relative z-10">
                            <CardTitle className="flex items-center gap-2 text-2xl">
                                <Plus className="h-6 w-6 text-primary" />
                                Nova Correção
                            </CardTitle>
                            <CardDescription className="text-base pt-2">
                                Inicie o processo de correção digitalizando folhas de resposta
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="relative z-10 h-full flex flex-col justify-end pb-8">
                            <Button asChild size="lg" className="w-full sm:w-auto shadow-lg shadow-primary/25">
                                <Link to="/corrections/new">Começar Agora</Link>
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Stats / Recent Activity Placeholder */}
                    <Card className="glass glass-hover border-0 flex flex-col justify-between">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <FileText className="h-5 w-5 text-blue-400" />
                                Correções Recentes
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">12</div>
                            <p className="text-xs text-muted-foreground">Correções este mês</p>
                            <Button asChild variant="link" className="px-0 mt-2 text-primary">
                                <Link to="/corrections">Ver todas &rarr;</Link>
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Answer Keys */}
                    <Card className="glass glass-hover border-0 flex flex-col justify-between">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <Key className="h-5 w-5 text-amber-400" />
                                Gabaritos
                            </CardTitle>
                            <CardDescription>
                                Gerencie as respostas das provas
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button asChild variant="outline" className="w-full bg-transparent hover:bg-white/5">
                                <Link to="/answer-keys">Gerenciar</Link>
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Templates */}
                    <Card className="glass glass-hover border-0 flex flex-col justify-between">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <LayoutTemplate className="h-5 w-5 text-emerald-400" />
                                Templates
                            </CardTitle>
                            <CardDescription>
                                Modelos de folha de resposta
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button asChild variant="outline" className="w-full bg-transparent hover:bg-white/5">
                                <Link to="/templates">Visualizar</Link>
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Exam Builder */}
                    <Card className="glass glass-hover border-0 flex flex-col justify-between">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <FileText className="h-5 w-5 text-pink-400" />
                                Criador de Provas
                            </CardTitle>
                            <CardDescription>
                                Crie provas com múltiplas variantes
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Button asChild variant="outline" className="w-full bg-transparent hover:bg-white/5">
                                <Link to="/exams">Minhas Provas</Link>
                            </Button>
                        </CardContent>
                    </Card>

                </div>
            </main>
        </div>
    )
}

