import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useTranslation } from 'react-i18next';
import { authService } from '../services/authService';
import { LogOut, Globe } from 'lucide-react';

export const Navbar: React.FC = () => {
    const { t, i18n } = useTranslation();
    const router = useRouter();

    const handleLogout = () => {
        authService.logout();
    };

    const toggleLanguage = () => {
        const newLang = i18n.language === 'en' ? 'fr' : 'en';
        i18n.changeLanguage(newLang);
    };

    return (
        <nav className="bg-white shadow">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 justify-between">
                    <div className="flex">
                        <div className="flex flex-shrink-0 items-center">
                            <span className="text-xl font-bold text-primary">M365 Optimizer</span>
                        </div>
                        <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                            <Link href="/dashboard" className={`inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium ${router.pathname === '/dashboard' ? 'border-primary text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                {t('Dashboard')}
                            </Link>
                            <Link href="/admin/sku-mapping" className={`inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium ${router.pathname.startsWith('/admin') ? 'border-primary text-gray-900' : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}`}>
                                {t('Admin')}
                            </Link>
                        </div>
                    </div>
                    <div className="flex items-center">
                        <button
                            onClick={toggleLanguage}
                            className="p-2 text-gray-400 hover:text-gray-500"
                            title="Switch Language"
                        >
                            <Globe className="h-6 w-6" />
                        </button>
                        <button
                            onClick={handleLogout}
                            className="ml-3 p-2 text-gray-400 hover:text-gray-500"
                            title={t('Logout')}
                        >
                            <LogOut className="h-6 w-6" />
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};
