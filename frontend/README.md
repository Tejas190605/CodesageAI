# CodeSage AI Frontend MVP

Modern developer dashboard web interface for CodeSage AI, built with **Next.js 16 (App Router)**, **React 19**, **TypeScript**, and **Tailwind CSS**.

## Features

* **Dashboard Overview (`/`)**: Displays monitored repositories count, live open pull requests, total reviewed pull requests, average quality score rating, recent pull requests list, and system architecture summary.
* **Repositories Overview (`/repos`)**: Lists monitored GitHub repositories with live metadata, default branch, public/private badges, and open PR counts.
* **Repository Detail (`/repos/[owner]/[repo]`)**: Deep-dive into a single repository's pull requests with filtering by state (`all`, `open`, `closed`).
* **AI Review Detail (`/repos/[owner]/[repo]/pulls/[number]`)**: Detailed view for pull requests featuring changed files stats (+additions/-deletions/commits/comments) and safe Markdown rendering of CodeSage AI review findings.
* **Settings & Integration (`/settings`)**: Displays API connection health indicator, backend configuration requirements, and step-by-step GitHub Webhook setup guide.

## Design Architecture

* **Framework**: Next.js 16 (App Router) + React 19 + TypeScript
* **Styling**: Tailwind CSS with dark developer-tool design system tokens (Zinc/Slate dark canvas `#09090b`, indigo/emerald/amber/rose functional accents).
* **Icons**: `lucide-react`
* **API Communication**: Decoupled HTTP client (`src/lib/api.ts`) communicating exclusively with the CodeSage FastAPI backend server. Zero raw browser calls to external GitHub APIs.

## Requirements

* **Node.js**: `v20+` (Tested on Node.js `v25.6.0`)
* **npm**: `v10+` (Tested on npm `v11.8.0`)
* **CodeSage Backend**: FastAPI server running at `http://127.0.0.1:8000`

## Environment Variables

Create `.env.local` in the `frontend` directory:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

> **Security Note**: Never place `GITHUB_TOKEN`, `GEMINI_API_KEY`, or `GITHUB_WEBHOOK_SECRET` in frontend environment files. Secrets must remain strictly backend-only.

## Local Setup & Development

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Quality & Build Commands

* **Linting**:
  ```bash
  npm run lint
  ```
* **Production Build**:
  ```bash
  npm run build
  ```
