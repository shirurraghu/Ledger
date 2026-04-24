# Use the official Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy entire project
COPY . .

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.wsgi:app"]

