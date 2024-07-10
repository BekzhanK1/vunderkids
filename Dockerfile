# Use an official Python runtime as a parent image
FROM python:3.8-alpine

# Set environment variable to ensure output is shown in real-time
ENV PYTHONUNBUFFERED 1

# Install build dependencies
RUN apk add --no-cache gcc musl-dev postgresql-dev

# Set the working directory in the container
WORKDIR /django

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

# Copy the current directory contents into the container at /django
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Default command to run both Gunicorn and Celery
CMD ["sh", "-c", "gunicorn vunderkids.wsgi --bind 0.0.0.0:8000 & celery -A vunderkids worker --loglevel=info"]
