This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Features

### Interactive Tutorial Chat Assistant
The application includes an AI-powered chat assistant that appears after tutorial generation. Users can ask questions about:
- Tutorial concepts and abstractions
- Code examples and implementations
- Project structure and file organization
- Chapter-specific content
- Learning recommendations

## Getting Started

First, set up your environment variables:

```bash
cp .env.example .env.local
# Edit .env.local with your API endpoints
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Chat API Configuration

The chat functionality connects to an external API endpoint. Configure the following environment variables:

- `NEXT_PUBLIC_CHAT_API_URL` - Your external chat API endpoint (required)
- `BACKEND_API_URL` - Your backend API base URL (for other features)
- Optional: Add API keys for external AI services

The chat will send a POST request to your configured endpoint with the following payload:
```json
{
  "message": "User question",
  "tutorialData": "Generated tutorial data object",
  "repositoryMetadata": "Repository metadata object"
}
```

Expected response format:
```json
{
  "response": "AI response text"
}
```

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
