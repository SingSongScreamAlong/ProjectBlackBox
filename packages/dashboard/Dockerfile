# Build stage
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files from root and all workspaces
COPY package*.json ./
COPY packages/common/package*.json ./packages/common/
COPY packages/dashboard/package*.json ./packages/dashboard/

# Install all dependencies
RUN npm install --workspaces --include-workspace-root

# Copy source code
COPY packages/common ./packages/common
COPY packages/dashboard ./packages/dashboard
COPY tsconfig*.json ./

# Build dashboard (vite handles @controlbox/common via alias)
WORKDIR /app/packages/dashboard
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine AS runner

# Copy built static files
COPY --from=builder /app/packages/dashboard/build /usr/share/nginx/html

# Copy nginx config for SPA routing
RUN echo 'server { \
    listen 8080; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
