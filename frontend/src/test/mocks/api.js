// Mock API responses for testing

export const mockUploadResponse = {
  result_id: 'test-result-123',
  status: 'processing',
  message: 'Video uploaded successfully. Processing started.',
}

export const mockResults = [
  {
    result_id: 'result-1',
    detection_type: 'birds',
    unique_entities: 10,
    total_detections: 150,
    status: 'completed',
    created_at: '2024-01-01T12:00:00Z',
    video_source: 'test_video.mp4',
  },
  {
    result_id: 'result-2',
    detection_type: 'livestock',
    unique_entities: 5,
    total_detections: 80,
    status: 'processing',
    created_at: '2024-01-01T11:00:00Z',
    video_source: 'sheep_video.mp4',
  },
  {
    result_id: 'result-3',
    detection_type: 'birds',
    unique_entities: 0,
    total_detections: 0,
    status: 'failed',
    created_at: '2024-01-01T10:00:00Z',
    video_source: 'bad_video.mp4',
    error: 'Processing failed',
  },
]

export const mockResultDetail = {
  result_id: 'result-1',
  detection_type: 'birds',
  unique_entities: 10,
  total_detections: 150,
  status: 'completed',
  created_at: '2024-01-01T12:00:00Z',
  video_source: 'test_video.mp4',
  output_dir: 'runs/detect/test_results/bird_iteration1',
  track_ids: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  detections_by_class: {
    bird: 150,
  },
  unique_entities_by_primary_class: {
    bird: 10,
  },
  summary_text: 'Bird Count Summary\nUnique birds detected: 10\nTotal detections: 150',
}

export const mockLivestockResultDetail = {
  result_id: 'result-2',
  detection_type: 'livestock',
  unique_entities: 5,
  total_detections: 80,
  status: 'completed',
  created_at: '2024-01-01T11:00:00Z',
  video_source: 'sheep_video.mp4',
  output_dir: 'runs/detect/test_results/iteration1',
  track_ids: [1, 2, 3, 4, 5],
  detections_by_class: {
    sheep: 50,
    cow: 30,
  },
  unique_entities_by_primary_class: {
    sheep: 3,
    cow: 2,
  },
  summary_text: 'Livestock Count Summary\nUnique entities: 5',
}
