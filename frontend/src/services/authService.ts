import api from './api';
import { Token, User } from '../types';

export const authService = {
    login: async (username: string, password: string): Promise<Token> => {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await api.post<Token>('/auth/login', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
        }

        return response.data;
    },

    me: async (): Promise<User> => {
        const response = await api.get<User>('/users/me');
        return response.data;
    },

    logout: () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    },

    isAuthenticated: (): boolean => {
        if (typeof window === 'undefined') return false;
        return !!localStorage.getItem('token');
    }
};
