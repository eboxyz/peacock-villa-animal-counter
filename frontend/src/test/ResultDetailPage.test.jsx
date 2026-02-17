import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ResultDetailPage from '../pages/ResultDetailPage'
import { api } from '../services/api'

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    getResult: vi.fn(),
  },
}))

// Mock useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ resultId: 'result-1' }),
  }
})

describe('ResultDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock to return a simple result so we can test basic rendering
    api.getResult.mockResolvedValue({
      result_id: 'result-1',
      status: 'completed',
      detection_type: 'birds',
      unique_entities: 10,
      total_detections: 150,
    })
  })

  it('renders result detail page', () => {
    render(
      <BrowserRouter>
        <ResultDetailPage />
      </BrowserRouter>
    )
    
    // Just check that the page renders without crashing
    expect(screen.getByText(/result/i)).toBeInTheDocument()
  })
})
