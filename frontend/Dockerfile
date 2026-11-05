FROM oven/bun:1.4.4 AS build

WORKDIR /app
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend/vite.config.ts frontend/tsconfig.json ./
COPY frontend/src ./src
COPY frontend/static ./static
RUN bun run build

FROM nginx:1.27-alpine AS runtime
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
