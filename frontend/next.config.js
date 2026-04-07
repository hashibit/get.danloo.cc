/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  i18n: {
    locales: ['en', 'zh'],
    defaultLocale: process.env.DEFAULT_LOCALE || 'en',
    localeDetection: false,
  },
  // Add any other Next.js configuration options here
}

module.exports = nextConfig