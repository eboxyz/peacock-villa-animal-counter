import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ResultDetailPage from '../pages/ResultDetailPage'
import { api } from '../services/api'
import { mockResultDetail, mockLivestockResultDetail } from './mocks/api'
import userEvent from '@testing-library/user-event'

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    getResult: vi.fn(),
  },
}))

// Mock useParams - need to do this before importing the component
const mockUseParams = vi.fn(() => ({ resultId: 'result-1' }))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => mockUseParams(),
  }
})

describe('ResultDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows loading state initially', () => {
    api.getResult.mockImplementation(() => new Promise(() => {}))
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    expect(screen.getByText(/loading result/i)).toBeInTheDocument()
  })

  it('displays result details when loaded', async () => {
    api.getResult.mockResolvedValue(mockResultDetail)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('birds')).toBeInTheDocument()
      expect(screen.getByText('result-1')).toBeInTheDocument()
      expect(screen.getByText('10')).toBeInTheDocument() // unique_entities
      expect(screen.getByText('150')).toBeInTheDocument() // total_detections
    })
  })

  it('shows processing status and auto-refreshes', async () => {
    const processingResult = { ...mockResultDetail, status: 'processing' }
    api.getResult.mockResolvedValue(processingResult)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/processing in progress/i)).toBeInTheDocument()
    })
    
    // Fast-forward 5 seconds (auto-refresh interval)
    vi.advanceTimersByTime(5000)
    
    await waitFor(() => {
      expect(api.getResult).toHaveBeenCalledTimes(2)
    })
  })

  it('shows error message when result not found', async () => {
    api.getResult.mockRejectedValue(new Error('Result not found'))
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/not found/i)).toBeInTheDocument()
      expect(screen.getByText(/back to results/i)).toBeInTheDocument()
    })
  })

  it('displays class breakdowns for completed results', async () => {
    api.getResult.mockResolvedValue(mockLivestockResultDetail)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Detections by Class')).toBeInTheDocument()
      expect(screen.getByText('sheep')).toBeInTheDocument()
      expect(screen.getByText('cow')).toBeInTheDocument()
      expect(screen.getByText('Unique Animals by Primary Class')).toBeInTheDocument()
    })
  })

  it('displays summary text when available', async () => {
    api.getResult.mockResolvedValue(mockResultDetail)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Summary')).toBeInTheDocument()
      expect(screen.getByText(/Bird Count Summary/i)).toBeInTheDocument()
    })
  })

  it('displays track IDs when available', async () => {
    api.getResult.mockResolvedValue(mockResultDetail)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Track IDs')).toBeInTheDocument()
      expect(screen.getByText(/1, 2, 3/i)).toBeInTheDocument()
    })
  })

  it('shows failed status with error message', async () => {
    const failedResult = {
      ...mockResultDetail,
      status: 'failed',
      error: 'Processing failed: Invalid video format',
    }
    api.getResult.mockResolvedValue(failedResult)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeInTheDocument()
      expect(screen.getByText(/Invalid video format/i)).toBeInTheDocument()
    })
  })

  it('displays video metadata', async () => {
    api.getResult.mockResolvedValue(mockResultDetail)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/test_video\.mp4/i)).toBeInTheDocument()
    })
  })

  it('has back button that navigates to results list', async () => {
    api.getResult.mockResolvedValue(mockResultDetail)
    
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      const backButton = screen.getByText(/back to results/i)
      expect(backButton).toBeInTheDocument()
      expect(backButton.closest('a')).toHaveAttribute('href', '/results')
    })
  })
})
