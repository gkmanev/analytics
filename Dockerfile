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
RUN pip install --upgrade pip && pip install -r requirements.txt 

RUN pip install -U setuptools wheel


RUN pip install torch==1.13.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html --target=/kaggle/working/


RUN pip install autogluon --target=/kaggle/working/

# Copy the current directory contents into the container at /app
COPY . /app/

