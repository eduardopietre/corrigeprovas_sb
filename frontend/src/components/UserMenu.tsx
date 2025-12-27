/**
 * UserMenu - Dropdown menu for user actions with role-based options
 * Requirements: 1.6, 1.7
 */

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuGroup,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/contexts/AuthContext'
import { useRoles } from '@/hooks/useRoles'
import {
    Building,
    ChevronDown,
    Coins,
    CreditCard,
    Loader2,
    LogOut,
    Settings,
    Shield,
    User,
} from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export function UserMenu() {
    const { user, signOut } = useAuth()
    const { profile, roles, isAdmin, isInstitutionAdmin, isLoading } = useRoles()
    const navigate = useNavigate()
    const [isSigningOut, setIsSigningOut] = useState(false)

    const handleSignOut = async () => {
        setIsSigningOut(true)
        try {
            await signOut()
            navigate('/login')
        } catch (err) {
            console.error('Failed to sign out:', err)
        } finally {
            setIsSigningOut(false)
        }
    }

    if (!user) {
        return null
    }

    const displayName = profile?.displayName || user.email?.split('@')[0] || 'Usuário'
    const email = user.email || ''

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-4 w-4 text-primary" />
                    </div>
                    <span className="hidden md:inline-block max-w-[150px] truncate">
                        {displayName}
                    </span>
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end">
                <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium">{displayName}</p>
                        <p className="text-xs text-muted-foreground truncate">{email}</p>
                        {isLoading ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                            <div className="flex flex-wrap gap-1 mt-1">
                                {roles.map(role => (
                                    <Badge key={role} variant="secondary" className="text-xs">
                                        {role === 'ADMIN' && 'Admin'}
                                        {role === 'INSTITUTION_ADMIN' && 'Admin Inst.'}
                                        {role === 'USER' && 'Usuário'}
                                    </Badge>
                                ))}
                            </div>
                        )}
                    </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />

                {/* User options */}
                <DropdownMenuGroup>
                    <DropdownMenuItem onClick={() => navigate('/profile')}>
                        <User className="mr-2 h-4 w-4" />
                        Meu Perfil
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/usage')}>
                        <Coins className="mr-2 h-4 w-4" />
                        Consumo de Tokens
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/subscriptions')}>
                        <CreditCard className="mr-2 h-4 w-4" />
                        Assinatura
                    </DropdownMenuItem>
                </DropdownMenuGroup>

                {/* Institution Admin options */}
                {isInstitutionAdmin && (
                    <>
                        <DropdownMenuSeparator />
                        <DropdownMenuGroup>
                            <DropdownMenuLabel className="text-xs text-muted-foreground">
                                Instituição
                            </DropdownMenuLabel>
                            <DropdownMenuItem onClick={() => navigate('/institution/users')}>
                                <Building className="mr-2 h-4 w-4" />
                                Usuários da Instituição
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate('/institution/reports')}>
                                <Settings className="mr-2 h-4 w-4" />
                                Relatórios
                            </DropdownMenuItem>
                        </DropdownMenuGroup>
                    </>
                )}

                {/* Admin options */}
                {isAdmin && (
                    <>
                        <DropdownMenuSeparator />
                        <DropdownMenuGroup>
                            <DropdownMenuLabel className="text-xs text-muted-foreground">
                                Administração
                            </DropdownMenuLabel>
                            <DropdownMenuItem onClick={() => navigate('/admin/users')}>
                                <Shield className="mr-2 h-4 w-4" />
                                Gerenciar Usuários
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate('/admin/institutions')}>
                                <Building className="mr-2 h-4 w-4" />
                                Instituições
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate('/admin/plans')}>
                                <CreditCard className="mr-2 h-4 w-4" />
                                Planos
                            </DropdownMenuItem>
                        </DropdownMenuGroup>
                    </>
                )}

                <DropdownMenuSeparator />
                <DropdownMenuItem
                    onClick={handleSignOut}
                    disabled={isSigningOut}
                    className="text-destructive focus:text-destructive"
                >
                    {isSigningOut ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                        <LogOut className="mr-2 h-4 w-4" />
                    )}
                    Sair
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}

export default UserMenu
