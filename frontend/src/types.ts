/**
 * Type definitions for Music Scout API (Simplified Phase 3)
 */

export interface Source {
  id: number;
  name: string;
}

export interface Review {
  id: number;
  title: string;
  url: string;
  review_score: number | null;
  review_score_raw: string | null;
  published_date: string;
  author: string | null;
  content?: string;
  source: Source;
}

// API response from /api/reviews/latest
export interface ReviewItemResponse {
  id: number;
  source_name: string;
  url: string;
  title: string;
  published_date: string;
  author: string | null;
  review_score: number | null;
  review_score_raw: string | null;
}

export interface Album {
  artist: string;
  album: string;
  review_count: number;
  reviews: Review[];
  first_seen: string;
  latest_review: string;
  genres: string[];
  cover_art_url: string | null;
  tracks: string[];  // Album-level tracks
}

export interface AlbumsResponse {
  total: number;
  items: Album[];
}

export interface Single {
  id: number;
  title: string;
  url: string;
  artist: string;
  album: string | null;
  tracks: string[];
  content_type: string;
  published_date: string;
  source: Source;
  cover_art_url: string | null;
  genres: string[];
}

export interface SinglesResponse {
  total: number;
  items: Single[];
  limit: number;
  offset: number;
}

// Aliases for backward compatibility
export type AlbumAggregate = Album;
export type ReviewItem = Review;
