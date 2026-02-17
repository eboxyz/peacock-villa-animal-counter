import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import './Header.css'

function Header() {
  const location = useLocation()

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            🐑 Animal Counter
          </Link>
          <nav className="nav">
            <Link 
              to="/" 
              className={location.pathname === '/' ? 'nav-link active' : 'nav-link'}
            >
              Upload
            </Link>
            <Link 
              to="/results" 
              className={location.pathname === '/results' ? 'nav-link active' : 'nav-link'}
            >
              Results
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header
