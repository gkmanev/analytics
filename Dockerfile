# Use NVIDIA base image with Ubuntu 20.04
FROM nvidia/cuda:11.6.2-base-ubuntu20.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive 

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    protobuf-compiler \
    python3 \
    python3-pip \
    python3-dev \
    tzdata && \
    ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Ensure python3 is the default
RUN ln -sf /usr/bin/python3 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip  # Use -sf to force overwrite

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt 

# Install additional packages
RUN pip install -U setuptools wheel

# Install PyTorch and AutoGluon
RUN pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu
#RUN pip install autogluon.timeseries
RUN pip install autogluon==1.2

# Copy project files
COPY . /app/

# Set entrypoint
CMD ["gunicorn", "ml_project.wsgi:application", "--bind", "0.0.0.0:8000"]
