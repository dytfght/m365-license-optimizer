import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { useTranslation } from 'react-i18next';
import { authService } from '../services/authService';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

export const LoginForm: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();
    const { t } = useTranslation();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await authService.login(username, password);
            router.push('/dashboard');
        } catch (err) {
            setError('Invalid credentials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full max-w-md space-y-8">
            <div>
                <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
                    {t('Login')}
                </h2>
            </div>
            <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                <div className="-space-y-px rounded-md shadow-sm">
                    <div>
                        <label htmlFor="username" className="sr-only">{t('Username')}</label>
                        <input
                            id="username"
                            name="username"
                            type="text"
                            required
                            className="relative block w-full rounded-t-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6 px-3"
                            placeholder={t('Username')}
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>
                    <div>
                        <label htmlFor="password" className="sr-only">{t('Password')}</label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            required
                            className="relative block w-full rounded-b-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6 px-3"
                            placeholder={t('Password')}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                </div>

                {error && <ErrorMessage message={error} />}

                <div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="group relative flex w-full justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white hover:bg-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
                    >
                        {loading ? <LoadingSpinner className="h-5 w-5 text-white" /> : t('Sign In')}
                    </button>
                </div>
            </form>
        </div>
    );
};
