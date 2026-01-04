# Build stage - use monorepo root as context
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files from root and all workspaces
COPY package*.json ./
COPY packages/common/package*.json ./packages/common/
COPY packages/protocol/package*.json ./packages/protocol/
COPY packages/server/package*.json ./packages/server/

# Install all dependencies (including workspace dependencies)
RUN npm install --workspaces --include-workspace-root

# Copy all source code
COPY packages/common ./packages/common
COPY packages/protocol ./packages/protocol
COPY packages/server ./packages/server
COPY tsconfig*.json ./

# Build shared packages first (if they have build scripts)
RUN npm run build --workspace=@controlbox/common --if-present
RUN npm run build --workspace=@controlbox/protocol --if-present

# Production stage
FROM node:22-alpine AS runner

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY packages/common/package*.json ./packages/common/
COPY packages/protocol/package*.json ./packages/protocol/
COPY packages/server/package*.json ./packages/server/

# Install production dependencies only
RUN npm install --workspaces --include-workspace-root --omit=dev

# Copy built shared packages
COPY --from=builder /app/packages/common ./packages/common
COPY --from=builder /app/packages/protocol ./packages/protocol

# Copy server source (we run with tsx, no pre-build needed)
COPY packages/server/src ./packages/server/src
COPY packages/server/tsconfig.json ./packages/server/

# Install tsx for runtime TypeScript execution
RUN npm install -g tsx

WORKDIR /app/packages/server

EXPOSE 8080

ENV NODE_ENV=production
ENV PORT=8080

CMD ["tsx", "src/standalone.ts"]
