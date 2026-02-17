from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
import motor.motor_asyncio
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Animal Counter API", version="1.0.0")

# Environment variables
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "animal_counter")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "/app/results"))
DEVICE = os.getenv("DEVICE", "cpu")

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# MongoDB client (lazy initialization to allow testing without MongoDB)
mongodb_client = None
db = None
results_collection = None

def get_mongodb_collection():
    """Get MongoDB collection, initializing client if needed"""
    global mongodb_client, db, results_collection
    if mongodb_client is None:
        try:
            mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
            db = mongodb_client[MONGODB_DB]
            results_collection = db["results"]
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB: {e}")
            # Return a mock collection for testing
            return None
    return results_collection


def get_db_collection():
    """Get MongoDB collection (sync wrapper for async)"""
    return results_collection


# Response models
class ProcessResponse(BaseModel):
    result_id: str
    status: str


class ResultItem(BaseModel):
    result_id: str
    detection_type: str
    unique_entities: int
    total_detections: int
    video_source: str
    created_at: str
    output_dir: Optional[str] = None


class ResultDetail(ResultItem):
    summary_text: Optional[str] = None
    track_ids: Optional[List[int]] = None
    detections_by_class: Optional[dict] = None
    unique_entities_by_primary_class: Optional[dict] = None


def process_video_task(video_path: str, detection_type: str, result_id: str):
    """
    Process video using appropriate counter script
    Returns dict with result data
    """
    try:
        video_path = Path(video_path)
        
        # Determine which script to use
        if detection_type == "birds":
            script = "bird_counter.py"
            project_name = "test_results"
            name_prefix = "bird_iteration"
        elif detection_type == "livestock":
            script = "sheep_counter.py"
            project_name = "test_results"
            name_prefix = "iteration"
        else:
            raise ValueError(f"Invalid detection_type: {detection_type}")
        
        # Run the processing script
        script_path = Path("/app") / "animal_counter" / "processors" / script
        cmd = [
            "python3",
            str(script_path),
            str(video_path),
            "--device", DEVICE
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        if result.returncode != 0:
            logger.error(f"Processing failed: {result.stderr}")
            raise RuntimeError(f"Processing failed: {result.stderr}")
        
        # Find the output directory (YOLO creates incrementing folders)
        project_base = Path("/app") / "runs" / "detect" / project_name
        output_dir = None
        
        if project_base.exists():
            # Find the most recent folder matching the prefix
            matching_dirs = [
                d for d in project_base.iterdir()
                if d.is_dir() and d.name.startswith(name_prefix)
            ]
            if matching_dirs:
                # Sort by modification time, get most recent
                output_dir = max(matching_dirs, key=lambda p: p.stat().st_mtime)
        
        if not output_dir or not output_dir.exists():
            raise RuntimeError("Could not find output directory")
        
        # Read count_summary.json
        json_file = output_dir / "count_summary.json"
        if not json_file.exists():
            raise RuntimeError("count_summary.json not found")
        
        with open(json_file, 'r') as f:
            summary_data = json.load(f)
        
        # Read count_summary.txt if it exists
        txt_file = output_dir / "count_summary.txt"
        summary_text = None
        if txt_file.exists():
            summary_text = txt_file.read_text()
        
        # Prepare result data for MongoDB
        result_data = {
            "result_id": result_id,
            "detection_type": detection_type,
            "video_source": str(video_path),
            "unique_entities": summary_data.get("unique_entities", 0),
            "total_detections": summary_data.get("total_detections", 0),
            "track_ids": summary_data.get("track_ids", []),
            "detections_by_class": summary_data.get("detections_by_class", {}),
            "unique_entities_by_primary_class": summary_data.get("unique_entities_by_primary_class", {}),
            "output_dir": str(output_dir),
            "summary_text": summary_text,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }
        
        # Store in MongoDB (sync insert for background task)
        # Use sync pymongo for background tasks
        try:
            from pymongo import MongoClient
            sync_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            sync_db = sync_client[MONGODB_DB]
            sync_collection = sync_db["results"]
            sync_collection.insert_one(result_data)
        except Exception as e:
            logger.error(f"Failed to store result in MongoDB: {e}")
        
        logger.info(f"Processing completed for result_id: {result_id}")
        return result_data
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        # Store error in MongoDB
        error_data = {
            "result_id": result_id,
            "detection_type": detection_type,
            "video_source": str(video_path),
            "status": "failed",
            "error": str(e),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        # Use sync pymongo for background tasks
        try:
            from pymongo import MongoClient
            sync_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            sync_db = sync_client[MONGODB_DB]
            sync_collection = sync_db["results"]
            sync_collection.insert_one(error_data)
        except Exception as e:
            logger.error(f"Failed to store error in MongoDB: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/process", status_code=202)
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    detection_type: str = Form(..., pattern="^(birds|livestock)$")
):
    """
    Process a video for animal counting
    
    - **detection_type**: "birds" or "livestock"
    - **video**: Video file to process
    """
    # Generate unique result ID
    result_id = uuid.uuid4().hex
    
    # Save uploaded file
    file_extension = Path(video.filename).suffix or ".mp4"
    saved_filename = f"{result_id}{file_extension}"
    saved_path = UPLOAD_DIR / saved_filename
    
    try:
        # Save file
        with open(saved_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        logger.info(f"Saved uploaded file: {saved_path}")
        
        # Add background task for processing
        background_tasks.add_task(
            process_video_task,
            str(saved_path),
            detection_type,
            result_id
        )
        
        # Store initial record
        collection = get_mongodb_collection()
        if collection:
            initial_record = {
                "result_id": result_id,
                "detection_type": detection_type,
                "video_source": video.filename,
                "status": "processing",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await collection.insert_one(initial_record)
        
        return ProcessResponse(
            result_id=result_id,
            status="processing"
        )
        
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}")
        # Clean up file if it exists
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/all", response_model=List[ResultItem])
async def get_all_results():
    """Get all processing results"""
    collection = get_mongodb_collection()
    if collection is None:
        return []
    
    cursor = collection.find({}).sort("created_at", -1)
    results = []
    async for doc in cursor:
        # Convert ObjectId to string
        if "_id" in doc:
            doc["result_id"] = doc.get("result_id") or str(doc["_id"])
            # Remove MongoDB _id
            doc.pop("_id", None)
        results.append(doc)
    
    return results


@app.get("/results/{result_id}", response_model=ResultDetail)
async def get_result(result_id: str):
    """Get a specific processing result"""
    collection = get_mongodb_collection()
    if collection is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    doc = await collection.find_one({"result_id": result_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Convert ObjectId to string if needed
    if "_id" in doc:
        doc.pop("_id")
    
    # If output_dir exists, try to read the txt file if not already stored
    if "summary_text" not in doc and "output_dir" in doc:
        txt_file = Path(doc["output_dir"]) / "count_summary.txt"
        if txt_file.exists():
            doc["summary_text"] = txt_file.read_text()
    
    return doc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
