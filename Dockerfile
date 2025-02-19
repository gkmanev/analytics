# Use NVIDIA base image with Python
FROM nvidia/cuda:11.6.2-base-ubuntu20.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive  

# Install dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    protobuf-compiler \
    tzdata && \
    ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Set Python 3 as default
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt 

RUN pip install -U setuptools wheel

# Install PyTorch and AutoGluon
RUN pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu
RUN pip install autogluon.timeseries

# Copy the project files
COPY . /app/

# Set entrypoint
CMD ["gunicorn", "ml_project.wsgi:application", "--bind", "0.0.0.0:8000"]
