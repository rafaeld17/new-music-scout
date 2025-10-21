/**
 * Album list component displaying albums with per-source reviews (Simplified Phase 3)
 */

import { useState, useEffect } from 'react';
import type { Album, AlbumsResponse, Source } from '../types';
import AlbumCard from './AlbumCard';
import './AlbumList.css';

interface AlbumListProps {
  view: 'recent'; // Simplified: only recent view for now
}

type SortOption = 'date' | 'review_count' | 'artist' | 'album';

interface SourceWithCount extends Source {
  count: number;
}

export default function AlbumList({ view }: AlbumListProps) {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [allAlbums, setAllAlbums] = useState<Album[]>([]); // Store all albums for filtering
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<SortOption>('date');
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set());
  const [selectedGenres, setSelectedGenres] = useState<Set<string>>(new Set());
  const [availableSources, setAvailableSources] = useState<SourceWithCount[]>([]);
  const [availableGenres, setAvailableGenres] = useState<Map<string, number>>(new Map());
  const [genreFilterExpanded, setGenreFilterExpanded] = useState(false);
  const itemsPerPage = 20;

  // Load all albums once
  useEffect(() => {
    async function loadAllAlbums() {
      setLoading(true);
      setError(null);

      try {
        // Use the API client
        const { fetchLatestReviews } = await import('../api');
        const reviews = await fetchLatestReviews(200);

        // Convert reviews to album format (group by album title)
        const albumMap = new Map<string, Album>();

        reviews.forEach(review => {
          const key = `${review.title}`;
          if (!albumMap.has(key)) {
            albumMap.set(key, {
              id: review.id,
              artist: review.title.split(' – ')[0] || review.title.split(' - ')[0] || 'Unknown Artist',
              album: review.title.split(' – ')[1] || review.title.split(' - ')[1] || review.title,
              release_year: new Date(review.published_date).getFullYear(),
              genres: [],
              tracks: [],
              reviews: [],
              spotify_id: null,
              spotify_url: null,
              album_art_url: null,
              musicbrainz_id: null
            });
          }

          const album = albumMap.get(key)!;
          album.reviews.push({
            id: review.id,
            source: {
              id: 0,
              name: review.source_name,
              weight: 1.0
            },
            url: review.url,
            title: review.title,
            author: review.author || 'Unknown',
            published_date: review.published_date,
            score: review.review_score,
            score_display: review.review_score_raw || null
          });
        });

        const data: AlbumsResponse = {
          items: Array.from(albumMap.values()),
          total: albumMap.size,
          page: 1,
          per_page: 200
        };

        // Parse genres from JSON strings to arrays
        const parsedItems = data.items.map(album => ({
          ...album,
          genres: typeof album.genres === 'string'
            ? (album.genres ? JSON.parse(album.genres) : [])
            : album.genres || [],
          tracks: typeof album.tracks === 'string'
            ? (album.tracks ? JSON.parse(album.tracks) : [])
            : album.tracks || []
        }));

        setAllAlbums(parsedItems);

        // Calculate source counts
        const sourceCounts = new Map<string, number>();
        parsedItems.forEach(album => {
          album.reviews.forEach(review => {
            const sourceName = review.source.name;
            sourceCounts.set(sourceName, (sourceCounts.get(sourceName) || 0) + 1);
          });
        });

        const sources: SourceWithCount[] = Array.from(sourceCounts.entries()).map(([name, count]) => ({
          id: 0, // Not used for filtering
          name,
          count
        })).sort((a, b) => b.count - a.count);

        setAvailableSources(sources);

        // Collect all unique genres with counts
        const genreCounts = new Map<string, number>();
        parsedItems.forEach(album => {
          if (album.genres && album.genres.length > 0) {
            album.genres.forEach((genre: string) => {
              genreCounts.set(genre, (genreCounts.get(genre) || 0) + 1);
            });
          }
        });

        setAvailableGenres(genreCounts);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load albums');
      } finally {
        setLoading(false);
      }
    }

    loadAllAlbums();
  }, [view]);

  // Filter, sort, and paginate albums whenever dependencies change
  useEffect(() => {
    let filteredAlbums = allAlbums;

    // Apply source filtering
    if (selectedSources.size > 0) {
      filteredAlbums = filteredAlbums.filter(album =>
        album.reviews.some(review => selectedSources.has(review.source.name))
      );
    }

    // Apply genre filtering
    if (selectedGenres.size > 0) {
      filteredAlbums = filteredAlbums.filter(album =>
        album.genres && album.genres.some(genre => selectedGenres.has(genre))
      );
    }

    // Apply sorting
    const sortedAlbums = [...filteredAlbums].sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.latest_review).getTime() - new Date(a.latest_review).getTime();
        case 'review_count':
          return b.review_count - a.review_count;
        case 'artist':
          return a.artist.localeCompare(b.artist);
        case 'album':
          return a.album.localeCompare(b.album);
        default:
          return 0;
      }
    });

    // Update total
    setTotal(sortedAlbums.length);

    // Apply pagination
    const offset = (page - 1) * itemsPerPage;
    const paginated = sortedAlbums.slice(offset, offset + itemsPerPage);
    setAlbums(paginated);

    // Reset to page 1 if current page is out of bounds
    if (offset >= sortedAlbums.length && sortedAlbums.length > 0) {
      setPage(1);
    }
  }, [allAlbums, selectedSources, selectedGenres, sortBy, page]);

  if (loading) {
    return (
      <div className="album-list-loading">
        <div className="spinner"></div>
        <p>Loading albums...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="album-list-error">
        <h3>Error loading albums</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (albums.length === 0) {
    return (
      <div className="album-list-empty">
        <p>No albums found</p>
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

  const handlePageClick = (pageNum: number) => {
    setPage(pageNum);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const toggleSource = (sourceName: string) => {
    const newSelected = new Set(selectedSources);
    if (newSelected.has(sourceName)) {
      newSelected.delete(sourceName);
    } else {
      newSelected.add(sourceName);
    }
    setSelectedSources(newSelected);
    setPage(1); // Reset to first page when filtering changes
  };

  const clearSourceFilters = () => {
    setSelectedSources(new Set());
    setPage(1);
  };

  const toggleGenre = (genre: string) => {
    const newSelected = new Set(selectedGenres);
    if (newSelected.has(genre)) {
      newSelected.delete(genre);
    } else {
      newSelected.add(genre);
    }
    setSelectedGenres(newSelected);
    setPage(1);
  };

  const clearGenreFilters = () => {
    setSelectedGenres(new Set());
    setPage(1);
  };

  // Generate page numbers to display (show current, prev, next, first, last)
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];

    if (totalPages <= 7) {
      // Show all pages if 7 or fewer
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (page > 3) {
        pages.push('...');
      }

      // Show pages around current page
      for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
        pages.push(i);
      }

      if (page < totalPages - 2) {
        pages.push('...');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div>
      <div className="album-list-header">
        <div>
          <h2>Recently Reviewed Albums</h2>
          <p className="album-count">
            Showing {startItem}-{endItem} of {total} albums
          </p>
        </div>
        <div className="sorting-controls">
          <label className="sort-label">Sort by:</label>
          <div className="sort-buttons">
            <button
              className={`sort-button ${sortBy === 'date' ? 'active' : ''}`}
              onClick={() => setSortBy('date')}
            >
              Latest
            </button>
            <button
              className={`sort-button ${sortBy === 'review_count' ? 'active' : ''}`}
              onClick={() => setSortBy('review_count')}
            >
              Most Reviewed
            </button>
            <button
              className={`sort-button ${sortBy === 'artist' ? 'active' : ''}`}
              onClick={() => setSortBy('artist')}
            >
              Artist A-Z
            </button>
            <button
              className={`sort-button ${sortBy === 'album' ? 'active' : ''}`}
              onClick={() => setSortBy('album')}
            >
              Album A-Z
            </button>
          </div>
        </div>
      </div>

      {availableSources.length > 0 && (
        <div className="filter-section">
          <div className="filter-header">
            <h3 className="filter-title">Filter by Source</h3>
            {selectedSources.size > 0 && (
              <button onClick={clearSourceFilters} className="clear-filters-button">
                Clear Filters ({selectedSources.size})
              </button>
            )}
          </div>
          <div className="source-filters">
            {availableSources.map(source => (
              <button
                key={source.name}
                className={`source-filter-button ${selectedSources.has(source.name) ? 'active' : ''}`}
                onClick={() => toggleSource(source.name)}
              >
                {source.name}
                <span className="source-count">{source.count}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {availableGenres.size > 0 && (
        <div className="filter-section genre-filter-section">
          <div className="filter-header genre-filter-header">
            <button
              className="genre-toggle-button"
              onClick={() => setGenreFilterExpanded(!genreFilterExpanded)}
            >
              <span className="genre-toggle-label">
                Filter by Genre
                {selectedGenres.size > 0 && (
                  <span className="selected-count-badge">{selectedGenres.size}</span>
                )}
              </span>
              <span className={`genre-toggle-icon ${genreFilterExpanded ? 'expanded' : ''}`}>
                ▼
              </span>
            </button>
            {selectedGenres.size > 0 && (
              <button onClick={clearGenreFilters} className="clear-filters-button">
                Clear ({selectedGenres.size})
              </button>
            )}
          </div>
          {genreFilterExpanded && (
            <div className="genre-filters-dropdown">
              {Array.from(availableGenres.entries())
                .sort((a, b) => b[1] - a[1])
                .map(([genre, count]) => (
                  <button
                    key={genre}
                    className={`source-filter-button ${selectedGenres.has(genre) ? 'active' : ''}`}
                    onClick={() => toggleGenre(genre)}
                  >
                    {genre}
                    <span className="source-count">{count}</span>
                  </button>
                ))}
            </div>
          )}
        </div>
      )}

      <div className="album-list">
        {albums.map((album, index) => (
          <AlbumCard key={`${album.artist}-${album.album}-${index}`} album={album} />
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

          <div className="pagination-numbers">
            {getPageNumbers().map((pageNum, index) => (
              pageNum === '...' ? (
                <span key={`ellipsis-${index}`} className="pagination-ellipsis">
                  ...
                </span>
              ) : (
                <button
                  key={pageNum}
                  className={`pagination-number ${page === pageNum ? 'active' : ''}`}
                  onClick={() => handlePageClick(pageNum as number)}
                >
                  {pageNum}
                </button>
              )
            ))}
          </div>

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
