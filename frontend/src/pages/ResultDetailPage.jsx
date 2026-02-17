import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../services/api'
import './ResultDetailPage.css'

function ResultDetailPage() {
  const { resultId } = useParams()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadResult()
    // Refresh every 5 seconds if still processing
    const interval = setInterval(() => {
      if (result?.status === 'processing') {
        loadResult()
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [resultId, result?.status])

  const loadResult = async () => {
    try {
      const data = await api.getResult(resultId)
      setResult(data)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load result')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const getVideoUrl = () => {
    if (!result?.output_dir) return null
    // The output_dir contains the full path, we need to find the video file
    // Format: runs/detect/test_results/iteration1/ or runs/detect/test_results/bird_iteration1/
    // Video files are in that directory with .mp4 extension
    // We'll construct the path relative to /results/ which Nginx serves
    const outputPath = result.output_dir.replace(/^.*runs\/detect\//, '')
    // Try common video filenames - the video source name should be in the output_dir
    const videoSource = result.video_source?.split('/').pop()?.replace(/\.[^/.]+$/, '') || 'video'
    return `/results/${outputPath}/${videoSource}.mp4`
  }

  if (loading) {
    return (
      <div className="container">
        <div className="text-center">
          <div className="loading" style={{ width: '2rem', height: '2rem', margin: '2rem auto' }}></div>
          <p>Loading result...</p>
        </div>
      </div>
    )
  }

  if (error || !result) {
    return (
      <div className="container">
        <div className="card">
          <div className="alert alert-error">
            {error || 'Result not found'}
          </div>
          <Link to="/results" className="btn">
            Back to Results
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="result-detail-page">
        <div className="page-header">
          <Link to="/results" className="btn btn-secondary">
            ← Back to Results
          </Link>
        </div>

        <div className="card">
          <div className="result-detail-header">
            <div>
              <h1 className="page-title">
                {result.detection_type === 'birds' ? '🐦' : '🐑'} {result.detection_type}
              </h1>
              <p className="result-id">ID: {result.result_id}</p>
            </div>
            <span className={`badge ${
              result.status === 'completed' ? 'badge-completed' :
              result.status === 'failed' ? 'badge-failed' :
              'badge-processing'
            }`}>
              {result.status}
            </span>
          </div>

          {result.status === 'processing' && (
            <div className="alert alert-info">
              <div className="loading" style={{ display: 'inline-block', marginRight: '0.5rem' }}></div>
              Processing in progress. This page will update automatically.
            </div>
          )}

          {result.status === 'failed' && result.error && (
            <div className="alert alert-error">
              Error: {result.error}
            </div>
          )}

          {result.status === 'completed' && (
            <>
              <div className="result-stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{result.unique_entities || 0}</div>
                  <div className="stat-label">Unique Animals</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{result.total_detections || 0}</div>
                  <div className="stat-label">Total Detections</div>
                </div>
              </div>

              {result.detections_by_class && Object.keys(result.detections_by_class).length > 0 && (
                <div className="detail-section">
                  <h2 className="section-title">Detections by Class</h2>
                  <div className="class-breakdown">
                    {Object.entries(result.detections_by_class).map(([className, count]) => (
                      <div key={className} className="class-item">
                        <span className="class-name">{className}</span>
                        <span className="class-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.unique_entities_by_primary_class && Object.keys(result.unique_entities_by_primary_class).length > 0 && (
                <div className="detail-section">
                  <h2 className="section-title">Unique Animals by Primary Class</h2>
                  <div className="class-breakdown">
                    {Object.entries(result.unique_entities_by_primary_class).map(([className, count]) => (
                      <div key={className} className="class-item">
                        <span className="class-name">{className}</span>
                        <span className="class-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.summary_text && (
                <div className="detail-section">
                  <h2 className="section-title">Summary</h2>
                  <pre className="summary-text">{result.summary_text}</pre>
                </div>
              )}

              {result.track_ids && result.track_ids.length > 0 && (
                <div className="detail-section">
                  <h2 className="section-title">Track IDs</h2>
                  <p className="track-ids">
                    {result.track_ids.join(', ')}
                  </p>
                </div>
              )}

              {getVideoUrl() && (
                <div className="detail-section">
                  <h2 className="section-title">Processed Video</h2>
                  <video
                    controls
                    className="result-video"
                    src={getVideoUrl()}
                  >
                    Your browser does not support the video tag.
                  </video>
                </div>
              )}
            </>
          )}

          <div className="result-meta">
            <p><strong>Video Source:</strong> {result.video_source}</p>
            <p><strong>Created:</strong> {formatDate(result.created_at)}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResultDetailPage
