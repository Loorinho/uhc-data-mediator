
FROM node:24.22.0-alpine

WORKDIR /app

# Enable pnpm through Corepack, pinned to the same major version used locally
RUN corepack enable && corepack prepare pnpm@10.30.2 --activate

# Copy pnpm manifests first for better build caching
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 3000

CMD ["pnpm", "run", "dev", "--host", "0.0.0.0", "--port", "3000"]
