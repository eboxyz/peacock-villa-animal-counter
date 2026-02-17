import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import UploadPage from './pages/UploadPage'
import ResultsPage from './pages/ResultsPage'
import ResultDetailPage from './pages/ResultDetailPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/results/:resultId" element={<ResultDetailPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
