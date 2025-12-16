FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Build TypeScript
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# Run
EXPOSE 3000
CMD ["node", "dist/server.js"]
