# Stage 1: Build the React application
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Declare build argument for absolute API URL in production
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy source code and configs
COPY tsconfig*.json vite.config.ts postcss.config.js tailwind.config.js index.html ./
COPY src ./src
COPY public ./public

# Build production bundle
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:stable-alpine

# Copy static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
