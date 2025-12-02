import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import '../i18n';

const queryClient = new QueryClient();

export default function App({ Component, pageProps }: AppProps) {
    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <Component {...pageProps} />
            </AuthProvider>
        </QueryClientProvider>
    );
}
