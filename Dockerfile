FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and image processing
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    motor==3.3.2 \
    pymongo==4.6.0 \
    python-multipart==0.0.6

# Copy application code
COPY animal_counter/ ./animal_counter/
COPY yolov8m.pt .
COPY yolov8l.pt .

# Create directories for uploads and results
RUN mkdir -p /app/uploads /app/results /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEVICE=cpu
ENV UPLOAD_DIR=/app/uploads
ENV RESULTS_DIR=/app/results

# Expose port for API
EXPOSE 8000

# Default command (will be overridden by docker-compose)
CMD ["python3", "--version"]
