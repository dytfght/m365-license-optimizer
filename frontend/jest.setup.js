import '@testing-library/jest-dom'

// Mock next/router
jest.mock('next/router', () => ({
    useRouter() {
        return {
            route: '/',
            pathname: '',
            query: '',
            asPath: '',
            push: jest.fn(),
            events: {
                on: jest.fn(),
                off: jest.fn()
            },
            beforePopState: jest.fn(() => null),
            prefetch: jest.fn(() => null)
        };
    },
}));

// Mock react-i18next
jest.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key) => key,
        i18n: {
            changeLanguage: jest.fn(),
            language: 'en'
        }
    }),
    initReactI18next: {
        type: '3rdParty',
        init: jest.fn(),
    }
}));
