/**
 * RoleService - Manages user roles and permissions
 * Requirements: 1.6, 1.7
 */

import { supabase } from '@/lib/supabase'

export type UserRole = 'USER' | 'ADMIN' | 'INSTITUTION_ADMIN'

export interface UserRoleEntry {
    userId: string
    role: UserRole
}

export interface UserProfile {
    userId: string
    email: string
    displayName: string | null
    institutionId: string | null
    roles: UserRole[]
}

/**
 * Gets all roles for a user
 */
export async function getUserRoles(userId: string): Promise<UserRole[]> {
    const { data, error } = await supabase
        .from('user_roles')
        .select('role')
        .eq('user_id', userId)

    if (error || !data) {
        return ['USER'] // Default role
    }

    return data.map(r => r.role as UserRole)
}

/**
 * Gets the user profile with roles
 */
export async function getUserProfile(userId: string): Promise<UserProfile | null> {
    const { data: profileData, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', userId)
        .single()

    if (profileError || !profileData) {
        return null
    }

    const roles = await getUserRoles(userId)

    return {
        userId: profileData.user_id,
        email: profileData.email,
        displayName: profileData.display_name,
        institutionId: profileData.institution_id,
        roles,
    }
}

/**
 * Checks if a user has a specific role
 */
export async function hasRole(userId: string, role: UserRole): Promise<boolean> {
    const roles = await getUserRoles(userId)
    return roles.includes(role)
}

/**
 * Checks if a user has any of the specified roles
 */
export async function hasAnyRole(userId: string, roles: UserRole[]): Promise<boolean> {
    const userRoles = await getUserRoles(userId)
    return roles.some(role => userRoles.includes(role))
}

/**
 * Checks if a user is an admin
 */
export async function isAdmin(userId: string): Promise<boolean> {
    return hasRole(userId, 'ADMIN')
}

/**
 * Checks if a user is an institution admin
 */
export async function isInstitutionAdmin(userId: string): Promise<boolean> {
    return hasRole(userId, 'INSTITUTION_ADMIN')
}

/**
 * Permission definitions for different features
 */
export const PERMISSIONS = {
    // Correction features
    CREATE_CORRECTION: ['USER', 'ADMIN', 'INSTITUTION_ADMIN'] as UserRole[],
    VIEW_ALL_CORRECTIONS: ['ADMIN', 'INSTITUTION_ADMIN'] as UserRole[],

    // Template features
    CREATE_TEMPLATE: ['ADMIN'] as UserRole[],
    EDIT_TEMPLATE: ['ADMIN'] as UserRole[],
    DELETE_TEMPLATE: ['ADMIN'] as UserRole[],

    // User management
    VIEW_USERS: ['ADMIN', 'INSTITUTION_ADMIN'] as UserRole[],
    MANAGE_USERS: ['ADMIN'] as UserRole[],
    MANAGE_INSTITUTION_USERS: ['INSTITUTION_ADMIN'] as UserRole[],

    // Subscription management
    VIEW_ALL_SUBSCRIPTIONS: ['ADMIN'] as UserRole[],
    MANAGE_PLANS: ['ADMIN'] as UserRole[],

    // Institution management
    MANAGE_INSTITUTIONS: ['ADMIN'] as UserRole[],
    VIEW_INSTITUTION_DATA: ['INSTITUTION_ADMIN'] as UserRole[],
}

/**
 * Checks if a user has permission for a specific action
 */
export async function hasPermission(
    userId: string,
    permission: keyof typeof PERMISSIONS
): Promise<boolean> {
    const allowedRoles = PERMISSIONS[permission]
    return hasAnyRole(userId, allowedRoles)
}

export interface RoleService {
    getUserRoles: typeof getUserRoles
    getUserProfile: typeof getUserProfile
    hasRole: typeof hasRole
    hasAnyRole: typeof hasAnyRole
    isAdmin: typeof isAdmin
    isInstitutionAdmin: typeof isInstitutionAdmin
    hasPermission: typeof hasPermission
    PERMISSIONS: typeof PERMISSIONS
}

export const roleService: RoleService = {
    getUserRoles,
    getUserProfile,
    hasRole,
    hasAnyRole,
    isAdmin,
    isInstitutionAdmin,
    hasPermission,
    PERMISSIONS,
}

export default roleService
