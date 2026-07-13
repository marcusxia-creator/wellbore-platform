# Next.js production image (multi-stage).
# NEXT_PUBLIC_* vars are inlined at build time, so they're build args here —
# changing them requires a rebuild, not just a restart.

FROM node:22-alpine AS builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./

ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ARG NEXT_PUBLIC_USE_MOCK=false
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_USE_MOCK=$NEXT_PUBLIC_USE_MOCK

RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app/frontend
ENV NODE_ENV=production

COPY --from=builder /app/frontend ./

EXPOSE 3000
CMD ["npm", "run", "start"]
