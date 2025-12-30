import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/contexts/AuthContext'
import { ArrowLeft, CheckCircle2 } from 'lucide-react'

const loginSchema = z.object({
    email: z.string().email('Email inválido'),
    password: z.string().min(6, 'Senha deve ter pelo menos 6 caracteres'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export function LoginPage() {
    const { signIn, signInWithGoogle } = useAuth()
    const navigate = useNavigate()
    const [error, setError] = useState<string | null>(null)
    const [isLoading, setIsLoading] = useState(false)

    const form = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            email: '',
            password: '',
        },
    })

    const onSubmit = async (values: LoginFormValues) => {
        setError(null)
        setIsLoading(true)

        try {
            const { error } = await signIn(values.email, values.password)
            if (error) {
                setError(error.message)
            } else {
                navigate('/')
            }
        } catch {
            setError('Erro ao fazer login. Tente novamente.')
        } finally {
            setIsLoading(false)
        }
    }

    const handleGoogleSignIn = async () => {
        setError(null)
        try {
            await signInWithGoogle()
        } catch {
            setError('Erro ao fazer login com Google. Tente novamente.')
        }
    }

    return (
        <div className="min-h-screen w-full flex">
            {/* Left Side - Visuals */}
            <div className="hidden lg:flex w-1/2 bg-background relative overflow-hidden items-center justify-center p-12">
                <div className="absolute inset-0 bg-primary/5 dark:bg-primary/10" />
                <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-primary/30 to-transparent blur-[120px] rounded-full animate-pulse" />
                <div className="relative z-10 max-w-lg text-left">
                    <h1 className="text-5xl font-bold tracking-tight mb-6">
                        Correção automática, <br />
                        <span className="text-gradient">resultados instantâneos.</span>
                    </h1>
                    <p className="text-xl text-muted-foreground mb-8">
                        Economize horas de trabalho manual. Digitalize, corrija e analise o desempenho dos seus alunos em minutos.
                    </p>
                    <div className="space-y-4">
                        {['Correção via IA', 'Relatórios Detalhados', 'Exportação para Excel'].map((feature) => (
                            <div key={feature} className="flex items-center gap-3">
                                <CheckCircle2 className="h-5 w-5 text-primary" />
                                <span className="text-lg">{feature}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right Side - Form */}
            <div className="flex-1 flex flex-col items-center justify-center p-4 lg:p-12 relative bg-background/50 backdrop-blur-sm">
                <Link to="/" className="absolute top-8 left-8 text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2">
                    <ArrowLeft className="h-4 w-4" /> Voltar
                </Link>

                <div className="w-full max-w-sm space-y-8 glass p-8 rounded-2xl animate-fade-in-up">
                    <div className="text-center space-y-2">
                        <h2 className="text-3xl font-bold">Bem-vindo de volta</h2>
                        <p className="text-muted-foreground">Entre na sua conta para continuar</p>
                    </div>

                    {error && (
                        <Alert variant="destructive">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                            <FormField
                                control={form.control}
                                name="email"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Email</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="email"
                                                placeholder="seu@email.com"
                                                className="bg-background/50"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="password"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Senha</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="password"
                                                placeholder="••••••••"
                                                className="bg-background/50"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <Button type="submit" className="w-full h-11 text-base shadow-lg shadow-primary/25" disabled={isLoading}>
                                {isLoading ? 'Entrando...' : 'Entrar'}
                            </Button>
                        </form>
                    </Form>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-white/10" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-background px-2 text-muted-foreground">
                                Ou continue com
                            </span>
                        </div>
                    </div>

                    <Button
                        variant="outline"
                        className="w-full h-11 bg-background/50 hover:bg-background/80"
                        onClick={handleGoogleSignIn}
                        type="button"
                    >
                        <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                            <path
                                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                fill="#4285F4"
                            />
                            <path
                                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                fill="#34A853"
                            />
                            <path
                                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                fill="#FBBC05"
                            />
                            <path
                                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                fill="#EA4335"
                            />
                        </svg>
                        Google
                    </Button>

                    <div className="flex flex-col space-y-4 text-center text-sm">
                        <Link
                            to="/forgot-password"
                            className="text-muted-foreground hover:text-primary transition-colors"
                        >
                            Esqueceu sua senha?
                        </Link>
                        <p className="text-muted-foreground">
                            Não tem uma conta?{' '}
                            <Link to="/register" className="text-primary hover:underline font-medium">
                                Cadastre-se gratuitamente
                            </Link>
                        </p>
                    </div>
                </div>
                <div className="mt-8 text-center text-xs text-muted-foreground">
                    &copy; {new Date().getFullYear()} CorrigeProvas. Todos os direitos reservados.
                </div>
            </div>
        </div>
    )
}
