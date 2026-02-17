import pytest
import json
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from animal_counter.api.main import app, process_video_task


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB async collection"""
    with patch('animal_counter.api.main.get_mongodb_collection') as mock_get_collection:
        mock_collection = AsyncMock()
        # Mock async methods
        mock_collection.find = Mock()
        mock_collection.find_one = AsyncMock()
        mock_collection.insert_one = AsyncMock()
        mock_get_collection.return_value = mock_collection
        yield mock_collection


@pytest.fixture
def sample_video_file():
    """Create a temporary video file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(b'fake video content')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_result_data():
    """Sample result data matching count_summary.json format"""
    return {
        "video_source": "/app/uploads/test_video.mp4",
        "unique_entities": 10,
        "total_detections": 150,
        "track_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "detection_type": "birds"
    }


class TestProcessEndpoint:
    """Tests for POST /process endpoint"""
    
    def test_process_birds_video(self, client, mock_mongodb, sample_video_file):
        """Test processing a bird video"""
        with patch('animal_counter.api.main.process_video_task') as mock_process:
            mock_process.return_value = {
                "result_id": "test-id-123",
                "status": "completed",
                "unique_entities": 10,
                "total_detections": 150
            }
            
            with open(sample_video_file, 'rb') as f:
                response = client.post(
                    "/process",
                    files={"video": ("test.mp4", f, "video/mp4")},
                    data={"detection_type": "birds"}
                )
            
            assert response.status_code == 202
            data = response.json()
            assert "result_id" in data
            assert "status" in data
            assert data["status"] == "processing"
    
    def test_process_livestock_video(self, client, mock_mongodb, sample_video_file):
        """Test processing a livestock (sheep/goats) video"""
        with patch('animal_counter.api.main.process_video_task') as mock_process:
            mock_process.return_value = {
                "result_id": "test-id-456",
                "status": "completed"
            }
            
            with open(sample_video_file, 'rb') as f:
                response = client.post(
                    "/process",
                    files={"video": ("test.mp4", f, "video/mp4")},
                    data={"detection_type": "livestock"}
                )
            
            assert response.status_code == 202
            data = response.json()
            assert "result_id" in data
    
    def test_process_missing_video(self, client):
        """Test processing without video file"""
        response = client.post(
            "/process",
            data={"detection_type": "birds"}
        )
        assert response.status_code == 422
    
    def test_process_invalid_detection_type(self, client, sample_video_file):
        """Test processing with invalid detection type"""
        with open(sample_video_file, 'rb') as f:
            response = client.post(
                "/process",
                files={"video": ("test.mp4", f, "video/mp4")},
                data={"detection_type": "invalid"}
            )
        assert response.status_code == 422
    
    def test_process_missing_detection_type(self, client, sample_video_file):
        """Test processing without detection type"""
        with open(sample_video_file, 'rb') as f:
            response = client.post(
                "/process",
                files={"video": ("test.mp4", f, "video/mp4")}
            )
        assert response.status_code == 422


class TestGetAllEndpoint:
    """Tests for GET /all endpoint"""
    
    def test_get_all_results_empty(self, client, mock_mongodb):
        """Test getting all results when none exist"""
        async def empty_iterator():
            if False:
                yield
        
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__ = lambda self: empty_iterator()
        mock_mongodb.find.return_value.sort.return_value = mock_cursor
        
        response = client.get("/all")
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_get_all_results(self, client, mock_mongodb, sample_result_data):
        """Test getting all results"""
        async def result_iterator():
            yield {**sample_result_data, "_id": "id1", "result_id": "id1", "created_at": "2024-01-01"}
            yield {**sample_result_data, "_id": "id2", "result_id": "id2", "created_at": "2024-01-02"}
        
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__ = lambda self: result_iterator()
        mock_mongodb.find.return_value.sort.return_value = mock_cursor
        
        response = client.get("/all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "result_id" in data[0]
        assert "unique_entities" in data[0]
        assert "detection_type" in data[0]


class TestGetResultEndpoint:
    """Tests for GET /results/{result_id} endpoint"""
    
    def test_get_result_success(self, client, mock_mongodb, sample_result_data):
        """Test getting a specific result"""
        mock_mongodb.find_one = AsyncMock(return_value={
            **sample_result_data,
            "_id": "test-id-123",
            "result_id": "test-id-123",
            "created_at": "2024-01-01",
            "output_dir": "runs/detect/test_results/bird_iteration1"
        })
        
        response = client.get("/results/test-id-123")
        assert response.status_code == 200
        data = response.json()
        assert data["result_id"] == "test-id-123"
        assert data["unique_entities"] == 10
        assert data["total_detections"] == 150
    
    def test_get_result_not_found(self, client, mock_mongodb):
        """Test getting a non-existent result"""
        mock_mongodb.find_one = AsyncMock(return_value=None)
        
        response = client.get("/results/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_result_with_txt_file(self, client, mock_mongodb, sample_result_data, tmp_path):
        """Test getting result that includes txt file content"""
        mock_mongodb.find_one = AsyncMock(return_value={
            **sample_result_data,
            "_id": "test-id-123",
            "result_id": "test-id-123",
            "output_dir": str(tmp_path),
            "summary_text": "Bird Count Summary\nUnique birds: 10"
        })
        
        response = client.get("/results/test-id-123")
        assert response.status_code == 200
        data = response.json()
        assert "summary_text" in data


class TestProcessVideoTask:
    """Tests for the process_video_task function"""
    
    @patch('animal_counter.api.main.MongoClient')
    @patch('animal_counter.api.main.subprocess.run')
    @patch('animal_counter.api.main.uuid.uuid4')
    def test_process_birds_video_task(self, mock_uuid, mock_subprocess, mock_mongo_client, tmp_path):
        """Test processing a bird video task"""
        mock_uuid.return_value.hex = "test-uuid-123"
        
        # Mock MongoDB
        mock_collection = Mock()
        mock_collection.insert_one = Mock()
        mock_db = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_client = Mock()
        mock_client.__getitem__ = Mock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client
        
        # Mock subprocess to simulate successful processing
        mock_subprocess.return_value = Mock(returncode=0)
        
        # Create mock output files
        output_dir = tmp_path / "runs" / "detect" / "test_results" / "bird_iteration1"
        output_dir.mkdir(parents=True)
        (output_dir / "count_summary.json").write_text(json.dumps({
            "unique_entities": 10,
            "total_detections": 150,
            "track_ids": [1, 2, 3]
        }))
        (output_dir / "count_summary.txt").write_text("Bird Count Summary")
        
        video_path = tmp_path / "test_video.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch('animal_counter.api.main.UPLOAD_DIR', tmp_path):
            with patch('animal_counter.api.main.RESULTS_DIR', tmp_path):
                with patch('animal_counter.api.main.Path') as mock_path:
                    # Mock Path operations
                    mock_path.return_value.exists.return_value = True
                    mock_path.return_value.iterdir.return_value = [output_dir]
                    mock_path.return_value.stat.return_value.st_mtime = 1234567890
                    mock_path.return_value.name = "bird_iteration1"
                    
                    result = process_video_task(str(video_path), "birds", "test-uuid-123")
        
        assert result["result_id"] == "test-uuid-123"
        assert result["detection_type"] == "birds"
        assert mock_collection.insert_one.called


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
