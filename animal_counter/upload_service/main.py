from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import httpx
import uuid
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Animal Counter Upload Service", version="1.0.0")

# Environment variables
API_SERVICE_URL = os.getenv("API_SERVICE_URL", "http://api:8000")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Response models
class UploadResponse(BaseModel):
    result_id: str
    status: str
    message: Optional[str] = None


async def forward_to_api_service(video_path: Path, detection_type: str) -> dict:
    """
    Forward processing request to API service
    
    Args:
        video_path: Path to the uploaded video file
        detection_type: "birds" or "livestock"
    
    Returns:
        Response dict from API service
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Read file content
            with open(video_path, 'rb') as f:
                file_content = f.read()
            
            files = {"video": (video_path.name, file_content, "video/mp4")}
            data = {"detection_type": detection_type}
            
            response = await client.post(
                f"{API_SERVICE_URL}/process",
                files=files,
                data=data
            )
            
            response.raise_for_status()
            return response.json()
                
    except httpx.HTTPError as e:
        logger.error(f"API service error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"API service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error forwarding to API: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to forward request: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/upload", response_model=UploadResponse)
async def upload_video(
    video: UploadFile = File(...),
    detection_type: str = Form(..., pattern="^(birds|livestock)$")
):
    """
    Upload a video file for processing
    
    - **detection_type**: "birds" or "livestock"
    - **video**: Video file to upload
    
    This endpoint:
    1. Saves the uploaded file to the shared volume
    2. Forwards the processing request to the API service
    3. Returns immediately with a result_id for status tracking
    """
    # Generate unique filename
    file_extension = Path(video.filename).suffix or ".mp4"
    result_id = uuid.uuid4().hex
    saved_filename = f"{result_id}{file_extension}"
    saved_path = UPLOAD_DIR / saved_filename
    
    try:
        # Save uploaded file to shared volume
        with open(saved_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        logger.info(f"Saved uploaded file: {saved_path} (size: {len(content)} bytes)")
        
        # Forward to API service for processing
        api_response = await forward_to_api_service(saved_path, detection_type)
        
        return UploadResponse(
            result_id=api_response.get("result_id", result_id),
            status=api_response.get("status", "processing"),
            message="Video uploaded successfully. Processing started."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already formatted)
        raise
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}")
        # Clean up file if it exists
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
