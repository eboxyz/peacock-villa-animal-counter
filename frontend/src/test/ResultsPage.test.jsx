import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ResultsPage from '../pages/ResultsPage'
import { api } from '../services/api'

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    getAllResults: vi.fn(),
  },
}))

const renderResultsPage = () => {
  return render(
    <BrowserRouter>
      <ResultsPage />
    </BrowserRouter>
  )
}

describe('ResultsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock to return empty array so we can test basic rendering
    api.getAllResults.mockResolvedValue([])
  })

  it('renders results page', () => {
    renderResultsPage()
    
    expect(screen.getByText(/results/i)).toBeInTheDocument()
  })
})
