# Animal Counter

Video processing API for counting animals (birds, sheep, goats) using YOLO object detection.

## Project Structure

```
animal_counter/
├── animal_counter/          # Main package
│   ├── api/                 # API service (processing)
│   │   └── main.py         # API endpoints
│   ├── upload_service/     # Upload service (file handling)
│   │   └── main.py         # Upload endpoints
│   └── processors/         # Video processing scripts
│       ├── bird_counter.py
│       └── sheep_counter.py
├── frontend/                # React frontend
│   ├── src/                # Source code
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js     # Vite configuration
├── tests/                   # Test suite
│   ├── test_api.py
│   └── test_upload_service.py
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Multi-service orchestration
├── nginx.conf              # Nginx configuration
├── requirements.txt         # Python dependencies
└── setup.py                 # Package setup
```

## Quick Start

### Local Development

#### Backend (API)

1. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

2. Start the API server:
```bash
python3 -m uvicorn animal_counter.api.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Frontend

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Docker (Full Stack)

```bash
# Build frontend first
cd frontend
npm install
npm run build
cd ..

# Start all services
docker-compose up
```

Access the application at `http://localhost`

## Testing

Run tests:
```bash
./run_tests.sh
```

Or manually:
```bash
python3 -m pytest tests/ -v
```

## Services

### API Service (Port 8000)
- `POST /process` - Process a video (internal)
- `GET /all` - Get all processing results
- `GET /results/{result_id}` - Get specific result
- `GET /health` - Health check

### Upload Service (Port 8001)
- `POST /upload` - Upload a video file (public-facing)
- `GET /health` - Health check

The upload service handles file uploads and forwards processing requests to the API service.

## Manual Testing Guide

### Prerequisites

1. Install dependencies:
```bash
pip3 install fastapi uvicorn motor pymongo python-multipart
```

2. (Optional) Start MongoDB if testing database features:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

### Running Tests

```bash
./run_tests.sh
```

Or manually:
```bash
pip3 install pytest pytest-asyncio httpx
python3 -m pytest tests/ -v
```

### Starting the API Server

#### Without Docker (for local testing):
```bash
# Set environment variables
export MONGODB_URL="mongodb://localhost:27017"  # or "mongodb://mongodb:27017" for Docker
export MONGODB_DB="animal_counter"
export UPLOAD_DIR="./uploads"
export RESULTS_DIR="./results"
export DEVICE="cpu"  # or "mps" for M4 Mac, "cuda" for GPU

# Start the server
python3 -m uvicorn animal_counter.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### With Docker Compose:
```bash
docker-compose up api
```

The API will be available at `http://localhost:8000`

### Testing Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

#### 2. Get All Results (initially empty)
```bash
curl http://localhost:8000/all
```

Expected response:
```json
[]
```

#### 3. Upload and Process a Video

**For Birds:**
```bash
curl -X POST "http://localhost:8000/process" \
  -F "video=@/path/to/your/video.mp4" \
  -F "detection_type=birds"
```

**For Livestock (sheep/goats):**
```bash
curl -X POST "http://localhost:8000/process" \
  -F "video=@/path/to/your/video.mp4" \
  -F "detection_type=livestock"
```

Expected response:
```json
{
  "result_id": "abc123...",
  "status": "processing"
}
```

**Note:** Processing happens in the background. The video will be processed using the appropriate counter script (`bird_counter.py` or `sheep_counter.py`).

#### 4. Get Specific Result

After uploading, use the `result_id` from the response:

```bash
curl http://localhost:8000/results/YOUR_RESULT_ID
```

Expected response includes:
- `result_id`: Unique identifier
- `detection_type`: "birds" or "livestock"
- `unique_entities`: Number of unique animals detected
- `total_detections`: Total detections across all frames
- `summary_text`: Text summary from count_summary.txt
- `track_ids`: List of tracked entity IDs
- `output_dir`: Path to output directory

#### 5. Check Processing Status

Get all results to see status:
```bash
curl http://localhost:8000/all | python3 -m json.tool
```

Look for your `result_id` and check the `status` field:
- `"processing"`: Still being processed
- `"completed"`: Processing finished successfully
- `"failed"`: Processing failed (check `error` field)

### Using the Test Script

Run the interactive test script:
```bash
./test_api_manual.sh
```

Or set a custom API URL:
```bash
API_URL=http://your-server:8000 ./test_api_manual.sh
```

### API Documentation

FastAPI provides automatic interactive documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Troubleshooting

1. **MongoDB Connection Errors**: The API will work without MongoDB for basic testing, but results won't persist. Check logs for connection errors.

2. **Video Processing Fails**: Check that `sheep_counter.py` and `bird_counter.py` are in `animal_counter/processors/` directory.

3. **Port Already in Use**: Change the port:
   ```bash
   python3 -m uvicorn animal_counter.api.main:app --port 8001
   ```

4. **Permission Errors**: Ensure upload and results directories are writable:
   ```bash
   mkdir -p uploads results
   chmod 755 uploads results
   ```
