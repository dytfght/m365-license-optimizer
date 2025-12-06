/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // i18n is handled by react-i18next, not Next.js built-in i18n
    // Output standalone for optimized Docker builds
    output: 'standalone',
}

module.exports = nextConfig
