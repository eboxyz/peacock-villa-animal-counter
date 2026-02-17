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

See [MANUAL_TESTING.md](MANUAL_TESTING.md) for detailed usage examples.
