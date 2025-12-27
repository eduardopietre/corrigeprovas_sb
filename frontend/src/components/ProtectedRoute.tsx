/**
 * ProtectedRoute - Route wrapper with authentication and role-based access
 * Requirements: 1.5, 1.6, 1.7
 */

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/contexts/AuthContext'
import { useRoles } from '@/hooks/useRoles'
import type { UserRole } from '@/services/roleService'
import { PERMISSIONS } from '@/services/roleService'
import { ShieldAlert } from 'lucide-react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

interface ProtectedRouteProps {
    children: React.ReactNode
    /** Required roles (user must have at least one) */
    requiredRoles?: UserRole[]
    /** Required permission */
    requiredPermission?: keyof typeof PERMISSIONS
    /** Redirect path when access is denied (default: shows access denied message) */
    redirectOnDeny?: string
}

export function ProtectedRoute({
    children,
    requiredRoles,
    requiredPermission,
    redirectOnDeny,
}: ProtectedRouteProps) {
    const { user, loading: authLoading } = useAuth()
    const { isLoading: rolesLoading, hasAnyRole, hasPermission } = useRoles()
    const location = useLocation()
    const navigate = useNavigate()

    const isLoading = authLoading || rolesLoading

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 bg-background">
                <div className="w-full max-w-md space-y-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-8 w-3/4" />
                    <Skeleton className="h-8 w-1/2" />
                </div>
            </div>
        )
    }

    if (!user) {
        // Redirect to login, but save the attempted location
        return <Navigate to="/login" state={{ from: location }} replace />
    }

    // Check role-based access
    const hasRequiredRole = !requiredRoles || hasAnyRole(requiredRoles)
    const hasRequiredPermission = !requiredPermission || hasPermission(requiredPermission)

    if (!hasRequiredRole || !hasRequiredPermission) {
        if (redirectOnDeny) {
            return <Navigate to={redirectOnDeny} replace />
        }

        return (
            <div className="min-h-screen flex items-center justify-center p-4 bg-background">
                <div className="w-full max-w-md">
                    <Alert variant="destructive">
                        <ShieldAlert className="h-4 w-4" />
                        <AlertTitle>Acesso Negado</AlertTitle>
                        <AlertDescription className="mt-2">
                            Você não tem permissão para acessar esta página.
                            {requiredRoles && (
                                <p className="mt-2 text-sm">
                                    Roles necessárias: {requiredRoles.join(', ')}
                                </p>
                            )}
                        </AlertDescription>
                    </Alert>
                    <div className="mt-4 flex gap-2">
                        <Button variant="outline" onClick={() => navigate(-1)}>
                            Voltar
                        </Button>
                        <Button onClick={() => navigate('/')}>
                            Ir para Home
                        </Button>
                    </div>
                </div>
            </div>
        )
    }

    return <>{children}</>
}

/**
 * AdminRoute - Shortcut for admin-only routes
 */
export function AdminRoute({ children }: { children: React.ReactNode }) {
    return (
        <ProtectedRoute requiredRoles={['ADMIN']}>
            {children}
        </ProtectedRoute>
    )
}

/**
 * InstitutionAdminRoute - Shortcut for institution admin routes
 */
export function InstitutionAdminRoute({ children }: { children: React.ReactNode }) {
    return (
        <ProtectedRoute requiredRoles={['ADMIN', 'INSTITUTION_ADMIN']}>
            {children}
        </ProtectedRoute>
    )
}

export default ProtectedRoute
