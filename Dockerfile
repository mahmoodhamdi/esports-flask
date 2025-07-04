# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port (Fly.io expects app to run on 8080)
EXPOSE 8080

# Command to run app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
