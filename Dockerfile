# Base image
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# If no requirements file exists, install Django directly
RUN pip install --no-cache-dir django gunicorn

# Copy application files
COPY . .

# Expose the port Django will run on
EXPOSE 8001

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "auth.wsgi:application"]