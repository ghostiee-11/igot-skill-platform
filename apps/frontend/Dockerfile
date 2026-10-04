FROM node:22-bookworm-slim AS dependencies
WORKDIR /app
# This isolated build context uses the app-local lockfile, not the workspace install.
COPY package.json package-lock.json ./
RUN NODE_OPTIONS=--max-old-space-size=1024 npm ci --no-audit --no-fund --maxsockets=4

FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# Keep peak build memory bounded on local Windows/WSL hosts.
ENV NEXT_TELEMETRY_DISABLED=1 NODE_OPTIONS=--max-old-space-size=1536
RUN npm run build -- --webpack

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0 PORT=3000 NEXT_TELEMETRY_DISABLED=1
# Standalone tracing omits static/public assets; copy both for the local server.
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
