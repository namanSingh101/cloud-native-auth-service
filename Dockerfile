# ============================
# Stage 1: build deps
# ============================
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \                   
    gcc \
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
    libpq-dev \                  
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

EXPOSE 8000

CMD ["uvicorn","app.app:app", "--host","0.0.0.0", "--port","8000","--reload"]

#for production ----> "--workers", "2"