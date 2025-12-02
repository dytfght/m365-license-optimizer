/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#0066CC',
                    50: '#E6F2FF',
                    100: '#CCE5FF',
                    200: '#99CCFF',
                    300: '#66B2FF',
                    400: '#3399FF',
                    500: '#0066CC',
                    600: '#0052A3',
                    700: '#003D7A',
                    800: '#002952',
                    900: '#001429',
                },
                secondary: {
                    DEFAULT: '#6B7280',
                    50: '#F9FAFB',
                    100: '#F3F4F6',
                    200: '#E5E7EB',
                    300: '#D1D5DB',
                    400: '#9CA3AF',
                    500: '#6B7280',
                    600: '#4B5563',
                    700: '#374151',
                    800: '#1F2937',
                    900: '#111827',
                },
            },
            animation: {
                spin: 'spin 1s linear infinite',
            },
        },
    },
    plugins: [],
}
