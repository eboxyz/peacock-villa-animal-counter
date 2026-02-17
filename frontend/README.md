# Animal Counter Frontend

React web application for uploading videos and viewing animal counting results.

## Features

- 📤 Video upload with drag-and-drop support
- 🐦🐑 Detection type selection (birds or livestock)
- 📊 Results list with real-time status updates
- 📹 Processed video playback
- 📱 Fully responsive design for mobile devices
- ⚡ Fast and modern UI with Vite

## Development

### Prerequisites

- Node.js 18+ and npm

### Setup

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Run Tests

```bash
npm test
```

Run tests in watch mode:
```bash
npm test -- --watch
```

Run tests with UI:
```bash
npm run test:ui
```

### Build for Production

```bash
npm run build
```

The built files will be in `frontend/build/` directory, which is served by Nginx.

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components (Header)
│   ├── pages/          # Page components (Upload, Results, Detail)
│   ├── services/       # API client
│   ├── App.jsx         # Main app component
│   └── main.jsx        # Entry point
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
└── package.json        # Dependencies
```

## API Integration

The frontend communicates with:
- `/api/*` - API service endpoints
- `/upload` - Upload service endpoint
- `/results/*` - Static result files (served by Nginx)

## Responsive Design

The app is fully responsive and optimized for:
- Mobile devices (320px+)
- Tablets (768px+)
- Desktop (1024px+)
