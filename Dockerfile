FROM node:22-alpine AS frontend-build

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# Leave VITE_BACKEND_PORT empty so production builds use the current origin by default.
ARG VITE_BACKEND_ORIGIN=
ARG VITE_BACKEND_PORT=
ENV VITE_BACKEND_ORIGIN=${VITE_BACKEND_ORIGIN}
ENV VITE_BACKEND_PORT=${VITE_BACKEND_PORT}
RUN npm run build

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV ZFS_MANAGER_CONFIG=/data/config.json
ENV ZFS_MANAGER_TASK_DB=/data/tasks.sqlite3

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend-build /build/frontend/dist/ /usr/share/nginx/html/
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/start.sh /start.sh

RUN chmod +x /start.sh \
    && mkdir -p /data /var/lib/nginx /var/log/nginx /var/cache/nginx

EXPOSE 80

CMD ["/start.sh"]
