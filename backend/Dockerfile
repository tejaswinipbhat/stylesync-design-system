FROM python:3.11-slim

WORKDIR /app

# System deps for Playwright + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 \
    libasound2 libpangocairo-1.0-0 libpango-1.0-0 libcairo2 \
    libatspi2.0-0 libgtk-3-0 libx11-xcb1 libxcb-dri3-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Build context is project root, so paths are relative to root
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY backend/ .
COPY database/ /app/database/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
