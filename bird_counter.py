from ultralytics import YOLO
import torch
import argparse
import os
import json
from pathlib import Path

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Count birds (turkeys, ducks, chickens) in a video using YOLO')
parser.add_argument('video', nargs='?', help='Video path (full path or filename relative to /Users/eyu/Videos)')
args = parser.parse_args()

# Default video directory (Photos app export location)
DEFAULT_VIDEO_DIR = '/Users/eyu/Videos'

# Determine video source path
if args.video:
    # If it's an absolute path (starts with /), use it as-is
    if args.video.startswith('/'):
        video_path = args.video
    else:
        # Otherwise, treat it as a filename and prepend default directory
        video_path = os.path.join(DEFAULT_VIDEO_DIR, args.video)
else:
    # Default fallback
    video_path = os.path.join(DEFAULT_VIDEO_DIR, 'your_video.mp4')
    print(f"No video specified, using default: {video_path}")

# Check if file exists, if not try common video extensions
if not os.path.exists(video_path):
    # Try common video extensions if no extension provided
    if '.' not in os.path.basename(video_path):
        # Try both lowercase and uppercase extensions (Photos exports as .MOV)
        common_extensions = ['.MOV', '.mov', '.MP4', '.mp4', '.m4v', '.M4V', '.avi', '.AVI', '.mkv', '.MKV']
        found = False
        for ext in common_extensions:
            test_path = video_path + ext
            if os.path.exists(test_path):
                video_path = test_path
                found = True
                break
        if not found:
            print(f"⚠️  Warning: File not found: {video_path}")
            print(f"   Tried extensions: {', '.join(common_extensions[:6])}...")

print(f"Video source: {video_path}")

# Verify file exists before processing
if not os.path.exists(video_path):
    print(f"❌ Error: Video file does not exist: {video_path}")
    exit(1)

# M4 MacBook uses MPS (Metal Performance Shaders)
device = 'mps' if torch.backends.mps.is_available() else 'cpu'
print(f"Using: {device}")

# Load pretrained model
model = YOLO('yolov8m.pt')

# COCO dataset class IDs: bird=14
# Note: COCO only has a general "bird" class, not specific types
# Turkeys, ducks, and chickens will all be detected as "bird"
BIRD_CLASS_ID = 14

print(f"Detecting birds (class {BIRD_CLASS_ID})")
print("⚠️  Note: COCO dataset only has a general 'bird' class.")
print("   Turkeys, ducks, and chickens will all be detected as 'bird'.")

# Run on your video
results = model.track(
    source=video_path,
    device=device,
    save=True,
    conf=0.3,
    classes=[BIRD_CLASS_ID],  # Only detect birds (turkeys, ducks, chickens will all show as "bird")
    project='test_results',
    name='bird_iteration'
)

# Get the actual save directory from results (where the MP4 was saved)
# YOLO saves to runs/detect/{project}/{name}/
output_dir = Path(results[0].save_dir) if hasattr(results[0], 'save_dir') else Path("runs/detect/test_results/bird_iteration")

# Count unique tracked entities
unique_track_ids = set()
total_detections = 0

print("\nAnalyzing tracking results...")
for result in results:
    if result.boxes is not None and result.boxes.id is not None:
        # Get track IDs for this frame and convert to native Python ints
        track_ids = result.boxes.id.cpu().numpy().astype(int)
        unique_track_ids.update(int(tid) for tid in track_ids)  # Convert to native Python int
        total_detections += len(track_ids)

unique_count = len(unique_track_ids)

# Prepare output data (convert all to native Python types for JSON serialization)
output_data = {
    "video_source": str(video_path),  # Ensure string
    "unique_entities": int(unique_count),  # Ensure native int
    "total_detections": int(total_detections),  # Ensure native int
    "track_ids": sorted([int(tid) for tid in unique_track_ids])  # Convert all to native Python ints
}

# Output directory is already set above (where YOLO saved the video)
# Ensure it exists (should already exist from YOLO)
output_dir.mkdir(parents=True, exist_ok=True)

# Find all previous iteration folders to compare (only for the same video)
project_base = output_dir.parent  # runs/detect/test_results/
previous_runs = []
if project_base.exists():
    for folder in sorted(project_base.iterdir()):
        if folder.is_dir() and folder.name.startswith('bird_iteration') and folder != output_dir:
            json_file = folder / "count_summary.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r') as prev_f:
                        prev_data = json.load(prev_f)
                        # Only compare runs of the same video
                        if prev_data.get('video_source') == str(video_path):
                            prev_data['folder_name'] = folder.name
                            previous_runs.append(prev_data)
                except:
                    pass

# Write JSON file with counts
json_output_path = output_dir / "count_summary.json"
with open(json_output_path, 'w') as f:
    json.dump(output_data, f, indent=2)

# Also write a simple text summary
txt_output_path = output_dir / "count_summary.txt"
with open(txt_output_path, 'w') as f:
    f.write(f"Bird Count Summary\n")
    f.write(f"{'='*50}\n\n")
    f.write(f"Video: {video_path}\n")
    f.write(f"Target birds: turkeys, ducks, chickens\n")
    f.write(f"Unique birds detected: {unique_count}\n")
    f.write(f"Total detections across all frames: {total_detections}\n")
    
    # Comparison with previous runs
    if previous_runs:
        f.write(f"\n{'='*50}\n")
        f.write(f"Comparison with Previous Runs\n")
        f.write(f"{'='*50}\n\n")
        
        f.write(f"Unique birds comparison:\n")
        f.write(f"  Current ({output_dir.name}): {unique_count}\n")
        for prev_run in previous_runs:
            prev_unique = prev_run.get('unique_entities', 0)
            diff = unique_count - prev_unique
            diff_str = f" ({diff:+d})" if diff != 0 else " (no change)"
            f.write(f"  {prev_run['folder_name']}: {prev_unique}{diff_str}\n")
        
        f.write(f"\nTotal detections comparison:\n")
        f.write(f"  Current ({output_dir.name}): {total_detections}\n")
        for prev_run in previous_runs:
            prev_detections = prev_run.get('total_detections', 0)
            diff = total_detections - prev_detections
            diff_str = f" ({diff:+d})" if diff != 0 else " (no change)"
            f.write(f"  {prev_run['folder_name']}: {prev_detections}{diff_str}\n")
    
    f.write(f"\nTrack IDs: {', '.join(map(str, sorted(unique_track_ids)))}\n")

print(f"\n✅ Done! Results saved to:")
print(f"   📹 Annotated video: {output_dir}")
print(f"   📊 Count summary (JSON): {json_output_path}")
print(f"   📄 Count summary (TXT): {txt_output_path}")
print(f"\n🐦 Unique birds detected: {unique_count}")