/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXTAUTH_URL: process.env.NEXTAUTH_URL || 'http://localhost:3000',
    NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET,
    AWS_COGNITO_CLIENT_ID: process.env.AWS_COGNITO_CLIENT_ID,
    AWS_COGNITO_CLIENT_SECRET: process.env.AWS_COGNITO_CLIENT_SECRET,
    AWS_COGNITO_ISSUER: process.env.AWS_COGNITO_ISSUER,
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:3001',
  },
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig