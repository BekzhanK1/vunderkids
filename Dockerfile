# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set environment variable to ensure output is shown in real-time
ENV PYTHONUNBUFFERED 1

# Install necessary packages
RUN apk add --no-cache gcc musl-dev postgresql-dev

# Set the working directory in the container
WORKDIR /django

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

# Copy the current directory contents into the container at /django
COPY . .

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the port the app runs on
EXPOSE 8000

# Set the entrypoint to the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["gunicorn", "vunderkids.wsgi", "--bind", "0.0.0.0:8000", "--workers", "4"]
