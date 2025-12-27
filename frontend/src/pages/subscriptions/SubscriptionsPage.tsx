/**
 * SubscriptionsPage - Displays plans and manages subscriptions
 * Requirements: 10.1, 10.2, 10.5
 */

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import {
    subscriptionService,
    type Plan,
    type SubscriptionWithPlan,
} from '@/services/subscriptionService'
import { AlertCircle, Check, CreditCard, ExternalLink, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

export function SubscriptionsPage() {
    const { user } = useAuth()
    const [plans, setPlans] = useState<Plan[]>([])
    const [currentSubscription, setCurrentSubscription] = useState<SubscriptionWithPlan | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isCheckoutLoading, setIsCheckoutLoading] = useState<string | null>(null)
    const [isPortalLoading, setIsPortalLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        async function loadData() {
            setIsLoading(true)
            setError(null)

            try {
                const [plansData, subscriptionData] = await Promise.all([
                    subscriptionService.getPlans(),
                    user ? subscriptionService.getCurrentSubscription(user.id) : null,
                ])

                setPlans(plansData)
                setCurrentSubscription(subscriptionData)
            } catch (err) {
                setError('Erro ao carregar planos. Tente novamente.')
                console.error(err)
            } finally {
                setIsLoading(false)
            }
        }

        loadData()
    }, [user])

    const handleSubscribe = async (planId: string) => {
        setIsCheckoutLoading(planId)
        setError(null)

        try {
            const checkoutUrl = await subscriptionService.createCheckoutSession(planId)
            if (checkoutUrl) {
                window.location.href = checkoutUrl
            } else {
                setError('Erro ao criar sessão de pagamento. Tente novamente.')
            }
        } catch (err) {
            setError('Erro ao processar assinatura. Tente novamente.')
            console.error(err)
        } finally {
            setIsCheckoutLoading(null)
        }
    }

    const handleManageSubscription = async () => {
        setIsPortalLoading(true)
        setError(null)

        try {
            const portalUrl = await subscriptionService.createPortalSession()
            if (portalUrl) {
                window.location.href = portalUrl
            } else {
                setError('Erro ao abrir portal de gerenciamento. Tente novamente.')
            }
        } catch (err) {
            setError('Erro ao abrir portal. Tente novamente.')
            console.error(err)
        } finally {
            setIsPortalLoading(false)
        }
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'ACTIVE':
                return <Badge className="bg-green-500">Ativa</Badge>
            case 'PAST_DUE':
                return <Badge variant="destructive">Pagamento Pendente</Badge>
            case 'CANCELED':
                return <Badge variant="secondary">Cancelada</Badge>
            default:
                return <Badge variant="outline">{status}</Badge>
        }
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="container mx-auto py-8 px-4">
            <div className="max-w-5xl mx-auto">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold mb-2">Planos e Assinaturas</h1>
                    <p className="text-muted-foreground">
                        Escolha o plano ideal para suas necessidades de correção de provas
                    </p>
                </div>

                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Erro</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {/* Current Subscription */}
                {currentSubscription && (
                    <Card className="mb-8 border-primary">
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle className="flex items-center gap-2">
                                        <CreditCard className="h-5 w-5" />
                                        Sua Assinatura Atual
                                    </CardTitle>
                                    <CardDescription>
                                        Plano {currentSubscription.plan.name}
                                    </CardDescription>
                                </div>
                                {getStatusBadge(currentSubscription.status)}
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-muted-foreground">Tokens mensais:</span>
                                    <span className="ml-2 font-medium">
                                        {currentSubscription.plan.monthlyTokens.toLocaleString()}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground">Próxima renovação:</span>
                                    <span className="ml-2 font-medium">
                                        {new Date(currentSubscription.currentPeriodEnd).toLocaleDateString('pt-BR')}
                                    </span>
                                </div>
                            </div>

                            {currentSubscription.status === 'PAST_DUE' && (
                                <Alert variant="destructive" className="mt-4">
                                    <AlertCircle className="h-4 w-4" />
                                    <AlertTitle>Pagamento Pendente</AlertTitle>
                                    <AlertDescription>
                                        Seu pagamento está pendente. Atualize seu método de pagamento para continuar usando o serviço.
                                    </AlertDescription>
                                </Alert>
                            )}
                        </CardContent>
                        <CardFooter>
                            <Button
                                variant="outline"
                                onClick={handleManageSubscription}
                                disabled={isPortalLoading}
                            >
                                {isPortalLoading ? (
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                ) : (
                                    <ExternalLink className="h-4 w-4 mr-2" />
                                )}
                                Gerenciar Assinatura
                            </Button>
                        </CardFooter>
                    </Card>
                )}

                {/* Plans Grid */}
                <div className="grid md:grid-cols-3 gap-6">
                    {plans.map((plan) => {
                        const isCurrentPlan = currentSubscription?.planId === plan.id
                        const isPopular = plan.id === 'pro' // Assuming 'pro' is the popular plan

                        return (
                            <Card
                                key={plan.id}
                                className={`relative ${isPopular ? 'border-primary shadow-lg' : ''} ${isCurrentPlan ? 'bg-primary/5' : ''
                                    }`}
                            >
                                {isPopular && (
                                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                        <Badge className="bg-primary">Mais Popular</Badge>
                                    </div>
                                )}
                                <CardHeader>
                                    <CardTitle>{plan.name}</CardTitle>
                                    <CardDescription>{plan.description}</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="mb-4">
                                        <span className="text-3xl font-bold">
                                            {subscriptionService.formatPrice(plan.monthlyPriceCents)}
                                        </span>
                                        <span className="text-muted-foreground">/mês</span>
                                    </div>

                                    <div className="mb-4 p-3 bg-muted rounded-lg">
                                        <span className="text-2xl font-bold text-primary">
                                            {plan.monthlyTokens.toLocaleString()}
                                        </span>
                                        <span className="text-muted-foreground ml-2">tokens/mês</span>
                                    </div>

                                    <ul className="space-y-2">
                                        {plan.features.map((feature, index) => (
                                            <li key={index} className="flex items-center gap-2 text-sm">
                                                <Check className="h-4 w-4 text-green-500 shrink-0" />
                                                <span>{feature}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </CardContent>
                                <CardFooter>
                                    {isCurrentPlan ? (
                                        <Button className="w-full" disabled>
                                            Plano Atual
                                        </Button>
                                    ) : (
                                        <Button
                                            className="w-full"
                                            variant={isPopular ? 'default' : 'outline'}
                                            onClick={() => handleSubscribe(plan.id)}
                                            disabled={isCheckoutLoading !== null}
                                        >
                                            {isCheckoutLoading === plan.id ? (
                                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                            ) : null}
                                            {currentSubscription ? 'Mudar para este plano' : 'Assinar'}
                                        </Button>
                                    )}
                                </CardFooter>
                            </Card>
                        )
                    })}
                </div>

                {/* FAQ or additional info */}
                <div className="mt-12 text-center text-sm text-muted-foreground">
                    <p>
                        Todos os planos incluem suporte por email e acesso a todas as funcionalidades.
                    </p>
                    <p className="mt-2">
                        Dúvidas? Entre em contato conosco em{' '}
                        <a href="mailto:suporte@corrigeprovas.com" className="text-primary hover:underline">
                            suporte@corrigeprovas.com
                        </a>
                    </p>
                </div>
            </div>
        </div>
    )
}

export default SubscriptionsPage
