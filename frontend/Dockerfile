FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Debug: Show file structure
RUN echo "=== Current directory ===" && pwd
RUN echo "=== Listing app directory ===" && ls -la /app/
RUN echo "=== Listing src directory ===" && ls -la /app/src/ || echo "src not found"
RUN echo "=== Listing src/lib directory ===" && ls -la /app/src/lib/ || echo "lib not found"
RUN echo "=== Checking api.ts ===" && (test -f /app/src/lib/api.ts && echo "api.ts EXISTS" || echo "api.ts NOT FOUND") && cat /app/src/lib/api.ts | head -5 || true

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

