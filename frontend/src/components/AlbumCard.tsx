/**
 * Album card component for displaying album with per-source reviews (Simplified Phase 3)
 */

import { useNavigate } from 'react-router-dom';
import type { Album } from '../types';
import './AlbumCard.css';

interface AlbumCardProps {
  album: Album;
}

export default function AlbumCard({ album }: AlbumCardProps) {
  const navigate = useNavigate();

  const formatScore = (score: number | null, raw: string | null) => {
    if (raw) return raw;
    if (score === null) return 'N/A';
    return score.toFixed(1) + '/10';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const handleCardClick = () => {
    const encodedArtist = encodeURIComponent(album.artist);
    const encodedAlbum = encodeURIComponent(album.album);
    navigate(`/album/${encodedArtist}/${encodedAlbum}`);
  };

  return (
    <div className="album-card" onClick={handleCardClick}>
      <div className="album-header">
        {album.cover_art_url && (
          <div className="album-cover">
            <img src={album.cover_art_url} alt={`${album.album} cover`} />
          </div>
        )}

        <div className="album-info">
          <h3 className="album-title">{album.album}</h3>
          <p className="artist-name">{album.artist}</p>
          {album.genres && album.genres.length > 0 && (
            <div className="genre-tags">
              {album.genres.map((genre, index) => (
                <span key={index} className="genre-tag">{genre}</span>
              ))}
            </div>
          )}
        </div>

        <div className="review-count-badge">
          <div className="count-value">{album.review_count}</div>
          <div className="count-label">{album.review_count === 1 ? 'Review' : 'Reviews'}</div>
        </div>
      </div>

      <div className="reviews-list">
        {album.reviews.map((review) => (
          <div key={review.id} className="review-item">
            <div className="review-row">
              <span className="source-name">{review.source.name}</span>
              <div className="review-right">
                {review.review_score !== null && (
                  <span className="review-score">
                    {formatScore(review.review_score, review.review_score_raw)}
                  </span>
                )}
                <span className="review-date">{formatDate(review.published_date)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="album-meta">
        <span className="meta-item">
          Latest: {formatDate(album.latest_review)}
        </span>
      </div>
    </div>
  );
}
