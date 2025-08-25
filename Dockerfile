# Use NVIDIA base image with Ubuntu 20.04
FROM nvidia/cuda:11.6.2-base-ubuntu20.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    protobuf-compiler \
    python3 \
    python3-pip \
    python3-dev \
    tzdata \
 && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

# Make python3/pip3 the defaults
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

WORKDIR /app

# Dependencies first (better layer caching)
COPY requirements.txt /app/

# Upgrade pip tooling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# ✅ GPU-enabled PyTorch (CUDA 11.8 wheels) — replaces the CPU-only wheels
# These wheels bundle the needed CUDA userspace libs; no extra CUDA install needed.
RUN pip install --no-cache-dir \
      torch==2.1.2 \
      torchvision==0.16.2 \
      --index-url https://download.pytorch.org/whl/cu118

# Other Python deps
RUN pip install --no-cache-dir -r requirements.txt

# AutoGluon (will keep your already-installed torch if compatible)
RUN pip install --no-cache-dir autogluon.timeseries

# Copy project
COPY . /app/

# Default entrypoint (compose overrides this for the worker)
CMD ["gunicorn", "ml_project.wsgi:application", "--bind", "0.0.0.0:8000"]
