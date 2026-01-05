FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with memory optimization
RUN npm install --maxsockets 1

# Copy source
COPY . .

# Build with aggressive memory limits and optimizations
# Reduce memory limit to 384MB and use single-threaded build
ENV NODE_OPTIONS="--max-old-space-size=384"
ENV NODE_ENV=production
# Build with minimal memory usage
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

