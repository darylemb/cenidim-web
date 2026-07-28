# Stage 1: Build Vue app with Vite
FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

# Stage 2: Serve with nginx-unprivileged
FROM nginxinc/nginx-unprivileged:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/30-subst-backend-host.sh /docker-entrypoint.d/30-subst-backend-host.sh

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]