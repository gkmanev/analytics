# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install cmake and any other necessary build dependencies
RUN apt-get update && \
    apt-get install -y cmake build-essential protobuf-compiler && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ARG TORCH_VER=1.9.1+cpu
ARG TORCH_VISION_VER=0.10.1+cpu
ARG NUMPY_VER=1.19.5

# Copy the dependencies file to the working directory
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org \
    torch=="${TORCH_VER}" torchvision=="${TORCH_VISION_VER}" -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install --no-cache-dir numpy=="${NUMPY_VER}" && \
    pip install --no-cache-dir autogluon.tabular[all]

# Copy the current directory contents into the container at /app
COPY . /app/
