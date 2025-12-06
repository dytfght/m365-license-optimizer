import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import translation files
import enTranslations from './i18n/locales/en.json';
import frTranslations from './i18n/locales/fr.json';

i18n
    .use(initReactI18next)
    .init({
        resources: {
            en: {
                ...enTranslations
            },
            fr: {
                ...frTranslations
            }
        },
        lng: "fr",
        fallbackLng: "en",
        interpolation: {
            escapeValue: false
        },
        ns: Object.keys(enTranslations),
        defaultNS: 'common',
        compatibilityJSON: 'v3',
        react: {
            useSuspense: false
        }
    });

export default i18n;
