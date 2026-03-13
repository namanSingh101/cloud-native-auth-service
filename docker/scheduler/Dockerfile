# ============================
# Stage 1: build deps
# ============================
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ============================
# Stage 2: runtime image
# ============================

FROM python:3.12-slim

WORKDIR /app

# install runtime libs necessary for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \   
    libpq5 \             
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
COPY docker/scheduler/crontab /etc/cron.d/session-cleanup

RUN chmod 0644 /etc/cron.d/session-cleanup && \
    crontab /etc/cron.d/session-cleanup

#cron env var stripping —
# dump the current environment into /etc/environment at container start,
# cron reads this file and restores the vars for each job
CMD printenv > /etc/environment && cron -f