import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import ResultsPage from '../pages/ResultsPage'
import { api } from '../services/api'
import { mockResults } from './mocks/api'

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
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows loading state initially', () => {
    api.getAllResults.mockImplementation(() => new Promise(() => {}))
    
    renderResultsPage()
    
    expect(screen.getByText(/loading results/i)).toBeInTheDocument()
  })

  it('displays empty state when no results', async () => {
    api.getAllResults.mockResolvedValue([])
    
    renderResultsPage()
    
    await waitFor(() => {
      expect(screen.getByText(/no results yet/i)).toBeInTheDocument()
      expect(screen.getByText(/upload a video/i)).toBeInTheDocument()
    })
  })

  it('displays list of results', async () => {
    api.getAllResults.mockResolvedValue(mockResults)
    
    renderResultsPage()
    
    await waitFor(() => {
      expect(screen.getByText('birds')).toBeInTheDocument()
      expect(screen.getByText('livestock')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument() // unique_entities
      expect(screen.getByText('150')).toBeInTheDocument() // total_detections
    })
  })

  it('shows correct status badges', async () => {
    api.getAllResults.mockResolvedValue(mockResults)
    
    renderResultsPage()
    
    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('Processing')).toBeInTheDocument()
      expect(screen.getByText('Failed')).toBeInTheDocument()
    })
  })

  it('displays results sorted by date (newest first)', async () => {
    api.getAllResults.mockResolvedValue(mockResults)
    
    renderResultsPage()
    
    await waitFor(() => {
      const resultCards = screen.getAllByText(/birds|livestock/i)
      // First result should be birds (newest)
      expect(resultCards[0]).toHaveTextContent('birds')
    })
  })

  it('shows error message when API fails', async () => {
    api.getAllResults.mockRejectedValue(new Error('Failed to fetch'))
    
    renderResultsPage()
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
    })
  })

  it('has refresh button that reloads results', async () => {
    const user = userEvent.setup()
    api.getAllResults.mockResolvedValue(mockResults)
    
    renderResultsPage()
    
    await waitFor(() => {
      expect(api.getAllResults).toHaveBeenCalledTimes(1)
    })
    
    const refreshButton = screen.getByText('Refresh')
    await user.click(refreshButton)
    
    await waitFor(() => {
      expect(api.getAllResults).toHaveBeenCalledTimes(2)
    })
  })

  it('auto-refreshes every 10 seconds', async () => {
    api.getAllResults.mockResolvedValue(mockResults)
    
    renderResultsPage()
    
    await waitFor(() => {
      expect(api.getAllResults).toHaveBeenCalledTimes(1)
    })
    
    // Fast-forward 10 seconds
    vi.advanceTimersByTime(10000)
    
    await waitFor(() => {
      expect(api.getAllResults).toHaveBeenCalledTimes(2)
    })
  })

  it('creates links to result detail pages', async () => {
    api.getAllResults.mockResolvedValue(mockResults)
    
    renderResultsPage()
    
    await waitFor(() => {
      const links = screen.getAllByRole('link')
      const resultLinks = links.filter(link => link.href.includes('/results/'))
      expect(resultLinks.length).toBeGreaterThan(0)
      expect(resultLinks[0].href).toContain('/results/result-1')
    })
  })
})
