import { supabase } from '@/lib/supabase'
import type { AuthResponse, Session, User } from '@supabase/supabase-js'
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

interface AuthContextValue {
    user: User | null
    session: Session | null
    loading: boolean
    signIn(email: string, password: string): Promise<AuthResponse>
    signUp(email: string, password: string): Promise<AuthResponse>
    signOut(): Promise<void>
    resetPassword(email: string): Promise<{ error: Error | null }>
    signInWithGoogle(): Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [session, setSession] = useState<Session | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session)
            setUser(session?.user ?? null)
            setLoading(false)
        })

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (_event, session) => {
                setSession(session)
                setUser(session?.user ?? null)
                setLoading(false)
            }
        )

        return () => subscription.unsubscribe()
    }, [])

    const signIn = async (email: string, password: string): Promise<AuthResponse> => {
        const response = await supabase.auth.signInWithPassword({ email, password })
        return response
    }

    const signUp = async (email: string, password: string): Promise<AuthResponse> => {
        const response = await supabase.auth.signUp({ email, password })
        return response
    }

    const signOut = async (): Promise<void> => {
        await supabase.auth.signOut()
    }

    const resetPassword = async (email: string): Promise<{ error: Error | null }> => {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password`,
        })
        return { error }
    }

    const signInWithGoogle = async (): Promise<void> => {
        await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/`,
            },
        })
    }

    const value: AuthContextValue = {
        user,
        session,
        loading,
        signIn,
        signUp,
        signOut,
        resetPassword,
        signInWithGoogle,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
