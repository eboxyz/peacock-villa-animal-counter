# Animal Counter

Video processing API for counting animals (birds, sheep, goats) using YOLO object detection.

## Project Structure

```
animal_counter/
├── animal_counter/          # Main package
│   ├── api/                 # FastAPI application
│   │   └── main.py         # API endpoints
│   └── processors/         # Video processing scripts
│       ├── bird_counter.py
│       └── sheep_counter.py
├── tests/                   # Test suite
│   └── test_api.py
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Multi-service orchestration
├── requirements.txt         # Python dependencies
└── setup.py                 # Package setup
```

## Quick Start

### Local Development

1. Install dependencies:
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

### Docker

```bash
docker-compose up
```

## Testing

Run tests:
```bash
./run_tests.sh
```

Or manually:
```bash
python3 -m pytest tests/ -v
```

## API Endpoints

- `POST /process` - Upload and process a video
- `GET /all` - Get all processing results
- `GET /results/{result_id}` - Get specific result
- `GET /health` - Health check

See [MANUAL_TESTING.md](MANUAL_TESTING.md) for detailed usage examples.
