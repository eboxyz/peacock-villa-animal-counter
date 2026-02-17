import pytest
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from animal_counter.upload_service.main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


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
def mock_api_client():
    """Mock the API service client"""
    with patch('animal_counter.upload_service.main.httpx.AsyncClient') as mock_client_class:
        # Create mock response (httpx response.json() is synchronous)
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json = Mock(return_value={"result_id": "test-result-123", "status": "processing"})
        mock_response.raise_for_status = Mock()
        
        # Create mock client
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        # Setup async context manager
        async def aenter():
            return mock_client
        
        async def aexit(*args):
            return None
        
        mock_client_class.return_value.__aenter__ = aenter
        mock_client_class.return_value.__aexit__ = aexit
        
        yield mock_client


class TestUploadEndpoint:
    """Tests for POST /upload endpoint"""
    
    def test_upload_birds_video(self, client, sample_video_file, mock_api_client, tmp_path):
        """Test uploading a bird video"""
        with patch('animal_counter.upload_service.main.UPLOAD_DIR', tmp_path):
            with open(sample_video_file, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"video": ("test.mp4", f, "video/mp4")},
                    data={"detection_type": "birds"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "result_id" in data
        assert data["result_id"] == "test-result-123"
        assert "status" in data
    
    def test_upload_livestock_video(self, client, sample_video_file, mock_api_client, tmp_path):
        """Test uploading a livestock video"""
        # Update mock response for this test (httpx response.json() is synchronous)
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json = Mock(return_value={"result_id": "test-result-456", "status": "processing"})
        mock_response.raise_for_status = Mock()
        mock_api_client.post.return_value = mock_response
        
        with patch('animal_counter.upload_service.main.UPLOAD_DIR', tmp_path):
            with open(sample_video_file, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"video": ("test.mp4", f, "video/mp4")},
                    data={"detection_type": "livestock"}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["result_id"] == "test-result-456"
    
    def test_upload_missing_video(self, client):
        """Test uploading without video file"""
        response = client.post(
            "/upload",
            data={"detection_type": "birds"}
        )
        assert response.status_code == 422
    
    def test_upload_invalid_detection_type(self, client, sample_video_file):
        """Test uploading with invalid detection type"""
        with open(sample_video_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"video": ("test.mp4", f, "video/mp4")},
                data={"detection_type": "invalid"}
            )
        assert response.status_code == 422
    
    def test_upload_missing_detection_type(self, client, sample_video_file):
        """Test uploading without detection type"""
        with open(sample_video_file, 'rb') as f:
            response = client.post(
                "/upload",
                files={"video": ("test.mp4", f, "video/mp4")}
            )
        assert response.status_code == 422
    
    def test_upload_api_service_unavailable(self, client, sample_video_file, mock_api_client, tmp_path):
        """Test handling when API service is unavailable"""
        import httpx
        mock_api_client.post.side_effect = httpx.ConnectError("Connection refused")
        
        with patch('animal_counter.upload_service.main.UPLOAD_DIR', tmp_path):
            with open(sample_video_file, 'rb') as f:
                response = client.post(
                    "/upload",
                    files={"video": ("test.mp4", f, "video/mp4")},
                    data={"detection_type": "birds"}
                )
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
    
    def test_upload_saves_file(self, client, sample_video_file, mock_api_client, tmp_path):
        """Test that uploaded file is saved to disk"""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        
        with patch('animal_counter.upload_service.main.UPLOAD_DIR', upload_dir):
            with open(sample_video_file, 'rb') as f:
                file_content = f.read()
                f.seek(0)
                response = client.post(
                    "/upload",
                    files={"video": ("test.mp4", f, "video/mp4")},
                    data={"detection_type": "birds"}
                )
        
        assert response.status_code == 200
        # Check that file was saved (result_id is in filename)
        data = response.json()
        result_id = data["result_id"]
        saved_files = list(upload_dir.glob(f"{result_id}*"))
        assert len(saved_files) > 0
        assert saved_files[0].read_bytes() == file_content


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
