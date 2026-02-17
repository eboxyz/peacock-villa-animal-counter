import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import UploadPage from '../pages/UploadPage'
import { api } from '../services/api'
import { mockUploadResponse } from './mocks/api'

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    uploadVideo: vi.fn(),
  },
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderUploadPage = () => {
  return render(
    <BrowserRouter>
      <UploadPage />
    </BrowserRouter>
  )
}

describe('UploadPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload form with detection type selector', () => {
    renderUploadPage()
    
    expect(screen.getByText('Upload Video')).toBeInTheDocument()
    expect(screen.getByLabelText('Detection Type')).toBeInTheDocument()
    expect(screen.getByText('Birds (turkeys, ducks, chickens)')).toBeInTheDocument()
    expect(screen.getByText('Livestock (sheep, goats, cows, horses)')).toBeInTheDocument()
  })

  it('allows selecting detection type', async () => {
    const user = userEvent.setup()
    renderUploadPage()
    
    const select = screen.getByLabelText('Detection Type')
    await act(async () => {
      await user.selectOptions(select, 'livestock')
    })
    
    expect(select.value).toBe('livestock')
  })

  it('shows file input and allows file selection', async () => {
    const user = userEvent.setup()
    renderUploadPage()
    
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    const input = screen.getByLabelText(/Click to select video file/i)
    
    await act(async () => {
      await user.upload(input, file)
    })
    
    expect(screen.getByText(/test\.mp4/i)).toBeInTheDocument()
  })

  it('validates file type and shows error for invalid files', async () => {
    const user = userEvent.setup()
    renderUploadPage()
    
    const file = new File(['content'], 'test.txt', { type: 'text/plain' })
    const input = screen.getByLabelText(/Click to select video file/i)
    
    await act(async () => {
      await user.upload(input, file)
    })
    
    await waitFor(() => {
      expect(screen.getByText(/Please select a valid video file/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('validates file size and shows error for files over 500MB', async () => {
    const user = userEvent.setup()
    renderUploadPage()
    
    // Create a mock file with large size property without allocating memory
    const largeFile = new File(['small content'], 'large.mp4', { type: 'video/mp4' })
    // Override the size property to simulate a large file
    Object.defineProperty(largeFile, 'size', {
      value: 501 * 1024 * 1024, // 501MB
      writable: false
    })
    
    const input = screen.getByLabelText(/Click to select video file/i)
    
    await act(async () => {
      await user.upload(input, largeFile)
    })
    
    await waitFor(() => {
      expect(screen.getByText(/less than 500MB/i)).toBeInTheDocument()
    })
  })

  it('shows error when submitting without file', async () => {
    const user = userEvent.setup()
    renderUploadPage()
    
    const submitButton = screen.getByText('Upload & Process')
    // Button should be disabled when no file is selected
    expect(submitButton).toBeDisabled()
    
    // Manually trigger form submission to test error handling
    const form = submitButton.closest('form')
    await act(async () => {
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true })
      form.dispatchEvent(submitEvent)
    })
    
    await waitFor(() => {
      expect(screen.getByText(/Please select a video file/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('successfully uploads file and shows success message', async () => {
    const user = userEvent.setup()
    api.uploadVideo.mockResolvedValue(mockUploadResponse)
    
    renderUploadPage()
    
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    const input = screen.getByLabelText(/Click to select video file/i)
    await act(async () => {
      await user.upload(input, file)
    })
    
    const submitButton = screen.getByText('Upload & Process')
    await act(async () => {
      await user.click(submitButton)
    })
    
    await waitFor(() => {
      expect(api.uploadVideo).toHaveBeenCalledWith(file, 'birds')
      expect(screen.getByText(/uploaded successfully/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('navigates to result page after successful upload', async () => {
    const user = userEvent.setup()
    api.uploadVideo.mockResolvedValue(mockUploadResponse)
    
    vi.useFakeTimers({ advanceTimers: true })
    renderUploadPage()
    
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    const input = screen.getByLabelText(/Click to select video file/i)
    await act(async () => {
      await user.upload(input, file)
    })
    
    const submitButton = screen.getByText('Upload & Process')
    await act(async () => {
      await user.click(submitButton)
    })
    
    await waitFor(() => {
      expect(api.uploadVideo).toHaveBeenCalled()
    })
    
    // Fast-forward timers
    await act(async () => {
      vi.advanceTimersByTime(2000)
    })
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/results/test-result-123')
    })
    
    vi.useRealTimers()
  })

  it('shows error message when upload fails', async () => {
    const user = userEvent.setup()
    api.uploadVideo.mockRejectedValue(new Error('Upload failed'))
    
    renderUploadPage()
    
    // Wait for component to render
    await waitFor(() => {
      expect(screen.getByText('Upload Video')).toBeInTheDocument()
    })
    
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    const input = screen.getByLabelText(/Click to select video file/i)
    await act(async () => {
      await user.upload(input, file)
    })
    
    const submitButton = screen.getByText('Upload & Process')
    await act(async () => {
      await user.click(submitButton)
    })
    
    await waitFor(() => {
      expect(screen.getByText(/upload failed/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('disables form while uploading', async () => {
    const user = userEvent.setup()
    api.uploadVideo.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    renderUploadPage()
    
    // Wait for component to render
    await waitFor(() => {
      expect(screen.getByText('Upload Video')).toBeInTheDocument()
    })
    
    const file = new File(['video content'], 'test.mp4', { type: 'video/mp4' })
    const input = screen.getByLabelText(/Click to select video file/i)
    await act(async () => {
      await user.upload(input, file)
    })
    
    const submitButton = screen.getByText('Upload & Process')
    await act(async () => {
      await user.click(submitButton)
    })
    
    await waitFor(() => {
      expect(submitButton).toBeDisabled()
      expect(screen.getByText(/uploading/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })
})
