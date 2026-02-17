import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import UploadPage from '../pages/UploadPage'

// Mock the API
vi.mock('../services/api', () => ({
  api: {
    uploadVideo: vi.fn(),
  },
}))

// Mock useNavigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
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
  it('renders upload form', () => {
    renderUploadPage()
    
    expect(screen.getByText('Upload Video')).toBeInTheDocument()
    expect(screen.getByLabelText('Detection Type')).toBeInTheDocument()
    expect(screen.getByText('Birds (turkeys, ducks, chickens)')).toBeInTheDocument()
    expect(screen.getByText('Livestock (sheep, goats, cows, horses)')).toBeInTheDocument()
  })
})
