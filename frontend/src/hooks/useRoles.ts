/**
 * useRoles - Hook for role-based access control
 * Requirements: 1.6, 1.7
 */

import { useAuth } from '@/contexts/AuthContext'
import { PERMISSIONS, roleService, type UserProfile, type UserRole } from '@/services/roleService'
import { useCallback, useEffect, useState } from 'react'

export interface UseRolesResult {
    roles: UserRole[]
    profile: UserProfile | null
    isLoading: boolean
    isAdmin: boolean
    isInstitutionAdmin: boolean
    hasRole: (role: UserRole) => boolean
    hasAnyRole: (roles: UserRole[]) => boolean
    hasPermission: (permission: keyof typeof PERMISSIONS) => boolean
    refresh: () => Promise<void>
}

export function useRoles(): UseRolesResult {
    const { user } = useAuth()
    const [roles, setRoles] = useState<UserRole[]>([])
    const [profile, setProfile] = useState<UserProfile | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    const loadRoles = useCallback(async () => {
        if (!user) {
            setRoles([])
            setProfile(null)
            setIsLoading(false)
            return
        }

        setIsLoading(true)
        try {
            const userProfile = await roleService.getUserProfile(user.id)
            if (userProfile) {
                setProfile(userProfile)
                setRoles(userProfile.roles)
            } else {
                setRoles(['USER'])
                setProfile(null)
            }
        } catch (err) {
            console.error('Failed to load roles:', err)
            setRoles(['USER'])
        } finally {
            setIsLoading(false)
        }
    }, [user])

    useEffect(() => {
        loadRoles()
    }, [loadRoles])

    const hasRole = useCallback((role: UserRole): boolean => {
        return roles.includes(role)
    }, [roles])

    const hasAnyRole = useCallback((checkRoles: UserRole[]): boolean => {
        return checkRoles.some(role => roles.includes(role))
    }, [roles])

    const hasPermission = useCallback((permission: keyof typeof PERMISSIONS): boolean => {
        const allowedRoles = PERMISSIONS[permission]
        return allowedRoles.some(role => roles.includes(role))
    }, [roles])

    const isAdmin = roles.includes('ADMIN')
    const isInstitutionAdmin = roles.includes('INSTITUTION_ADMIN')

    return {
        roles,
        profile,
        isLoading,
        isAdmin,
        isInstitutionAdmin,
        hasRole,
        hasAnyRole,
        hasPermission,
        refresh: loadRoles,
    }
}

export default useRoles
