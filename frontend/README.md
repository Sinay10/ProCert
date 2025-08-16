# ProCert Learning Platform Frontend

A modern, responsive web application for AWS certification learning built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- **Modern Stack**: Next.js 14 with App Router, TypeScript, Tailwind CSS
- **Authentication**: AWS Cognito integration with NextAuth.js
- **State Management**: React Query for server state, Zustand for client state
- **Responsive Design**: Mobile-first responsive design with Tailwind CSS
- **Component Library**: Custom UI components with consistent design system
- **Testing**: Comprehensive test suite with Vitest and React Testing Library

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- AWS Cognito User Pool configured

### Installation

1. Clone the repository and navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Copy environment variables:
```bash
cp .env.example .env.local
```

4. Configure your environment variables in `.env.local`:
```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
AWS_COGNITO_CLIENT_ID=your-cognito-client-id
AWS_COGNITO_CLIENT_SECRET=your-cognito-client-secret
AWS_COGNITO_ISSUER=https://cognito-idp.region.amazonaws.com/your-user-pool-id
NEXT_PUBLIC_API_BASE_URL=https://your-api-gateway-url
```

5. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
src/
├── app/                    # Next.js 14 App Router pages
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Dashboard page
│   ├── chat/              # Chat interface
│   ├── quizzes/           # Quiz pages
│   ├── progress/          # Progress tracking
│   └── study-path/        # Study path pages
├── components/            # React components
│   ├── ui/                # Reusable UI components
│   ├── layout/            # Layout components
│   ├── auth/              # Authentication components
│   ├── dashboard/         # Dashboard components
│   └── landing/           # Landing page components
├── lib/                   # Utility libraries
│   ├── auth.ts            # NextAuth configuration
│   └── api-client.ts      # API client setup
├── types/                 # TypeScript type definitions
└── test/                  # Test utilities and setup
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run test` - Run tests
- `npm run test:ui` - Run tests with UI
- `npm run test:run` - Run tests once

## Authentication

The application uses AWS Cognito for authentication through NextAuth.js. Users can sign in with their Cognito credentials, and the session is managed automatically.

## API Integration

The frontend communicates with the backend API through a configured API client that:
- Automatically adds authentication tokens
- Handles error responses
- Provides type-safe API calls
- Integrates with React Query for caching

## Testing

The project includes comprehensive tests using:
- **Vitest** - Fast unit test runner
- **React Testing Library** - Component testing utilities
- **Jest DOM** - Additional DOM matchers

Run tests with:
```bash
npm run test
```

## Deployment

The application can be deployed to any platform that supports Next.js:

1. Build the application:
```bash
npm run build
```

2. Deploy the `.next` folder to your hosting platform

## Contributing

1. Follow the existing code style and patterns
2. Write tests for new components and features
3. Ensure all tests pass before submitting
4. Use TypeScript for type safety

## License

This project is part of the ProCert Learning Platform.