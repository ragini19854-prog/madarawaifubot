FROM python:3.10-slim-bookworm

ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
    bash \
    bzip2 \
    curl \
    figlet \
    git \
    util-linux \
    libffi-dev \
    libjpeg-dev \
    libwebp-dev \
    neofetch \
    postgresql \
    postgresql-client \
    libpq-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libxslt1-dev \
    openssl \
    pv \
    jq \
    wget \
    python3-dev \
    libreadline-dev \
    libyaml-dev \
    gcc \
    sqlite3 \
    libsqlite3-dev \
    sudo \
    zlib1g \
    ffmpeg \
    libssl-dev \
    libxi6 \
    xvfb \
    unzip \
    libopus0 \
    libopus-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools

# Clone repo
RUN git clone https://github.com/Mynameishekhar/ptb /root/ptb
WORKDIR /root/ptb

# Install Python deps
RUN pip install -U -r requirements.txt

# Run bot
CMD ["python3", "-m", "shivu"]
