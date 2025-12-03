import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { authService } from '../services/authService';
import { User } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (token: string) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    login: () => { },
    logout: () => { },
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const initAuth = async () => {
            if (authService.isAuthenticated()) {
                try {
                    const userData = await authService.me();
                    setUser(userData);
                } catch (error) {
                    console.error("Auth check failed", error);
                    authService.logout();
                }
            }
            setLoading(false);
        };

        initAuth();
    }, []);

    const login = async (token: string) => {
        localStorage.setItem('token', token);
        try {
            const userData = await authService.me();
            setUser(userData);
            router.push('/dashboard');
        } catch (error) {
            console.error("Failed to fetch user profile after login", error);
            // Optionally handle error (e.g. logout if token is invalid)
        }
    };

    const logout = () => {
        authService.logout();
        setUser(null);
    };

    if (loading) {
        return <div className="h-screen flex items-center justify-center"><LoadingSpinner /></div>;
    }

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
