FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
# Empty means "same origin"; Nginx proxies API requests to the api service.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM python:3.11-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    KANJIAI_DB_PATH=/data/kanjiai.db
WORKDIR /app/backend
RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt backend/requirements-ml.txt ./
# The VPS runs inference on CPU. Installing the default Linux PyTorch wheel may
# pull several gigabytes of unused NVIDIA/CUDA libraries, which exceeds the
# disk budget of small VPS plans. Install the CPU wheel first; the subsequent
# requirements install keeps that compatible torch version.
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install -r requirements-ml.txt
COPY backend ./
COPY deploy /app/deploy
RUN addgroup --system appuser \
    && adduser --system --ingroup appuser appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data \
    && chmod +x /app/deploy/api-entrypoint.sh
USER appuser
EXPOSE 8010
ENTRYPOINT ["/app/deploy/api-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010", "--proxy-headers", "--forwarded-allow-ips=*"]

FROM nginx:1.27-alpine AS web
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html
EXPOSE 80
