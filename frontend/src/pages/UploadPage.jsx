import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import './UploadPage.css'

function UploadPage() {
  const [file, setFile] = useState(null)
  const [detectionType, setDetectionType] = useState('birds')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const navigate = useNavigate()

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      // Validate file type
      const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska']
      if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
        setError('Please select a valid video file (MP4, MOV, AVI, or MKV)')
        return
      }
      
      // Validate file size (500MB limit)
      if (selectedFile.size > 500 * 1024 * 1024) {
        setError('File size must be less than 500MB')
        return
      }

      setFile(selectedFile)
      setError(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file) {
      setError('Please select a video file')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await api.uploadVideo(file, detectionType)
      setSuccess(`Video uploaded successfully! Processing started. Result ID: ${result.result_id}`)
      setFile(null)
      
      // Reset file input
      const fileInput = document.getElementById('video-file')
      if (fileInput) fileInput.value = ''
      
      // Redirect to results after a delay
      setTimeout(() => {
        navigate(`/results/${result.result_id}`)
      }, 2000)
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="container">
      <div className="upload-page">
        <h1 className="page-title">Upload Video</h1>
        <p className="page-subtitle">
          Upload a video to count animals. Choose between birds or livestock detection.
        </p>

        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="detection-type" className="form-label">
                Detection Type
              </label>
              <select
                id="detection-type"
                className="form-select"
                value={detectionType}
                onChange={(e) => setDetectionType(e.target.value)}
                disabled={uploading}
              >
                <option value="birds">Birds (turkeys, ducks, chickens)</option>
                <option value="livestock">Livestock (sheep, goats, cows, horses)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="video-file" className="form-label">
                Video File
              </label>
              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="video-file"
                  className="file-input"
                  accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,.mp4,.mov,.avi,.mkv"
                  onChange={handleFileChange}
                  disabled={uploading}
                />
                <label
                  htmlFor="video-file"
                  className={`file-input-label ${file ? 'has-file' : ''}`}
                >
                  {file ? (
                    <span>📹 {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                  ) : (
                    <span>📁 Click to select video file or drag and drop</span>
                  )}
                </label>
              </div>
            </div>

            {error && (
              <div className="alert alert-error">
                {error}
              </div>
            )}

            {success && (
              <div className="alert alert-success">
                {success}
              </div>
            )}

            <button
              type="submit"
              className="btn"
              disabled={!file || uploading}
            >
              {uploading ? (
                <>
                  <span className="loading"></span> Uploading...
                </>
              ) : (
                'Upload & Process'
              )}
            </button>
          </form>
        </div>

        <div className="card">
          <h2 className="card-title">How it works</h2>
          <ol className="info-list">
            <li>Select detection type (birds or livestock)</li>
            <li>Choose your video file (MP4, MOV, AVI, or MKV)</li>
            <li>Click "Upload & Process"</li>
            <li>Wait for processing to complete</li>
            <li>View results with unique animal counts</li>
          </ol>
        </div>
      </div>
    </div>
  )
}

export default UploadPage
