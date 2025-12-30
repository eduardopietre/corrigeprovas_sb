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

const registerSchema = z.object({
    email: z.string().email('Email inválido'),
    password: z.string().min(6, 'Senha deve ter pelo menos 6 caracteres'),
    confirmPassword: z.string().min(6, 'Confirmação de senha deve ter pelo menos 6 caracteres'),
}).refine((data) => data.password === data.confirmPassword, {
    message: 'As senhas não coincidem',
    path: ['confirmPassword'],
})

type RegisterFormValues = z.infer<typeof registerSchema>

export function RegisterPage() {
    const { signUp, signInWithGoogle } = useAuth()
    const navigate = useNavigate()
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)
    const [isLoading, setIsLoading] = useState(false)

    const form = useForm<RegisterFormValues>({
        resolver: zodResolver(registerSchema),
        defaultValues: {
            email: '',
            password: '',
            confirmPassword: '',
        },
    })

    const onSubmit = async (values: RegisterFormValues) => {
        setError(null)
        setSuccess(null)
        setIsLoading(true)

        try {
            const { error, data } = await signUp(values.email, values.password)
            if (error) {
                setError(error.message)
            } else if (data.user && !data.session) {
                // Email confirmation required
                setSuccess('Cadastro realizado! Verifique seu email para confirmar a conta.')
            } else {
                navigate('/')
            }
        } catch {
            setError('Erro ao criar conta. Tente novamente.')
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
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-bl from-primary/30 to-transparent blur-[120px] rounded-full animate-pulse" />
                <div className="relative z-10 max-w-lg text-left">
                    <h1 className="text-5xl font-bold tracking-tight mb-6">
                        Comece a corrigir <br />
                        <span className="text-gradient">de forma inteligente.</span>
                    </h1>
                    <p className="text-xl text-muted-foreground mb-8">
                        Junte-se a milhares de professores e instituições que já modernizaram seu processo de avaliação.
                    </p>
                    <div className="space-y-4">
                        {['Plano Gratuito Inicial', 'Templates Customizáveis', 'Suporte Técnico'].map((feature) => (
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
                        <h2 className="text-3xl font-bold">Crie sua Conta</h2>
                        <p className="text-muted-foreground">Preencha seus dados para começar</p>
                    </div>

                    {error && (
                        <Alert variant="destructive">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    {success && (
                        <Alert className="border-primary/50 text-primary">
                            <AlertDescription>{success}</AlertDescription>
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

                            <FormField
                                control={form.control}
                                name="confirmPassword"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Confirmar Senha</FormLabel>
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
                                {isLoading ? 'Criando conta...' : 'Criar Conta'}
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

                    <div className="mt-4 text-center text-sm">
                        <p className="text-muted-foreground">
                            Já tem uma conta?{' '}
                            <Link to="/login" className="text-primary hover:underline font-medium">
                                Entrar
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
