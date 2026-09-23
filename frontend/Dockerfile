# ==============================================================================
# Multi-stage Dockerfile for Vite (React) Frontend
# Optimized for production with security, performance, and aggressive layer caching
#
# Stages:
#   dependencies  — install & cache node_modules (cache-busted only on package changes)
#   builder       — compile Vite SPA (cache-busted on source changes)
#   production    — minimal, secure Nginx runtime image (non-root)
# ==============================================================================

# Base image for node steps
ARG NODE_IMAGE=node:20-alpine
# (Nginx has been completely removed)

# ==============================================================================
# Stage 1: Dependencies — install node_modules (only re-runs on package changes)
# ==============================================================================
FROM ${NODE_IMAGE} AS dependencies

WORKDIR /frontend

# Copy only lockfile and package.json first — maximises cache hit rate.
# These rarely change compared to src/.
COPY package*.json ./

# Install all dependencies securely and silently
RUN npm ci --prefer-offline --no-audit --progress=false --ignore-scripts \
    && npm cache clean --force

# ==============================================================================
# Stage 2: Builder — compile Vite app (re-runs on any source change)
# ==============================================================================
FROM ${NODE_IMAGE} AS builder

WORKDIR /frontend

# Inherit compiled node_modules from dependencies stage
COPY --from=dependencies /frontend/node_modules ./node_modules

# Package manifests (needed by npm to run scripts)
COPY package*.json ./

# Build config files
COPY tsconfig*.json ./
COPY vite.config.ts ./
# If you have tailwind/postcss, uncomment these:
# COPY tailwind.config.js ./
# COPY postcss.config.mjs ./

# Application source + public assets (most-frequently-changed layer — keep last)
COPY index.html ./
COPY public ./public
COPY src ./src

# Optimization: Set NODE_ENV to production for the build step
ENV NODE_ENV=production

# Build Vite production bundle
RUN npm run build

# ==============================================================================
# Stage 3: Production — minimal runtime image
# ==============================================================================
FROM ${NODE_IMAGE} AS production

ENV APP_INTERNAL_PORT=8080

LABEL maintainer="winsta" \
      version="1.0" \
      description="Winsta SMT Frontend — Production Image" \
      org.opencontainers.image.title="Winsta SMT Frontend" \
      org.opencontainers.image.description="Production-ready Vite SPA" \
      org.opencontainers.image.version="1.0.0"

# Install serve for high-performance static file serving without nginx
RUN npm install -g serve

# Non-root user for security
RUN addgroup -g 1001 -S mrdas \
    && adduser -S mrdas -u 1001 -G mrdas

WORKDIR /app

# Copy compiled assets from builder stage
COPY --from=builder /frontend/dist /app
RUN chown -R mrdas:mrdas /app

# Switch to the unprivileged 'mrdas' user
USER mrdas

EXPOSE ${APP_INTERNAL_PORT}

# Add a Docker Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:${APP_INTERNAL_PORT}/ || exit 1

# Start serve with SPA routing enabled (-s)
CMD ["serve", "-s", ".", "-l", "8080"]
