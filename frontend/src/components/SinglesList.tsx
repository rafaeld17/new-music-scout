/**
 * Singles list component showing recent track releases and premieres
 */

import { useState, useEffect } from 'react';
import type { Single, SinglesResponse } from '../types';
import './SinglesList.css';

export default function SinglesList() {
  const [singles, setSingles] = useState<Single[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const itemsPerPage = 20;

  useEffect(() => {
    async function loadSingles() {
      setLoading(true);
      setError(null);

      try {
        const offset = (page - 1) * itemsPerPage;
        const url = `http://127.0.0.1:8000/api/singles?limit=${itemsPerPage}&offset=${offset}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch singles: ${response.statusText}`);
        }

        const data: SinglesResponse = await response.json();

        // Parse genres and tracks from JSON strings to arrays
        const parsedItems = data.items.map(single => ({
          ...single,
          genres: typeof single.genres === 'string'
            ? (single.genres ? JSON.parse(single.genres) : [])
            : single.genres || [],
          tracks: typeof single.tracks === 'string'
            ? (single.tracks ? JSON.parse(single.tracks) : [])
            : single.tracks || []
        }));

        setSingles(parsedItems);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load singles');
      } finally {
        setLoading(false);
      }
    }

    loadSingles();
  }, [page]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getContentTypeBadge = (type: string) => {
    const badges: Record<string, { label: string; color: string }> = {
      premiere: { label: 'Premiere', color: '#8b5cf6' },
      news: { label: 'News', color: '#3b82f6' },
      review: { label: 'Review', color: '#10b981' },
    };
    return badges[type] || { label: type, color: '#6b7280' };
  };

  if (loading) {
    return (
      <div className="singles-loading">
        <div className="spinner"></div>
        <p>Loading new singles...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="singles-error">
        <h3>Error loading singles</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (singles.length === 0) {
    return (
      <div className="singles-empty">
        <p>No singles found</p>
      </div>
    );
  }

  const totalPages = Math.ceil(total / itemsPerPage);
  const startItem = (page - 1) * itemsPerPage + 1;
  const endItem = Math.min(page * itemsPerPage, total);

  const handlePrevPage = () => {
    if (page > 1) {
      setPage(page - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleNextPage = () => {
    if (page < totalPages) {
      setPage(page + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div>
      <div className="singles-header">
        <div>
          <h2>New Singles & Tracks</h2>
          <p className="singles-count">
            Showing {startItem}-{endItem} of {total} releases
          </p>
        </div>
      </div>

      <div className="singles-list">
        {singles.map((single) => (
          <div key={single.id} className="single-card">
            <div className="single-main">
              <div className="single-info">
                <div className="single-header-row">
                  <h3 className="artist-name">{single.artist}</h3>
                  <span
                    className="content-type-badge"
                    style={{ backgroundColor: getContentTypeBadge(single.content_type).color }}
                  >
                    {getContentTypeBadge(single.content_type).label}
                  </span>
                </div>

                {single.album && (
                  <p className="album-name">from {single.album}</p>
                )}

                <div className="tracks-section">
                  <div className="tracks-label">Tracks:</div>
                  <ul className="track-list">
                    {single.tracks.map((track, index) => (
                      <li key={index} className="track-name">{track}</li>
                    ))}
                  </ul>
                </div>

                {single.genres && single.genres.length > 0 && (
                  <div className="genre-tags-small">
                    {single.genres.slice(0, 3).map((genre, index) => (
                      <span key={index} className="genre-tag-small">{genre}</span>
                    ))}
                  </div>
                )}

                <div className="single-meta">
                  <span className="source-badge">{single.source.name}</span>
                  <span className="date-text">{formatDate(single.published_date)}</span>
                </div>
              </div>

              {single.cover_art_url && (
                <div className="single-cover">
                  <img src={single.cover_art_url} alt={`${single.artist} cover`} />
                </div>
              )}
            </div>

            <a
              href={single.url}
              target="_blank"
              rel="noopener noreferrer"
              className="read-more-link"
            >
              Read More →
            </a>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-button"
            onClick={handlePrevPage}
            disabled={page === 1}
          >
            ← Previous
          </button>

          <span className="page-info">
            Page {page} of {totalPages}
          </span>

          <button
            className="pagination-button"
            onClick={handleNextPage}
            disabled={page === totalPages}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
