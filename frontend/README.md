# Winsta AI — Trend Automation Studio (Frontend)

Modern, high-performance web studio for **autonomous trend intelligence, multimodal AI prompt generation, and omnichannel social media automation**. Built with **React 18, TypeScript 5, Vite 8, and Tailwind CSS**.

---

## 🚀 Key Features

- **Executive Analytics & Trend Discovery**: Real-time multi-platform trend monitoring (Instagram, TikTok, YouTube, X, Google Trends).
- **Interactive 6-Modality AI Prompt Studio**: Generates, tests, and visualizes:
  1. Text-to-Image (Midjourney v6, FLUX.1) with live in-studio visual preview generation
  2. Text-to-Video (OpenAI Sora, Haiper AI, Luma)
  3. Text-to-Voice (ElevenLabs script generation)
  4. Image-to-Image (ControlNet / SDXL)
  5. Image-to-Video (Runway Gen-3 / Kling)
  6. Video-to-Video (DomoAI / Kaiber)
- **Omnichannel Social Media Hub**: Manage accounts, scheduling calendar, post approvals, and performance analytics across Meta (Instagram, Threads), TikTok, and X.
- **Enterprise Modular Admin Panel**: Dedicated tabs for AI Provider Catalogue & Sandbox, RBAC User Management, Brand Kit Tokens, and Discovery Settings.
- **Dynamic Route Code-Splitting**: Micro-chunk loading with `React.lazy()` and Suspense—cutting initial bundle size by 50% (317 kB main bundle, 99 kB gzip).
- **Internationalization (i18n)**: Native multi-language support (English, Indonesian, Arabic with RTL layout support) powered by pure JSON dictionaries.

---

## 🛠️ Tech Stack & Architecture

- **Core**: React 18, TypeScript 5, Vite 8
- **Styling**: Tailwind CSS, PostCSS, Lucide React Icons
- **State & Routing**: React Context API, React Router DOM v6
- **Architecture**: Domain-Driven Pages, Services Facade, Declarative Route & Component Guards

### Directory Structure

```text
frontend/
├── src/
│   ├── api/                  # Low-level Axios HTTP clients
│   ├── components/
│   │   ├── common/           # UI primitives (Button, Badge, Modal, Input, etc.) + index.ts
│   │   ├── domain/           # Feature cards and modals (Prompt, Trends, Social) + index.ts
│   │   │   └── prompt/       # LivePreviewCard.tsx & ModalityTabContent.tsx
│   │   ├── guards/           # PageGuard.tsx (Route RBAC) & PermissionGuard.tsx
│   │   └── layout/           # App Header, Sidebar, and navigation
│   ├── context/              # AuthContext, LanguageContext, ToastContext
│   ├── hooks/                # usePermissions, useApiCall, useDebounce
│   ├── i18n/                 # translations.ts (typed language configuration)
│   ├── lib/                  # utils.ts (cn helper compatible with shadcn/ui)
│   ├── locales/              # Pure JSON translation dictionaries (en.json, id.json, ar.json)
│   ├── pages/                # Domain-organized pages with index.ts barrel export
│   │   ├── admin/            # AdminPage & modular tabs (AiEngine, Users, BrandKit, Settings)
│   │   ├── auth/             # LoginPage, LandingPage
│   │   ├── dashboard/        # DashboardPage, ScoringPage
│   │   ├── legal/            # PrivacyPage, TermsPage, DataDeletionPage
│   │   ├── social/           # 7 Social media automation & calendar pages
│   │   └── trends/           # Trends, TrendRuns, TrendSources
│   ├── services/             # Unified facade layer (aiService, authService, trendService, socialService)
│   ├── types/                # Strict TypeScript type definitions
│   └── utils/                # cn.ts, formatters.ts
├── .env.example              # Template environment variables
├── Dockerfile                # Multi-stage production build (Node.js -> Nginx Alpine)
├── nginx.conf                # Production reverse proxy and caching rules
└── vite.config.ts            # Vite bundler configuration
```

---

## ⚡ Quick Start (Local Development)

### 1. Prerequisites
- **Node.js**: `v20.x` or higher
- **npm**: `v10.x` or higher

### 2. Installation
Clone the repository and install dependencies:
```bash
cd frontend
npm install
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration:
```env
# Backend API Base URL
VITE_API_URL=http://localhost:8000

# Application Metadata
VITE_APP_NAME="Winsta AI Trend Automation"
VITE_APP_VERSION="1.0.0"
VITE_APP_ENV=development
```

### 4. Run Development Server
```bash
npm run dev
```
The studio will be available at `http://localhost:5173`.

---

## 📦 Production Build & Docker

### Local Production Build
Check TypeScript types and compile the optimized production bundle:
```bash
npm run build
```
Preview the production build locally:
```bash
npm run preview
```

### Docker Production Deployment
The frontend uses a multi-stage Docker build with Nginx Alpine:
```bash
docker build -t winsta-trend-frontend .
docker run -d -p 3005:80 --name pta-frontend winsta-trend-frontend
```

---

## 🛡️ Best Practices & Conventions

1. **Imports**:
   - Prefer barrel exports: `import { Button, Badge } from '@/components/common'`
   - Use unified services: `import { aiService, trendService } from '@/services'`
2. **Role-Based Access Control (RBAC)**:
   - Use `usePermissions()` hook for granular conditional rendering.
   - Wrap protected routes with `<PageGuard allowedRoles={['admin', 'trend_manager']}>`.
3. **Adding New Translations**:
   - Add the key to `src/locales/en.json`, `src/locales/id.json`, and `src/locales/ar.json`.
