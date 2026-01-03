FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Debug: Check if files exist and show structure
RUN echo "=== Checking src/lib directory ===" && ls -la /app/src/lib/ 2>&1 || echo "lib directory not found"
RUN echo "=== Checking if api.ts exists ===" && test -f /app/src/lib/api.ts && echo "api.ts exists" || echo "api.ts NOT FOUND"
RUN echo "=== Checking if utils.ts exists ===" && test -f /app/src/lib/utils.ts && echo "utils.ts exists" || echo "utils.ts NOT FOUND"
RUN echo "=== Checking vite.config.ts ===" && cat /app/vite.config.ts

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

