# Stage 1: Build of React
FROM node:22-alpine as build

WORKDIR /app

# Copy dependencies and config
COPY package.json package-lock.json .npmrc ./

# Install dependencies (npm ci is faster and more reliable in Docker)
RUN npm ci

# Copy the source code
COPY . .

# Build the application for production
RUN npm run build

# Stage 2: Web Server Nginx
FROM nginxinc/nginx-unprivileged:alpine

# Copy the built static files from the previous stage to the Nginx html directory
COPY --from=build /app/build /usr/share/nginx/html

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080
EXPOSE 8080

# Command to start Nginx
CMD ["nginx", "-g", "daemon off;"]
