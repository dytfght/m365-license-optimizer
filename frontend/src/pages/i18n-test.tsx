import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Languages } from 'lucide-react';

/**
 * Page de test pour le changement de langue (LOT 12)
 * URL: http://localhost:3001/i18n-test
 */
const I18nTestPage: React.FC = () => {
    const { t, i18n } = useTranslation();
    const [currentLang, setCurrentLang] = useState(i18n.language || 'en');

    const languages = [
        { code: 'en', name: 'English', flag: '🇬🇧' },
        { code: 'fr', name: 'Français', flag: '🇫🇷' },
    ];

    const changeLanguage = (lang: string) => {
        i18n.changeLanguage(lang);
        setCurrentLang(lang);
        // Sauvegarder la préférence dans le localStorage
        localStorage.setItem('preferredLanguage', lang);
        console.log(`🌐 Language changed to: ${lang}`);
    };

    // Section de test pour les différents namespaces
    const sections = [
        {
            title: 'Common',
            keys: ['login', 'logout', 'dashboard', 'save', 'cancel', 'loading'],
        },
        {
            title: 'User',
            keys: ['userPrincipalName', 'displayName', 'department', 'language'],
        },
        {
            title: 'Tenant',
            keys: ['tenantId', 'syncUsers', 'syncLicenses', 'details'],
        },
    ];

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* En-tête */}
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h1 className="text-3xl font-bold text-gray-900">
                            🌐 {t('common:login', 'Login')} - Test i18n (LOT 12)
                        </h1>
                        <div className="flex items-center space-x-2">
                            <Languages className="h-6 w-6 text-blue-600" />
                            <span className="text-sm font-medium">
                                {currentLang.toUpperCase()}
                            </span>
                        </div>
                    </div>
                    <p className="text-gray-600">
                        Testez le changement de langue en temps réel. Le site se met à jour immédiatement.
                    </p>
                </div>

                {/* Sélecteur de langue */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        <Globe className="h-5 w-5 mr-2" />
                        Sélectionner la langue
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {languages.map((lang) => (
                            <button
                                key={lang.code}
                                onClick={() => changeLanguage(lang.code)}
                                className={`p-4 rounded-lg border-2 flex items-center justify-between transition-all ${
                                    currentLang === lang.code
                                        ? 'border-blue-500 bg-blue-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}
                            >
                                <div className="flex items-center">
                                    <span className="text-2xl mr-3">{lang.flag}</span>
                                    <div className="text-left">
                                        <div className="font-semibold text-gray-900">
                                            {lang.name}
                                        </div>
                                        <div className="text-sm text-gray-500">
                                            {lang.code.toUpperCase()}
                                        </div>
                                    </div>
                                </div>
                                {currentLang === lang.code && (
                                    <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                                        Actif
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Test des traductions */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {sections.map((section) => (
                        <div
                            key={section.title}
                            className="bg-white rounded-lg shadow-md p-6"
                        >
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                {section.title} Namespace
                            </h3>
                            <div className="space-y-3">
                                {section.keys.map((key) => (
                                    <div
                                        key={key}
                                        className="border-b border-gray-100 pb-2"
                                    >
                                        <div className="text-xs text-gray-500 font-mono">
                                            {section.title.toLowerCase()}:{key}
                                        </div>
                                        <div className="text-gray-900 font-medium">
                                            {t(`${section.title.toLowerCase()}:${key}`)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Section démo interactive */}
                <div className="mt-6 bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Démo Interactive
                    </h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <span>{t('common:loading', 'Loading...')}</span>
                            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
                        </div>
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                            {t('common:save', 'Save')}
                        </button>
                        <button className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 ml-2">
                            {t('common:cancel', 'Cancel')}
                        </button>
                    </div>
                </div>

                {/* Debug Info */}
                <div className="mt-6 bg-blue-50 rounded-lg p-4">
                    <h4 className="font-semibold text-blue-900 mb-2">🛠️ Debug Info</h4>
                    <div className="text-sm text-blue-800 space-y-1">
                        <div>Langage actuel: <strong>{currentLang}</strong></div>
                        <div>Langage i18next: <strong>{i18n.language || 'N/A'}</strong></div>
                        <div>Langue détectée: <strong>{i18n.languages?.join(', ') || 'N/A'}</strong></div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default I18nTestPage;
