import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import './ResultsPage.css'

function ResultsPage() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadResults()
    // Refresh every 10 seconds to check for updates
    const interval = setInterval(loadResults, 10000)
    return () => clearInterval(interval)
  }, [])

  const loadResults = async () => {
    try {
      const data = await api.getAllResults()
      // Sort by created_at descending (newest first)
      const sorted = data.sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      )
      setResults(sorted)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load results')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      processing: { class: 'badge-processing', text: 'Processing' },
      completed: { class: 'badge-completed', text: 'Completed' },
      failed: { class: 'badge-failed', text: 'Failed' },
    }
    const statusInfo = statusMap[status] || statusMap.processing
    return <span className={`badge ${statusInfo.class}`}>{statusInfo.text}</span>
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  if (loading) {
    return (
      <div className="container">
        <div className="text-center">
          <div className="loading" style={{ width: '2rem', height: '2rem', margin: '2rem auto' }}></div>
          <p>Loading results...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="results-page">
        <div className="page-header">
          <h1 className="page-title">Results</h1>
          <button onClick={loadResults} className="btn btn-secondary">
            Refresh
          </button>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {results.length === 0 ? (
          <div className="card text-center">
            <p className="empty-state">No results yet. Upload a video to get started!</p>
            <Link to="/" className="btn mt-2">
              Upload Video
            </Link>
          </div>
        ) : (
          <div className="results-grid">
            {results.map((result) => (
              <Link
                key={result.result_id}
                to={`/results/${result.result_id}`}
                className="result-card"
              >
                <div className="result-card-header">
                  <h3 className="result-card-title">
                    {result.detection_type === 'birds' ? '🐦' : '🐑'} {result.detection_type}
                  </h3>
                  {getStatusBadge(result.status)}
                </div>
                <div className="result-card-body">
                  <div className="result-stat">
                    <span className="result-stat-label">Unique Animals:</span>
                    <span className="result-stat-value">
                      {result.unique_entities || 'N/A'}
                    </span>
                  </div>
                  <div className="result-stat">
                    <span className="result-stat-label">Total Detections:</span>
                    <span className="result-stat-value">
                      {result.total_detections || 'N/A'}
                    </span>
                  </div>
                  <div className="result-card-footer">
                    <small className="result-date">
                      {formatDate(result.created_at)}
                    </small>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ResultsPage
