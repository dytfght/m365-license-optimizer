import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';

/**
 * Hook to protect routes and ensure user is authenticated
 * Redirects to /login if user is not authenticated
 * 
 * @returns { user, loading } - Current user and loading state
 */
export const useRequireAuth = () => {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !user) {
            router.push('/login');
        }
    }, [user, loading, router]);

    return { user, loading };
};
