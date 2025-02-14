# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies (netcat for connectivity checks, gcc, and dos2unix)
RUN apt-get update && \
    apt-get install -y netcat-openbsd gcc dos2unix && \
    rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy the requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Copy the entrypoint script, convert line endings, and make it executable
COPY config/scripts/entrypoint.sh /entrypoint.sh
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh

# Create a non-root user and group, then adjust ownership of application directories
RUN addgroup --system appgroup && adduser --system --group appuser && \
    chown -R appuser:appgroup /app /venv /entrypoint.sh

# Switch to the non-root user
USER appuser

# Set the entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
