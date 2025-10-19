/**
 * Album detail page component showing all reviews for a single album
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { Album } from '../types';
import './AlbumDetail.css';

export default function AlbumDetail() {
  const { artist, album } = useParams<{ artist: string; album: string }>();
  const navigate = useNavigate();
  const [albumData, setAlbumData] = useState<Album | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAlbum() {
      setLoading(true);
      setError(null);

      try {
        // Fetch all albums and find the matching one
        // TODO: In future, create dedicated endpoint for single album
        const url = `http://127.0.0.1:8000/api/albums?limit=200&fetch_metadata=false`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch album: ${response.statusText}`);
        }

        const data = await response.json();

        // Find matching album
        const matchingAlbum = data.items.find(
          (item: Album) =>
            item.artist.toLowerCase() === artist?.toLowerCase() &&
            item.album.toLowerCase() === album?.toLowerCase()
        );

        if (!matchingAlbum) {
          throw new Error('Album not found');
        }

        // Parse genres and tracks from JSON strings to arrays
        const parsedAlbum: Album = {
          ...matchingAlbum,
          genres: typeof matchingAlbum.genres === 'string'
            ? (matchingAlbum.genres ? JSON.parse(matchingAlbum.genres) : [])
            : matchingAlbum.genres || [],
          tracks: typeof matchingAlbum.tracks === 'string'
            ? (matchingAlbum.tracks ? JSON.parse(matchingAlbum.tracks) : [])
            : matchingAlbum.tracks || []
        };

        setAlbumData(parsedAlbum);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load album');
      } finally {
        setLoading(false);
      }
    }

    loadAlbum();
  }, [artist, album]);

  const formatScore = (score: number | null, raw: string | null) => {
    if (raw) return raw;
    if (score === null) return 'N/A';
    return score.toFixed(1) + '/10';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  };

  const getFullContent = (content: string) => {
    if (!content) return '';

    // Strip HTML tags but preserve paragraphs as line breaks
    const text = content
      .replace(/<\/p>/g, '\n\n')
      .replace(/<br\s*\/?>/g, '\n')
      .replace(/<[^>]+>/g, '');

    // Decode HTML entities
    const decoded = text
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#8211;/g, '–')
      .replace(/&#8212;/g, '—')
      .replace(/&#8217;/g, "'")
      .replace(/&#8220;/g, '"')
      .replace(/&#8221;/g, '"')
      .replace(/&rsquo;/g, "'")
      .replace(/&ldquo;/g, '"')
      .replace(/&rdquo;/g, '"');

    return decoded.trim();
  };

  if (loading) {
    return (
      <div className="album-detail-loading">
        <div className="spinner"></div>
        <p>Loading album details...</p>
      </div>
    );
  }

  if (error || !albumData) {
    return (
      <div className="album-detail-error">
        <h3>Error loading album</h3>
        <p>{error || 'Album not found'}</p>
        <button onClick={() => navigate('/')} className="back-button">
          ← Back to Albums
        </button>
      </div>
    );
  }

  return (
    <div className="album-detail">
      <div className="detail-header">
        <button onClick={() => navigate('/')} className="back-button">
          ← Back to Albums
        </button>
      </div>

      <div className="album-detail-content">
        <div className="album-cover-section">
          {albumData.cover_art_url && (
            <img
              src={albumData.cover_art_url}
              alt={`${albumData.album} cover`}
              className="album-cover-large"
            />
          )}
        </div>

        <div className="album-info-section">
          <div className="album-header-with-spotify">
            <div>
              <h1 className="album-title-large">{albumData.album}</h1>
              <h2 className="artist-name-large">{albumData.artist}</h2>
            </div>
            <a
              href={`https://open.spotify.com/search/${encodeURIComponent(`${albumData.artist} ${albumData.album}`)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="spotify-search-button"
              title="Search on Spotify"
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
              </svg>
              Search on Spotify
            </a>
          </div>

          {albumData.genres && albumData.genres.length > 0 && (
            <div className="genre-tags-large">
              {albumData.genres.map((genre, index) => (
                <span key={index} className="genre-tag-large">{genre}</span>
              ))}
            </div>
          )}

          <div className="album-stats">
            <div className="stat-item">
              <span className="stat-label">Total Reviews:</span>
              <span className="stat-value">{albumData.review_count}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Latest Review:</span>
              <span className="stat-value">{formatDate(albumData.latest_review)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">First Seen:</span>
              <span className="stat-value">{formatDate(albumData.first_seen)}</span>
            </div>
          </div>
        </div>
      </div>

      {albumData.tracks && albumData.tracks.length > 0 && (
        <div className="album-tracks-section">
          <h3 className="tracks-section-heading">Track Listing</h3>
          <ol className="album-tracks-list">
            {albumData.tracks.map((track, index) => (
              <li key={index} className="album-track-item">
                {track}
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="reviews-section">
        <h3 className="reviews-heading">Reviews from Different Sources</h3>
        <div className="reviews-detail-list">
          {albumData.reviews.map((review) => (
            <div key={review.id} className="review-detail-card">
              <div className="review-header">
                <div className="review-source-info">
                  <h4 className="source-name-large">{review.source.name}</h4>
                  {review.author && (
                    <p className="review-author">by {review.author}</p>
                  )}
                </div>
                <div className="review-meta">
                  {review.review_score !== null && (
                    <div className="review-score-large">
                      {formatScore(review.review_score, review.review_score_raw)}
                    </div>
                  )}
                  <div className="review-date-large">
                    {formatDate(review.published_date)}
                  </div>
                </div>
              </div>

              <h5 className="review-title">{review.title}</h5>

              {review.content && (
                <div className="review-excerpt-detail">
                  <p>{getFullContent(review.content)}</p>
                </div>
              )}

              <a
                href={review.url}
                target="_blank"
                rel="noopener noreferrer"
                className="review-link-button"
              >
                Read Full Review on {review.source.name} →
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
