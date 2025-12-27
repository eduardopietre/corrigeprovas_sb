/**
 * UsageDashboardPage - Displays token balance and usage history
 * Requirements: 9.4
 */

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table'
import { useAuth } from '@/contexts/AuthContext'
import { subscriptionService, type SubscriptionWithPlan } from '@/services/subscriptionService'
import {
    usageService,
    type UsageLedgerEntry,
    type UsageStats,
} from '@/services/usageService'
import { ChevronLeft, ChevronRight, Coins, History, Loader2, TrendingDown, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'

const PAGE_SIZE = 10

export function UsageDashboardPage() {
    const { user } = useAuth()
    const [stats, setStats] = useState<UsageStats | null>(null)
    const [subscription, setSubscription] = useState<SubscriptionWithPlan | null>(null)
    const [history, setHistory] = useState<UsageLedgerEntry[]>([])
    const [totalEntries, setTotalEntries] = useState(0)
    const [currentPage, setCurrentPage] = useState(1)
    const [isLoading, setIsLoading] = useState(true)
    const [isLoadingHistory, setIsLoadingHistory] = useState(false)

    useEffect(() => {
        async function loadData() {
            if (!user) return

            setIsLoading(true)
            try {
                const [statsData, subscriptionData, historyData] = await Promise.all([
                    usageService.getUsageStats(user.id),
                    subscriptionService.getCurrentSubscription(user.id),
                    usageService.getUsageHistory(user.id, 1, PAGE_SIZE),
                ])

                setStats(statsData)
                setSubscription(subscriptionData)
                setHistory(historyData.entries)
                setTotalEntries(historyData.total)
            } catch (err) {
                console.error('Failed to load usage data:', err)
            } finally {
                setIsLoading(false)
            }
        }

        loadData()
    }, [user])

    const loadPage = async (page: number) => {
        if (!user) return

        setIsLoadingHistory(true)
        try {
            const historyData = await usageService.getUsageHistory(user.id, page, PAGE_SIZE)
            setHistory(historyData.entries)
            setCurrentPage(page)
        } catch (err) {
            console.error('Failed to load history:', err)
        } finally {
            setIsLoadingHistory(false)
        }
    }

    const totalPages = Math.ceil(totalEntries / PAGE_SIZE)

    const getUsagePercentage = (): number => {
        if (!subscription || !stats) return 0
        const monthlyTokens = subscription.plan.monthlyTokens
        if (monthlyTokens === 0) return 0
        return Math.min(100, (stats.totalUsed / monthlyTokens) * 100)
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
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Consumo de Tokens</h1>
                    <p className="text-muted-foreground">
                        Acompanhe seu saldo e histórico de uso de tokens
                    </p>
                </div>

                {/* Stats Cards */}
                <div className="grid md:grid-cols-3 gap-6 mb-8">
                    {/* Balance Card */}
                    <Card>
                        <CardHeader className="pb-2">
                            <CardDescription className="flex items-center gap-2">
                                <Coins className="h-4 w-4" />
                                Saldo Atual
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-primary">
                                {stats?.balance.toLocaleString() || 0}
                            </div>
                            <p className="text-sm text-muted-foreground mt-1">
                                tokens disponíveis
                            </p>
                        </CardContent>
                    </Card>

                    {/* Used This Month Card */}
                    <Card>
                        <CardHeader className="pb-2">
                            <CardDescription className="flex items-center gap-2">
                                <TrendingDown className="h-4 w-4" />
                                Usado Este Mês
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-orange-500">
                                {stats?.totalUsed.toLocaleString() || 0}
                            </div>
                            <p className="text-sm text-muted-foreground mt-1">
                                tokens consumidos
                            </p>
                        </CardContent>
                    </Card>

                    {/* Credits Card */}
                    <Card>
                        <CardHeader className="pb-2">
                            <CardDescription className="flex items-center gap-2">
                                <TrendingUp className="h-4 w-4" />
                                Total de Créditos
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-green-500">
                                {stats?.totalCredits.toLocaleString() || 0}
                            </div>
                            <p className="text-sm text-muted-foreground mt-1">
                                tokens recebidos
                            </p>
                        </CardContent>
                    </Card>
                </div>

                {/* Usage Progress */}
                {subscription && (
                    <Card className="mb-8">
                        <CardHeader>
                            <CardTitle>Uso do Plano</CardTitle>
                            <CardDescription>
                                Plano {subscription.plan.name} - {subscription.plan.monthlyTokens.toLocaleString()} tokens/mês
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span>Usado: {stats?.totalUsed.toLocaleString() || 0}</span>
                                    <span>Limite: {subscription.plan.monthlyTokens.toLocaleString()}</span>
                                </div>
                                <Progress value={getUsagePercentage()} className="h-3" />
                                <p className="text-sm text-muted-foreground">
                                    {getUsagePercentage().toFixed(1)}% do limite mensal utilizado
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Usage History */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <History className="h-5 w-5" />
                            Histórico de Uso
                        </CardTitle>
                        <CardDescription>
                            {totalEntries} registros encontrados
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isLoadingHistory ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                            </div>
                        ) : history.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                Nenhum registro de uso encontrado
                            </div>
                        ) : (
                            <>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Data</TableHead>
                                            <TableHead>Descrição</TableHead>
                                            <TableHead className="text-right">Tokens</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {history.map((entry) => (
                                            <TableRow key={entry.id}>
                                                <TableCell className="text-muted-foreground">
                                                    {new Date(entry.createdAt).toLocaleDateString('pt-BR', {
                                                        day: '2-digit',
                                                        month: '2-digit',
                                                        year: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit',
                                                    })}
                                                </TableCell>
                                                <TableCell>
                                                    <div className="flex items-center gap-2">
                                                        {usageService.getReasonLabel(entry.reason)}
                                                        {entry.jobId && (
                                                            <Badge variant="outline" className="text-xs">
                                                                Job
                                                            </Badge>
                                                        )}
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <span
                                                        className={
                                                            entry.deltaTokens >= 0
                                                                ? 'text-green-600 font-medium'
                                                                : 'text-red-600 font-medium'
                                                        }
                                                    >
                                                        {entry.deltaTokens >= 0 ? '+' : ''}
                                                        {entry.deltaTokens.toLocaleString()}
                                                    </span>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>

                                {/* Pagination */}
                                {totalPages > 1 && (
                                    <div className="flex items-center justify-between mt-4">
                                        <p className="text-sm text-muted-foreground">
                                            Página {currentPage} de {totalPages}
                                        </p>
                                        <div className="flex gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => loadPage(currentPage - 1)}
                                                disabled={currentPage === 1}
                                            >
                                                <ChevronLeft className="h-4 w-4" />
                                                Anterior
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => loadPage(currentPage + 1)}
                                                disabled={currentPage === totalPages}
                                            >
                                                Próxima
                                                <ChevronRight className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default UsageDashboardPage
