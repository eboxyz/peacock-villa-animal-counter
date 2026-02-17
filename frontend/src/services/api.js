const API_BASE = '/api'
const UPLOAD_BASE = '/upload'

export const api = {
  // Upload video
  async uploadVideo(file, detectionType) {
    const formData = new FormData()
    formData.append('video', file)
    formData.append('detection_type', detectionType)

    const response = await fetch(`${UPLOAD_BASE}/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || 'Upload failed')
    }

    return response.json()
  },

  // Get all results
  async getAllResults() {
    const response = await fetch(`${API_BASE}/all`)
    if (!response.ok) {
      throw new Error('Failed to fetch results')
    }
    return response.json()
  },

  // Get specific result
  async getResult(resultId) {
    const response = await fetch(`${API_BASE}/results/${resultId}`)
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Result not found')
      }
      throw new Error('Failed to fetch result')
    }
    return response.json()
  },

  // Health check
  async healthCheck() {
    const response = await fetch(`${API_BASE}/health`)
    return response.json()
  },
}
