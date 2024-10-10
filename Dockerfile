# Use an official Python runtime as a parent image
FROM python:3.8

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
RUN pip install --upgrade pip && pip install -r requirements.txt 

RUN pip install -U setuptools wheel

RUN pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu

RUN pip install autogluon.timeseries

# Copy the current directory contents into the container at /app
COPY . /app/

