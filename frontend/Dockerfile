FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
# `npm install` (not `npm ci`) — package-lock.json drifts from package.json
# whenever a devDep is added without re-running install (e.g. @playwright/test
# was added to package.json without a lockfile sync). PR #5 made the same
# fix for Vercel's installCommand. `npm ci` would refuse to install at all.
RUN npm install --no-audit --no-fund

# ---

FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ---

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000

CMD ["npm", "start"]
