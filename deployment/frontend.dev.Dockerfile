# Next.js dev-mode image (hot reload).
#
# node_modules is installed inside the image (Linux binaries) and preserved at
# runtime by a named volume — the Windows-installed node_modules on the host
# must never be mounted into the container, its native binaries won't run.
# Rebuild with --build after changing package.json / package-lock.json.

FROM node:22-alpine

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]
