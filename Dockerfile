FROM python:3.10-slim-bookworm

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (minimal + required)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ffmpeg \
    libpq-dev \
    gcc \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g \
    libopus0 \
    libopus-dev \
    xvfb \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools

# Install latest Telegram library (safe modern version)
RUN pip install python-telegram-bot==21.6

# Set working directory
WORKDIR /root/ptb

# Copy project files (IMPORTANT: build from repo folder)
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Run bot
CMD ["python3", "-m", "shivu"]
