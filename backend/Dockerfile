# Optimized base image for Python
FROM python:3.11-slim

# Prevents Python from writing .pyc files to the container
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering console output (for real-time logs)
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required to build certain libraries (like psycopg or network utilities)
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy and install requirements first (Leverages Docker's layer caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

# The default command will be overridden in docker-compose for development,
# but we leave this as a base.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]