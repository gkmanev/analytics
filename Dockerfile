# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install cmake and any other necessary build dependencies
RUN apt-get update && apt-get install -y cmake build-essential protobuf-compiler


# Copy the dependencies file to the working directory
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt --no-use-pep517

RUN pip install -U setuptools wheel

RUN pip install --use-pep517

RUN pip install torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu

RUN pip install autogluon

# Copy the current directory contents into the container at /app
COPY . /app/

