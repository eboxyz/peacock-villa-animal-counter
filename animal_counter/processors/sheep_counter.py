from ultralytics import YOLO
import torch
import argparse
import os
import json
from pathlib import Path

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Count animals in a video using YOLO')
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

# COCO dataset class IDs for livestock-like animals
# Goat is NOT in COCO, but goats may be detected as these similar animals:
# - Cow (19): Similar size, four-legged, hooved
# - Sheep (18): Very similar, same family (Caprinae)
# - Horse (17): Similar size, four-legged, hooved
# - Giraffe (23): Large four-legged (may catch some goats)
SHEEP_CLASS_ID = 18
COW_CLASS_ID = 19
HORSE_CLASS_ID = 17
GIRAFFE_CLASS_ID = 23

# Group these together as livestock-like animals (goats may appear as any of these)
LIVESTOCK_CLASS_IDS = [SHEEP_CLASS_ID, COW_CLASS_ID, HORSE_CLASS_ID, GIRAFFE_CLASS_ID]

print(f"Detecting livestock-like animals:")
print(f"  - Sheep (class {SHEEP_CLASS_ID})")
print(f"  - Cow (class {COW_CLASS_ID})")
print(f"  - Horse (class {HORSE_CLASS_ID})")
print(f"  - Giraffe (class {GIRAFFE_CLASS_ID})")
print("⚠️  Note: Goat is not in COCO dataset. Goats may be detected as any of these classes.")

# Run on your video
results = model.track(
    source=video_path,
    device=device,
    save=True,
    conf=0.3,
    classes=LIVESTOCK_CLASS_IDS,  # Detect livestock-like animals (goats may appear as any)
    project='test_results',
    name='iteration'
)

# Get the actual save directory from results (where the MP4 was saved)
# YOLO saves to runs/detect/{project}/{name}/
output_dir = Path(results[0].save_dir) if hasattr(results[0], 'save_dir') else Path("runs/detect/test_results/iteration")

# Count unique tracked entities
unique_track_ids = set()
total_detections = 0
class_counts = {}  # Count detections by class type
track_id_classes = {}  # Track which class each track ID was detected as

print("\nAnalyzing tracking results...")
for result in results:
    if result.boxes is not None and result.boxes.id is not None:
        # Get track IDs and classes for this frame
        track_ids = result.boxes.id.cpu().numpy().astype(int)
        unique_track_ids.update(int(tid) for tid in track_ids)  # Convert to native Python int
        total_detections += len(track_ids)
        
        # Track which class each track ID was detected as
        if result.boxes.cls is not None:
            classes = result.boxes.cls.cpu().numpy().astype(int)
            for tid, cls_id in zip(track_ids, classes):
                tid_int = int(tid)
                cls_name = model.names[int(cls_id)]
                
                # Count overall class detections
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                
                # Track class per track ID
                if tid_int not in track_id_classes:
                    track_id_classes[tid_int] = {}
                track_id_classes[tid_int][cls_name] = track_id_classes[tid_int].get(cls_name, 0) + 1

unique_count = len(unique_track_ids)

# Assign primary class to each track ID (most frequent class for that track)
track_primary_classes = {}
for tid, class_dict in track_id_classes.items():
    # Get the most frequent class for this track ID
    primary_class = max(class_dict.items(), key=lambda x: x[1])[0]
    track_primary_classes[tid] = primary_class

# Count unique entities by primary class
primary_class_counts = {}
for tid, primary_class in track_primary_classes.items():
    primary_class_counts[primary_class] = primary_class_counts.get(primary_class, 0) + 1

# Prepare output data (convert all to native Python types for JSON serialization)
output_data = {
    "video_source": str(video_path),  # Ensure string
    "unique_entities": int(unique_count),  # Ensure native int
    "total_detections": int(total_detections),  # Ensure native int
    "detections_by_class": {k: int(v) for k, v in class_counts.items()},  # Total detections by class
    "unique_entities_by_primary_class": {k: int(v) for k, v in primary_class_counts.items()},  # Unique entities by primary class
    "track_ids": sorted([int(tid) for tid in unique_track_ids]),  # Convert all to native Python ints
    "track_class_assignments": {int(tid): {"primary_class": cls, "all_classes": {k: int(v) for k, v in track_id_classes[tid].items()}} 
                                for tid, cls in track_primary_classes.items()}  # Detailed breakdown per track
}

# Output directory is already set above (where YOLO saved the video)
# Ensure it exists (should already exist from YOLO)
output_dir.mkdir(parents=True, exist_ok=True)

# Find all previous iteration folders to compare (only for the same video)
project_base = output_dir.parent  # runs/detect/test_results/
previous_runs = []
if project_base.exists():
    for folder in sorted(project_base.iterdir()):
        if folder.is_dir() and folder.name.startswith('iteration') and folder != output_dir:
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
    f.write(f"Livestock Count Summary\n")
    f.write(f"{'='*50}\n\n")
    f.write(f"Video: {video_path}\n")
    f.write(f"Target animals: sheep, cow, horse, giraffe (goats may appear as any)\n\n")
    f.write(f"Unique entities detected: {unique_count}\n")
    f.write(f"Total detections across all frames: {total_detections}\n\n")
    
    # Current run details
    f.write(f"Total detections by class (may include same animal classified differently):\n")
    for class_name, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        f.write(f"  - {class_name}: {count}\n")
    f.write(f"\nUnique entities by primary class (each animal counted once, by most frequent class):\n")
    for class_name, count in sorted(primary_class_counts.items(), key=lambda x: -x[1]):
        f.write(f"  - {class_name}: {count}\n")
    
    # Comparison with previous runs
    if previous_runs:
        f.write(f"\n{'='*50}\n")
        f.write(f"Comparison with Previous Runs\n")
        f.write(f"{'='*50}\n\n")
        
        # Compare unique entities
        f.write(f"Unique entities comparison:\n")
        f.write(f"  Current ({output_dir.name}): {unique_count}\n")
        for prev_run in previous_runs:
            prev_unique = prev_run.get('unique_entities', 0)
            diff = unique_count - prev_unique
            diff_str = f" ({diff:+d})" if diff != 0 else " (no change)"
            f.write(f"  {prev_run['folder_name']}: {prev_unique}{diff_str}\n")
        
        # Compare primary class counts
        if primary_class_counts:
            f.write(f"\nPrimary class comparison:\n")
            all_classes = set(primary_class_counts.keys())
            for prev_run in previous_runs:
                prev_classes = prev_run.get('unique_entities_by_primary_class', {})
                all_classes.update(prev_classes.keys())
            
            for class_name in sorted(all_classes):
                current = primary_class_counts.get(class_name, 0)
                f.write(f"  {class_name}:\n")
                f.write(f"    Current ({output_dir.name}): {current}\n")
                for prev_run in previous_runs:
                    prev_count = prev_run.get('unique_entities_by_primary_class', {}).get(class_name, 0)
                    diff = current - prev_count
                    diff_str = f" ({diff:+d})" if diff != 0 else " (no change)"
                    f.write(f"    {prev_run['folder_name']}: {prev_count}{diff_str}\n")
    
    f.write(f"\nNote: Some animals may be classified as different classes across frames.\n")
    f.write(f"      Each animal is assigned a 'primary class' based on its most frequent classification.\n")
    f.write(f"\nTrack IDs: {', '.join(map(str, sorted(unique_track_ids)))}\n")

print(f"\n✅ Done! Results saved to:")
print(f"   📹 Annotated video: {output_dir}")
print(f"   📊 Count summary (JSON): {json_output_path}")
print(f"   📄 Count summary (TXT): {txt_output_path}")
print(f"\n📈 Unique livestock-like animals detected: {unique_count}")
if primary_class_counts:
    print(f"\nUnique entities by primary class (each animal counted once):")
    for class_name, count in sorted(primary_class_counts.items(), key=lambda x: -x[1]):
        print(f"   - {class_name}: {count} animals")
if class_counts:
    print(f"\nTotal detections by class (includes re-classifications):")
    for class_name, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"   - {class_name}: {count} detections")
    print(f"\n⚠️  Note: Some animals may be classified as different classes across frames.")
    print(f"   Each animal is assigned a 'primary class' based on its most frequent classification.")