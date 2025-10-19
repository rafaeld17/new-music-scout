# Music Scout Frontend

React + TypeScript web interface for the New Music Scout review aggregation system.

## Features

- **Album List Views**: Browse albums by recent reviews, top-rated, or most controversial
- **Consensus Metrics**: Visual display of review consensus and controversy scores
- **Score Aggregation**: Shows weighted average, median, and individual review scores
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Data**: Fetches live data from the FastAPI backend

## Development

### Prerequisites

- Node.js 18+ and npm
- FastAPI backend running on `http://localhost:8000`

### Setup

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Architecture

- **Vite**: Fast build tool and dev server
- **React 19**: UI library
- **TypeScript**: Type-safe development
- **CSS**: Component-scoped styling

## API Integration

The frontend connects to the FastAPI backend via the `/api` proxy configured in `vite.config.ts`:

- `GET /api/albums/recent` - Recently reviewed albums
- `GET /api/albums/top-rated` - Top-rated albums
- `GET /api/albums/controversial` - Divisive albums
- `GET /api/reviews/latest` - Latest reviews

## Project Structure

```
src/
├── components/       # React components
│   ├── AlbumList.tsx     # Album grid view
│   ├── AlbumCard.tsx     # Individual album card
│   └── *.css             # Component styles
├── types.ts          # TypeScript type definitions
├── api.ts            # API client functions
├── App.tsx           # Main app component
└── index.css         # Global styles
```

## Next Steps

- Album detail page with full review list
- Filtering and sorting options
- Search functionality
- Album cover art integration
